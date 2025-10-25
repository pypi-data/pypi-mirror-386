import os
import re
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from openai import OpenAI
from rich.console import Console

from .prompt_kinds import get_prompt_for_type


console = Console()


# -------------------------
# Utilities (IO and parsing)
# -------------------------


def _read_text_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        # Fall back without encoding
        try:
            return Path(path).read_text(errors="ignore")
        except Exception:
            return ""


def _read_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader  # lazy import
    except Exception:
        console.print(
            "pypdf is not installed. Install it or run: poetry add pypdf",
            style="bold yellow",
        )
        return ""
    try:
        reader = PdfReader(path)
        out: List[str] = []
        # Guard against very large PDFs
        for page in reader.pages:
            try:
                out.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(out)
    except Exception as e:
        console.print(f"Failed to read PDF {path}: {e}", style="bold red")
        return ""


def _strip_tex_comments(text: str) -> str:
    lines: List[str] = []
    for ln in text.splitlines():
        # Keep everything before an unescaped %
        # Simple heuristic: ignore lines that are purely comments
        m = re.match(r"^(.*?)((?<!\\)%|$)", ln)
        if m:
            content = (m.group(1) or "").rstrip()
            if content:
                lines.append(content)
    return "\n".join(lines)


def _collect_corpus(dir_path: str, max_files: Optional[int] = None) -> List[Tuple[str, str]]:
    """
    Return list of (path, text) for .tex and .pdf files under dir_path.
    """
    exts = {".tex", ".pdf"}
    results: List[Tuple[str, str]] = []
    count = 0
    for root, _dirs, files in os.walk(dir_path):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            fp = os.path.join(root, fn)
            text = ""
            try:
                if ext == ".tex":
                    text = _strip_tex_comments(_read_text_file(fp))
                elif ext == ".pdf":
                    text = _read_pdf_text(fp)
            except Exception:
                text = ""
            if text.strip():
                results.append((fp, text))
                count += 1
                if max_files and count >= max_files:
                    return results
    return results


# -------------------------
# Chunking and embeddings
# -------------------------


@dataclass
class RagChunk:
    id: str
    source_path: str
    text: str
    embedding: Optional[List[float]] = None


