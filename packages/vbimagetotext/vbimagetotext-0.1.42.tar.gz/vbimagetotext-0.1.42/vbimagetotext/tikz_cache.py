import os
import re
import json
from pathlib import Path
from typing import List, Dict, Optional

import click
from openai import OpenAI
from rich.console import Console


console = Console()


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return Path(path).read_text(errors="ignore")
        except Exception:
            return ""


def _find_tikz_snippets(tex: str) -> List[str]:
    # Non-greedy match for \begin{tikzpicture} ... \end{tikzpicture}
    # Dotall to allow newlines
    pattern = re.compile(
        r"\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\}", re.IGNORECASE)
    return [m.group(0).strip() for m in pattern.finditer(tex or "")]


def _normalize_for_dedupe(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


@click.command(help="Build a TikZ snippet cache (JSONL with embeddings) from .tex files")
@click.option("--dir", "dir_path", type=click.Path(exists=True, file_okay=False), required=True, help="Directory to scan recursively for .tex files")
@click.option("--out", "out_path", type=click.Path(file_okay=True, dir_okay=False), default="src/tikz_cache.jsonl", show_default=True, help="Output JSONL path")
@click.option("--embedding-model", default="text-embedding-3-large", show_default=True, help="Embedding model")
@click.option("--min-len", type=int, default=40, show_default=True, help="Minimum snippet length in characters")
@click.option("--max-len", type=int, default=4000, show_default=True, help="Maximum snippet length in characters")
@click.option("--max-snippets", type=int, default=500, show_default=True, help="Limit total snippets")
@click.option("--dedupe/--no-dedupe", default=True, show_default=True, help="Dedupe snippets by normalized text")
def tikzcache(dir_path: str, out_path: str, embedding_model: str, min_len: int, max_len: int, max_snippets: int, dedupe: bool):
    client = OpenAI()

    snippets: List[Dict[str, str]] = []
    seen: set[str] = set()
    count = 0
    for root, _dirs, files in os.walk(dir_path):
        for fn in files:
            if not fn.lower().endswith(".tex"):
                continue
            fp = os.path.join(root, fn)
            tex = _read_text(fp)
            if not tex:
                continue
            for snip in _find_tikz_snippets(tex):
                if len(snip) < min_len or len(snip) > max_len:
                    continue
                key = _normalize_for_dedupe(snip)
                if dedupe and key in seen:
                    continue
                seen.add(key)
                snippets.append({"source_path": fp, "snippet": snip})
                count += 1
                if count >= max_snippets:
                    break
            if count >= max_snippets:
                break
        if count >= max_snippets:
            break

    if not snippets:
        console.print("No TikZ snippets found.", style="bold yellow")
        return

    # Embed in small batches
    batch_size = 16
    idx = 0
    out_lines: List[str] = []
    for i in range(0, len(snippets), batch_size):
        batch = snippets[i:i + batch_size]
        emb_inp = [x["snippet"] for x in batch]
        resp = client.embeddings.create(model=embedding_model, input=emb_inp)
        for j, d in enumerate(resp.data):
            rec = {
                "id": f"tz_{idx}",
                "source_path": batch[j]["source_path"],
                "snippet": batch[j]["snippet"],
                "embedding_model": embedding_model,
                "embedding": list(d.embedding),
            }
            out_lines.append(json.dumps(rec, ensure_ascii=False))
            idx += 1

    Path(os.path.dirname(out_path) or ".").mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(out_lines) + ("\n" if out_lines else ""))
    console.print(
        f"Saved TikZ cache: {os.path.abspath(out_path)} ({len(out_lines)} snippets)", style="bold green")