def _simple_chunks(text: str, max_chars: int, overlap: int) -> List[str]:
    max_chars = max(200, max_chars)
    overlap = max(0, min(overlap, max_chars // 2))
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + max_chars)
        chunk = text[i:j]
        chunks.append(chunk)
        if j >= n:
            break
        i = j - overlap
    return chunks


def _embed_texts(client: OpenAI, model: str, texts: List[str]) -> List[List[float]]:
    # Batch as needed to avoid large payloads
    out: List[List[float]] = []
    batch_size = 16
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        for d in resp.data:
            out.append(list(d.embedding))
    return out


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    num = 0.0
    da = 0.0
    db = 0.0
    for x, y in zip(a, b):
        num += x * y
        da += x * x
        db += y * y
    if da == 0.0 or db == 0.0:
        return 0.0
    return float(num / (math.sqrt(da) * math.sqrt(db)))


def _load_or_build_index(
    client: OpenAI,
    dir_path: str,
    out_dir: str,
    embedding_model: str,
    max_chars: int,
    overlap: int,
    reindex: bool,
    max_files: Optional[int],
    max_chunks: Optional[int],
) -> List[RagChunk]:
    index_path = os.path.join(out_dir, "rag_index.jsonl")
    os.makedirs(out_dir, exist_ok=True)

    if os.path.exists(index_path) and not reindex:
        chunks: List[RagChunk] = []
        with open(index_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    chunks.append(
                        RagChunk(
                            id=obj["id"],
                            source_path=obj["source_path"],
                            text=obj["text"],
                            embedding=obj.get("embedding"),
                        )
                    )
                except Exception:
                    continue
        return chunks

    corpus = _collect_corpus(dir_path, max_files=max_files)
    items: List[RagChunk] = []
    cid = 0
    for src, text in corpus:
        for chunk in _simple_chunks(text, max_chars=max_chars, overlap=overlap):
            cid += 1
            items.append(RagChunk(id=f"c{cid}", source_path=src, text=chunk))
            if max_chunks and len(items) >= max_chunks:
                break
        if max_chunks and len(items) >= max_chunks:
            break

    embeddings = _embed_texts(client, embedding_model, [
                              x.text for x in items]) if items else []
    for x, emb in zip(items, embeddings):
        x.embedding = emb

    with open(index_path, "w", encoding="utf-8") as f:
        for x in items:
            f.write(json.dumps({
                "id": x.id,
                "source_path": x.source_path,
                "text": x.text,
                "embedding": x.embedding,
            }, ensure_ascii=False) + "\n")

    return items


def _retrieve(
    client: OpenAI,
    embedding_model: str,
    index: List[RagChunk],
    query_text: str,
    top_k: int,
) -> List[RagChunk]:
    if not index:
        return []
    resp = client.embeddings.create(model=embedding_model, input=[query_text])
    q = list(resp.data[0].embedding)
    scored = [(x, _cosine(q, x.embedding or [])) for x in index]
    scored.sort(key=lambda t: t[1], reverse=True)
    return [x for x, _s in scored[:max(1, top_k)]]


# -------------------------
# Prompting and generation
# -------------------------


def _extract_output_text(resp) -> str:
    try:
        text = getattr(resp, "output_text", None)
        if text:
            return text
        chunks = []
        for item in getattr(resp, "output", []) or []:
            for part in getattr(item, "content", []) or []:
                if getattr(part, "type", "") == "output_text":
                    chunks.append(str(getattr(part, "text", "")))
        return "\n".join(chunks)
    except Exception:
        return ""


def _adapt_prompt_for_rag(prompt_text: str) -> str:
    # Minimal adaptation: replace image wording with context wording
    prompt_text = prompt_text.replace(
        "Analyze the provided image",
        "Use the provided local reference context and optional seed problem",
    )
    prompt_text = prompt_text.replace(
        "Extract the **exact** physics question text from the image",
        "Derive the problem using the reference context; do not invent external facts",
    )
    return prompt_text


def _build_user_input(prompt_text: str, context_blocks: List[str], seed_problem: Optional[str]) -> List[Dict[str, str]]:
    content: List[Dict[str, str]] = [
        {"type": "input_text", "text": prompt_text}]
    if context_blocks:
        context_joined = "\n\n".join(context_blocks)
        content.append(
            {"type": "input_text", "text": f"Reference Context:\n{context_joined}"})
    if seed_problem:
        content.append(
            {"type": "input_text", "text": f"Seed Problem (LaTeX):\n{seed_problem}"})
    return content


def _extract_concepts(client: OpenAI, latex_snippet: str, model: str = "o4-mini") -> List[str]:
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Extract 1-3 core physics concepts from the LaTeX problem+solution. "
                                "Return ONLY strict JSON list of snake_case concept slugs."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": latex_snippet},
                    ],
                },
            ],
            text={"format": {"type": "text"}},
        )
        raw = _extract_output_text(resp).strip()
        data = json.loads(raw) if raw else []
        if isinstance(data, list):
            return [str(x) for x in data][:3]
        return []
    except Exception:
        return []


def _extract_topics_for_seed(client: OpenAI, text: str, model: str = "o4-mini") -> List[str]:
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are a precise classifier for LaTeX problem text. "
                                "Extract 1-5 concise topics/concepts represented, each 1-4 words. "
                                "Prefer canonical physics/maths topics (e.g., kinematics, work-energy, circular motion, simple circuits, sets). "
                                "Return ONLY a strict JSON list of strings."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": text[:20000]},
                    ],
                },
            ],
            text={"format": {"type": "text"}},
        )
        raw = _extract_output_text(resp).strip()
        data = json.loads(raw) if raw else []
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()][:5]
        return []
    except Exception:
        return []


# -------------------------
# CLI command
# -------------------------


@click.command(
    help=(
        "Deep research generation: builds a local RAG index from PDFs/TeX in the directory, "
        "then generates new LaTeX problems+solutions focused on local content."
    )
)
@click.option("--dir", "dir_path", type=click.Path(exists=True, file_okay=False, dir_okay=True), default=".", show_default=True, help="Directory to scan for .tex and .pdf files")
@click.option("--out-dir", "out_dir", type=click.Path(file_okay=False), default="src/deepresearch", show_default=True, help="Output directory for generated problems")
@click.option("--prompt-type", type=click.Choice(["mcq_sc", "mcq_mc", "subjective"], case_sensitive=False), default="mcq_sc", show_default=True, help="Problem format to generate")
@click.option("--model", default="o4-mini-deep-research", show_default=True, help="Responses model (e.g., o3-deep-research, o3, o4-mini-deep-research)")
@click.option("--effort", type=click.Choice(["low", "medium", "high"], case_sensitive=False), default="medium", show_default=True, help="Reasoning effort for Responses API")
@click.option("--embedding-model", default="text-embedding-3-large", show_default=True, help="Embedding model for local RAG")
@click.option("--top-k", type=int, default=8, show_default=True, help="Top-k retrieved chunks to feed as reference context")
@click.option("--max-context-chars", type=int, default=8000, show_default=True, help="Cap concatenated context length in characters")
@click.option("--chunk-chars", type=int, default=1400, show_default=True, help="Chunk size in characters for RAG")
@click.option("--chunk-overlap", type=int, default=200, show_default=True, help="Chunk overlap in characters for RAG")
@click.option("--max-files", type=int, default=None, help="Limit number of files to index (debug)")
@click.option("--max-chunks", type=int, default=600, show_default=True, help="Limit total chunks to index to control cost")
@click.option("--reindex/--no-reindex", default=False, show_default=True, help="Force rebuild of the local RAG index")
@click.option("--per-tex", type=int, default=1, show_default=True, help="How many new problems to generate per .tex seed file")
@click.option("--vector-store-id", multiple=True, default=(), help="Optional OpenAI vector store id(s) to enable file_search tool with deep-research models")
@click.option("--interactive/--no-interactive", "interactive", default=True, show_default=True, help="Interactively choose topic, difficulty, and count")
@click.option("--difficulty", type=click.Choice(["easy", "medium", "hard"], case_sensitive=False), default=None, help="Target difficulty; if omitted, will be prompted when interactive")
def deepresearch(
    dir_path: str,
    out_dir: str,
    prompt_type: str,
    model: str,
    effort: str,
    embedding_model: str,
    top_k: int,
    max_context_chars: int,
    chunk_chars: int,
    chunk_overlap: int,
    max_files: Optional[int],
    max_chunks: Optional[int],
    reindex: bool,
    per_tex: int,
    vector_store_id: Tuple[str, ...],
    interactive: bool,
    difficulty: Optional[str],
):
    os.makedirs(out_dir, exist_ok=True)

    client = OpenAI()

    console.print(
        f"Indexing corpus from: {os.path.abspath(dir_path)}", style="cyan")
    index = _load_or_build_index(
        client=client,
        dir_path=dir_path,
        out_dir=out_dir,
        embedding_model=embedding_model,
        max_chars=chunk_chars,
        overlap=chunk_overlap,
        reindex=reindex,
        max_files=max_files,
        max_chunks=max_chunks,
    )
    console.print(f"Indexed chunks: {len(index)}", style="green")

    # Seed problems are .tex files in the directory
    tex_files: List[str] = []
    for root, _dirs, files in os.walk(dir_path):
        for fn in files:
            if fn.lower().endswith(".tex"):
                tex_files.append(os.path.join(root, fn))
    if not tex_files:
        console.print(
            "No .tex seed files found. Nothing to generate.", style="bold yellow")
        return

    # Extract topics per seed for interactive selection
    topics_by_seed: Dict[str, List[str]] = {}
    all_topics: List[str] = []
    try:
        for fp in tex_files:
            txt = _read_text_file(fp)
            topics = _extract_topics_for_seed(client, txt)
            topics_by_seed[fp] = topics
            for t in topics:
                if t not in all_topics:
                    all_topics.append(t)
    except Exception:
        pass

    selected_topic: Optional[str] = None
    if interactive and all_topics:
        click.echo("\nSelect a topic:")
        for idx, t in enumerate(all_topics, start=1):
            click.echo(f"  {idx:>3}: {t}")
        try:
            choice = click.prompt("Enter number", default=1,
                                  type=click.IntRange(1, len(all_topics)))
            selected_topic = all_topics[choice - 1]
        except Exception:
            selected_topic = None

    # Prompt for difficulty if not provided
    selected_difficulty = (difficulty or "").lower().strip() or None
    if interactive and not selected_difficulty:
        diffs = ["easy", "medium", "hard"]
        click.echo("\nSelect difficulty:")
        for idx, d in enumerate(diffs, start=1):
            click.echo(f"  {idx:>3}: {d}")
        try:
            dc = click.prompt("Enter number", default=2,
                              type=click.IntRange(1, len(diffs)))
            selected_difficulty = diffs[dc - 1]
        except Exception:
            selected_difficulty = None

    # Prompt for per-tex count (problems per seed)
    per_tex_count = per_tex
    if interactive:
        try:
            per_tex_count = click.prompt(
                "\nProblems per seed (.tex)", default=per_tex, type=int)
        except Exception:
            per_tex_count = per_tex

    # Filter seeds by selected topic
    seeds: List[str] = tex_files
    if selected_topic:
        filtered: List[str] = []
        for fp in tex_files:
            if selected_topic in (topics_by_seed.get(fp) or []):
                filtered.append(fp)
        if filtered:
            seeds = filtered

    # Prepare prompt template adapted for RAG
    try:
        base_prompt = get_prompt_for_type(prompt_type)
    except Exception:
        base_prompt = get_prompt_for_type("mcq_sc")
    prompt_text = _adapt_prompt_for_rag(base_prompt)

    used = 0
    for seed_path in seeds:
        try:
            seed_text = _read_text_file(seed_path)
        except Exception:
            seed_text = ""
        if not seed_text.strip():
            continue

        # Retrieve context based on seed content (bias with selected topic)
        query_text = seed_text
        if selected_topic:
            query_text = f"Topic: {selected_topic}\n\n" + query_text
        retrieved = _retrieve(
            client=client,
            embedding_model=embedding_model,
            index=index,
            query_text=query_text,
            top_k=top_k,
        )
        # Build reference context (cap total chars)
        blocks: List[str] = []
        total = 0
        for ch in retrieved:
            t = ch.text.strip()
            if not t:
                continue
            if total + len(t) > max_context_chars:
                break
            blocks.append(f"[Source: {os.path.basename(ch.source_path)}]\n{t}")
            total += len(t)

        # Prepare Responses payload
        effort_for_model = (effort or "medium").lower()
        if "deep-research" in model and effort_for_model != "medium":
            console.print(
                "o3-deep-research only supports reasoning.effort='medium'; overriding.",
                style="yellow",
            )
            effort_for_model = "medium"
        guidance = []
        if selected_topic:
            guidance.append(f"Target topic: {selected_topic}.")
        if selected_difficulty:
            guidance.append(f"Target difficulty: {selected_difficulty}.")
        extra_rules = (" ".join(guidance)).strip()

        user_content = _build_user_input(
            (prompt_text + (f"\n\n{extra_rules}" if extra_rules else "")),
            blocks,
            seed_text,
        )

        body = {
            "model": model,
            "input": [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are an expert physics problem writer and LaTeX typesetter. "
                                "Focus ONLY on the provided 'Reference Context' and 'Seed Problem'. "
                                "Do not rely on external knowledge or manuals unless clearly present in the context. "
                                "Use TikZ minimally and correctly; prefer coordinates and simple primitives. "
                                "Output must be ONLY the LaTeX snippet from \\item to \\end{solution}."
                            ),
                        }
                    ],
                },
                {"role": "user", "content": user_content},
            ],
            "text": {"format": {"type": "text"}},
            "reasoning": {"effort": effort_for_model},
            "store": True,
        }
        if "deep-research" in model:
            if vector_store_id:
                body["tools"] = [{
                    "type": "file_search",
                    "vector_store_ids": list(vector_store_id),
                }]
            else:
                # Satisfy deep-research requirement with web_search tool if no vector store provided
                body["tools"] = [{"type": "web_search_preview"}]

        for n in range(1, max(1, per_tex_count) + 1):
            try:
                resp = client.responses.create(**body)
                latex = (_extract_output_text(resp) or "").strip()
            except Exception as e:
                console.print(
                    f"API error on {seed_path}: {e}", style="bold red")
                continue

            if not latex:
                console.print(
                    f"Empty response for {seed_path}", style="yellow")
                continue

            stem = Path(seed_path).stem
            out_tex = os.path.join(out_dir, f"{stem}_dr_{n}.tex")
            Path(out_tex).write_text(latex)

            # Extract concept(s)
            concepts = _extract_concepts(client, latex)
            if concepts:
                Path(out_tex + ".concept.json").write_text(json.dumps(concepts,
                                                                      ensure_ascii=False, indent=2))
            else:
                Path(out_tex + ".concept.txt").write_text("\n")

            used += 1
            console.print(f"Saved: {out_tex}", style="green")

    if used == 0:
        console.print("No problems generated.", style="bold yellow")
    else:
        console.print(
            f"Generated {used} problem(s) into {os.path.abspath(out_dir)}", style="bold green")
