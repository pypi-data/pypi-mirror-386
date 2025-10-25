import click
import os
import re
import sys
import glob
import json
import tempfile
from typing import List, Tuple

from rich.console import Console
from openai import OpenAI

from .functions import encode_image


PROMPT_DEEP_VARIANTS = {
    "low": (
        "You are an expert STEM tutor. Study the attached problem image and generate a fresh variant of the SAME core concept. "
        "Return ONLY a LaTeX snippet that starts with \\item and ends right after \\end{solution}. "
        "Use a 2-column tasks block with four options, marking the single correct one with \\ans. "
        "Keep math inline with $...$ and keep the solution very brief, showing only key steps."
    ),
    "medium": (
        "You are an expert STEM tutor. Study the attached problem image and generate a fresh variant of the SAME core concept. "
        "Return ONLY a LaTeX snippet that starts with \\item and ends right after \\end{solution}. "
        "Use a 2-column tasks block with four options, marking the single correct one with \\ans. "
        "Keep math inline with $...$ and keep the solution concise in an align* environment."
    ),
    "high": (
        "You are an expert STEM tutor. Study the attached problem image and generate a fresh variant of the SAME core concept. "
        "Return ONLY a LaTeX snippet that starts with \\item and ends right after \\end{solution}. "
        "Use a 2-column tasks block with four options, marking the single correct one with \\ans. "
        "Keep math inline with $...$ and include detailed solution steps with thorough explanations between steps."
    )
}


def _build_responses_input(prompt_text: str, image_b64_list: List[str], extra_texts: List[str] = None):
    content_items = [
        {"type": "input_text", "text": prompt_text}
    ]
    for b64 in image_b64_list:
        content_items.append(
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{b64}",
            }
        )
    if extra_texts:
        for t in extra_texts:
            content_items.append({"type": "input_text", "text": t})

    return [
        {
            "role": "user",
            "content": content_items,
        }
    ]


def _infer_output_name(image_path: str) -> str:
    """Derive an output base name like variant_1.tex from Problem_1.png; fallback to variant_<stem>.tex."""
    stem = os.path.splitext(os.path.basename(image_path))[0]
    m = re.match(r"^(.*?)(\d+)$", stem)
    if m:
        idx = m.group(2)
        return f"variant_{idx}.tex"
    return f"{stem}_variant.tex"


def _split_pattern(sample_path: str) -> Tuple[str, str, str]:
    dirname = os.path.dirname(sample_path)
    filename = os.path.basename(sample_path)
    m = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
    if not m:
        raise click.BadParameter(
            f"Path must contain an index number, e.g., Problem_1.png: {sample_path}"
        )
    prefix, _, ext = m.groups()
    return dirname, prefix, ext


def _read_file_text(client: OpenAI, file_id: str) -> str:
    """Download a file's content as text (for batch outputs/errors)."""
    stream = client.files.content(file_id)
    # Try common interfaces across client versions
    if hasattr(stream, "read"):
        data = stream.read()
        try:
            return data.decode("utf-8")
        except Exception:
            return data if isinstance(data, str) else ""
    if hasattr(stream, "text"):
        return stream.text
    if hasattr(stream, "content"):
        try:
            return stream.content.decode("utf-8")
        except Exception:
            return str(stream.content)
    return ""


def _get_batch_value(batch, key, default=None):
    try:
        if hasattr(batch, key):
            return getattr(batch, key)
    except Exception:
        pass
    try:
        if isinstance(batch, dict) and key in batch:
            return batch[key]
    except Exception:
        pass
    try:
        # Some clients expose .model_dump() or .to_dict()
        if hasattr(batch, "model_dump"):
            data = batch.model_dump()
            return data.get(key, default)
        if hasattr(batch, "to_dict"):
            data = batch.to_dict()
            return data.get(key, default)
    except Exception:
        pass
    return default


def _get_output_file_id(batch) -> str:
    """Best-effort retrieval of output file id across client variants."""
    # Common names seen in the wild
    candidates = [
        "output_file_id",
        "outputFileId",
        "results_file_id",
        "response_file_id",
    ]
    for key in candidates:
        val = _get_batch_value(batch, key)
        if isinstance(val, str) and val:
            return val
        if isinstance(val, list) and val:
            return val[0]
    # Some SDKs put IDs under a nested structure
    files_obj = _get_batch_value(batch, "files") or {}
    if isinstance(files_obj, dict):
        for key in ["output", "result", "responses"]:
            val = files_obj.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, list) and val:
                return val[0]
    return ""


def _extract_output_text_from_body(body) -> str:
    """Best-effort extraction of text from Responses API batch body."""
    try:
        if isinstance(body, str):
            return body
        if not isinstance(body, dict):
            return ""
        v = body.get("output_text")
        if isinstance(v, str) and v.strip():
            return v
        output = body.get("output")
        if isinstance(output, list):
            parts = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict):
                            t = c.get("text")
                            if isinstance(t, str) and t.strip():
                                parts.append(t)
            if parts:
                return "\n".join(parts)
        # Fallback to chat-like schema if present
        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    ctext = message.get("content")
                    if isinstance(ctext, str) and ctext.strip():
                        return ctext
    except Exception:
        return ""
    return ""


@click.command(
    help="Generate problem variants with o4-mini-deepresearch via Responses API. Supports single or batch image inputs."
)
@click.option(
    "-i",
    "--input",
    "inputs",
    type=click.Path(exists=True),
    multiple=True,
    help="Path(s) to problem image(s). Can be provided multiple times.",
)
@click.option(
    "-b",
    "--batch-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Directory containing images to process in batch (uses --glob pattern).",
)
@click.option(
    "--glob",
    "glob_pattern",
    type=str,
    default="*.png",
    show_default=True,
    help="Glob pattern for --batch-dir",
)
@click.option(
    "-o",
    "--out-dir",
    type=str,
    default="src/variant",
    show_default=True,
    help="Output directory for generated LaTeX snippets",
)
@click.option(
    "--model",
    type=str,
    default="o3",
    show_default=True,
    help="Model to use",
)
@click.option(
    "--num-variants",
    type=str,
    default="4",
    show_default=True,
    help="Variants to generate: either a single number N (generates 1..N) or a range like 2-5",
)
@click.option(
    "--use-batch",
    is_flag=True,
    default=False,
    help="Use OpenAI Batch API to enqueue requests for later processing",
)
@click.option(
    "--prompt-source",
    type=click.Choice(["prompts_py", "builtin"], case_sensitive=False),
    default="prompts_py",
    show_default=True,
    help="Where to fetch prompts for variants",
)
@click.option(
    "--vector-store-id",
    "vector_store_ids",
    multiple=True,
    type=str,
    default=("vs_68b0d279eb2c819181afb2b10a7141e5",),
    help="Vector store ID(s) for file_search tool (deep-research + --use-batch)",
)
@click.option(
    "--batch-status",
    "batch_status_id",
    type=str,
    default=None,
    help="Check and print status for a given batch id",
)
@click.option(
    "--batch-download",
    "batch_download_id",
    type=str,
    default=None,
    help="Download completed batch results into --out-dir",
)
@click.option(
    "-r",
    "--range",
    "ranges",
    nargs=2,
    type=int,
    default=None,
    help="When a single -i or --latex-file is given, expand over this inclusive range",
)
@click.option(
    "--latex-file",
    "-l",
    "latex_files",
    type=click.Path(exists=True),
    multiple=True,
    default=(),
    help="Path(s) to LaTeX problem file(s). Can be a single sample with --range",
)
@click.option(
    "--latex-text",
    type=str,
    default=None,
    help="Inline LaTeX problem text instead of images/files (single item)",
)
@click.option(
    "--batch-list",
    is_flag=True,
    default=False,
    help="List recent batches",
)
@click.option(
    "--batch-limit",
    type=int,
    default=20,
    show_default=True,
    help="How many recent batches to list",
)
@click.option(
    "--batch-pick",
    is_flag=True,
    default=False,
    help="After listing, interactively pick a batch",
)
@click.option(
    "--batch-action",
    type=click.Choice(["status", "download"], case_sensitive=False),
    default="status",
    show_default=True,
    help="Action to take on the picked batch",
)
@click.option(
    "--reasoning-effort",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
    default="high",
    show_default=True,
    help="Level of reasoning detail in solutions",
)
def deepvariant(inputs, batch_dir, glob_pattern, out_dir, model, num_variants, use_batch, prompt_source, vector_store_ids,
                batch_status_id, batch_download_id, ranges, latex_files, latex_text, batch_list, batch_limit, batch_pick,
                batch_action, reasoning_effort):
    console = Console()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        console.print(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.",
            style="bold red",
        )
        sys.exit(1)

    # Early: handle batch utilities (list/status/download)
    if batch_status_id or batch_download_id or batch_list:
        client = OpenAI(api_key=api_key)
        # Listing path
        if batch_list:
            try:
                listing = client.batches.list(limit=batch_limit)
            except Exception as e:
                console.print(f"Failed to list batches: {e}", style="bold red")
                sys.exit(1)
            items = getattr(listing, "data", []) or []
            if not items:
                console.print("No batches found.", style="yellow")
                sys.exit(0)
            console.print("Recent batches:", style="green")
            for idx, it in enumerate(items, start=1):
                console.print(
                    f"{idx:>2}. {it.id}  status={it.status}", style="dim")

            if batch_pick:
                choice = click.prompt(
                    "Select a batch by number", type=click.IntRange(1, len(items)))
                picked = items[choice - 1].id
                if batch_action == "status":
                    batch_status_id = picked
                else:
                    batch_download_id = picked

        if batch_status_id or batch_download_id:
            try:
                batch_id = batch_status_id or batch_download_id
                batch = client.batches.retrieve(batch_id)
            except Exception as e:
                console.print(
                    f"Failed to retrieve batch {batch_id}: {e}", style="bold red")
                sys.exit(1)

            status = _get_batch_value(batch, "status")
            console.print(f"Batch {batch.id} status: {status}", style="green")
            console.print(
                f"created_at: {_get_batch_value(batch, 'created_at')}", style="dim")

            if batch_download_id:
                output_file_id = _get_output_file_id(batch)
                if not output_file_id:
                    console.print(
                        "Batch has no output_file_id yet (not completed).", style="yellow")
                    sys.exit(1)

                os.makedirs(out_dir, exist_ok=True)
                try:
                    text = _read_file_text(client, output_file_id)
                except Exception as e:
                    console.print(
                        f"Failed downloading output: {e}", style="bold red")
                    sys.exit(1)

                saved = 0
                for line in text.splitlines():
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    custom_id = obj.get("custom_id") or "item"
                    # Shorten filename: drop any leading 'Problem_'
                    short_id = re.sub(r'^[Pp]roblem_', '', custom_id)
                    resp_body = (obj.get("response") or {}).get("body") or {}
                    out_text = _extract_output_text_from_body(
                        resp_body).strip()
                    out_name = f"variant_{short_id}.tex"
                    out_path = os.path.join(out_dir, out_name)
                    try:
                        with open(out_path, "w") as f:
                            f.write(out_text + "\n")
                        saved += 1
                        console.print(f"Saved: {out_path}", style="green")
                    except Exception as e:
                        console.print(
                            f"Failed writing {out_path}: {e}", style="bold red")

                if getattr(batch, 'error_file_id', None):
                    try:
                        err_text = _read_file_text(client, batch.error_file_id)
                        err_path = os.path.join(
                            out_dir, f"batch_{batch.id}_errors.jsonl")
                        with open(err_path, "w") as ef:
                            ef.write(err_text)
                        console.print(
                            f"Error file saved: {err_path}", style="yellow")
                    except Exception as e:
                        console.print(
                            f"Failed downloading error file: {e}", style="bold red")

                console.print(
                    f"Wrote {saved} result file(s) to {out_dir}", style="green")
            return

    # Build inputs: images vs latex (mutually exclusive)
    if (inputs or batch_dir) and (latex_text or latex_files):
        console.print(
            "Provide either images (-i/--batch-dir) OR latex (--latex-file/--latex-text), not both.",
            style="bold red",
        )
        sys.exit(1)

    image_paths: List[str] = []
    latex_items: List[Tuple[str, str]] = []  # (id, latex_text)

    if inputs or batch_dir:
        file_list: List[str] = []
        if inputs:
            file_list.extend(list(inputs))
        if batch_dir:
            file_list.extend(
                sorted(glob.glob(os.path.join(batch_dir, glob_pattern))))
        # Range expansion if a single sample provided
        if ranges and len(file_list) == 1:
            try:
                d, pfx, ext = _split_pattern(file_list[0])
            except click.BadParameter as e:
                console.print(str(e), style="bold red")
                sys.exit(1)
            start, end = ranges
            for i in range(start, end + 1):
                image_paths.append(os.path.join(d, f"{pfx}{i}{ext}"))
        else:
            image_paths = file_list
        if not image_paths:
            console.print(
                "No input files provided. Use -i or --batch-dir.", style="bold red")
            sys.exit(1)

    elif latex_text or latex_files:
        # Inline single
        if latex_text:
            latex_items.append(("inline", latex_text))
        # Files and optional range expansion
        if latex_files:
            lf = list(latex_files)
            if ranges and len(lf) == 1:
                try:
                    d, pfx, ext = _split_pattern(lf[0])
                except click.BadParameter as e:
                    console.print(str(e), style="bold red")
                    sys.exit(1)
                start, end = ranges
                for i in range(start, end + 1):
                    path = os.path.join(d, f"{pfx}{i}{ext}")
                    if not os.path.exists(path):
                        console.print(
                            f"Skipping missing file: {path}", style="yellow")
                        continue
                    with open(path, "r") as f:
                        latex_items.append((f"{pfx}{i}", f.read()))
            else:
                for path in lf:
                    if not os.path.exists(path):
                        console.print(
                            f"Skipping missing file: {path}", style="yellow")
                        continue
                    with open(path, "r") as f:
                        stem = os.path.splitext(os.path.basename(path))[0]
                        latex_items.append((stem, f.read()))
        if not latex_items:
            console.print("No latex inputs provided.", style="bold red")
            sys.exit(1)
    else:
        console.print("No inputs provided.", style="bold red")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    client = OpenAI(api_key=api_key)

    # Prepare prompt set
    selected_prompts: List[str] = []
    if prompt_source == "prompts_py":
        try:
            from .prompts import (
                prompt_mcq_variant_with_gpt_5,
                prompt_mcq_context_variant_with_gpt_5,
                prompt_mcq_numerical_variant_with_gpt_5,
                prompt_mcq_conceptual_variant_with_gpt_5,
                prompt_mcq_conceptual_plus__variant_with_gpt_5,
            )
            selected_prompts = [
                prompt_mcq_variant_with_gpt_5,
                prompt_mcq_context_variant_with_gpt_5,
                prompt_mcq_numerical_variant_with_gpt_5,
                prompt_mcq_conceptual_variant_with_gpt_5,
                prompt_mcq_conceptual_plus__variant_with_gpt_5,
            ]
        except Exception as e:
            console.print(
                f"Failed loading prompts from prompts.py, falling back to builtin: {e}",
                style="yellow",
            )
            selected_prompts = [PROMPT_DEEP_VARIANTS[reasoning_effort]]
    else:
        selected_prompts = [PROMPT_DEEP_VARIANTS[reasoning_effort]]

    def _parse_variant_spec(spec: str) -> List[int]:
        s = (spec or "").strip()
        if not s:
            return [1]
        # Allow N, start-end, start..end, start:end
        m = re.match(r"^(\d+)$", s)
        if m:
            n = int(m.group(1))
            return list(range(1, max(1, n) + 1))
        m = re.match(r"^(\d+)\s*[-:.]{1,2}\s*(\d+)$", s)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b:
                return list(range(a, b + 1))
            else:
                return list(range(a, b - 1, -1))
        # Fallback: try comma-separated values
        parts = [p.strip() for p in re.split(r"[,\s]+", s) if p.strip()]
        vals: List[int] = []
        for p in parts:
            if p.isdigit():
                vals.append(int(p))
        return vals or [1]

    variant_indices = _parse_variant_spec(num_variants)

    processed = 0

    if use_batch:
        # Build batch JSONL of multiple responses inputs
        batch_lines: List[dict] = []
        if image_paths:
            for image_path in image_paths:
                if not os.path.exists(image_path):
                    console.print(
                        f"Skipping missing file: {image_path}", style="yellow")
                    continue
                try:
                    b64 = encode_image(image_path)
                except Exception as e:
                    console.print(
                        f"Failed to read {image_path}: {e}", style="bold red")
                    continue

                stem = os.path.splitext(os.path.basename(image_path))[0]
                for k in variant_indices:
                    prompt_text = selected_prompts[(
                        k - 1) % len(selected_prompts)]
                    body = {
                        "model": model,
                        "input": _build_responses_input(prompt_text, [b64]),
                        "text": {"format": {"type": "text"}},
                        "reasoning": {"effort": reasoning_effort},
                        "store": True
                    }
                    if "deep-research" in model:
                        if not vector_store_ids:
                            console.print(
                                "--use-batch with deep-research model requires --vector-store-id (one or more).",
                                style="bold red",
                            )
                            sys.exit(1)
                        body["tools"] = [{
                            "type": "file_search",
                            "vector_store_ids": list(vector_store_ids),
                        }]
                    batch_lines.append({
                        "custom_id": f"{stem}_{k}",
                        "method": "POST",
                        "url": "/v1/responses",
                        "body": body,
                    })
        if latex_items:
            for stem, text in latex_items:
                for k in variant_indices:
                    prompt_text = selected_prompts[(
                        k - 1) % len(selected_prompts)]
                    body = {
                        "model": model,
                        "input": _build_responses_input(prompt_text, [], [text]),
                        "reasoning_effort": reasoning_effort
                    }
                    if "deep-research" in model:
                        if not vector_store_ids:
                            console.print(
                                "--use-batch with deep-research model requires --vector-store-id (one or more).",
                                style="bold red",
                            )
                            sys.exit(1)
                        body["tools"] = [{
                            "type": "file_search",
                            "vector_store_ids": list(vector_store_ids),
                        }]
                    batch_lines.append({
                        "custom_id": f"{stem}_{k}",
                        "method": "POST",
                        "url": "/v1/responses",
                        "body": body,
                    })

        if not batch_lines:
            console.print("No batch items to enqueue.", style="bold red")
            sys.exit(1)

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".jsonl") as tf:
            for line in batch_lines:
                tf.write(json.dumps(line) + "\n")
            tf_path = tf.name

        try:
            upload = client.files.create(
                file=open(tf_path, "rb"), purpose="batch")
            batch = client.batches.create(
                input_file_id=upload.id,
                endpoint="/v1/responses",
                completion_window="24h",
            )
            console.print(
                f"Enqueued batch {batch.id} with {len(batch_lines)} items. It will process later at lower cost.",
                style="green",
            )
            console.print(
                "Note: Retrieve results via the Batches API once completed.", style="dim")
        except Exception as e:
            console.print(f"Batch enqueue failed: {e}", style="bold red")
            sys.exit(1)

        return

    # Immediate generation (non-batch)
    if image_paths:
        for image_path in image_paths:
            if not os.path.exists(image_path):
                console.print(
                    f"Skipping missing file: {image_path}", style="yellow")
                continue

            try:
                b64 = encode_image(image_path)
            except Exception as e:
                console.print(
                    f"Failed to read {image_path}: {e}", style="bold red")
                continue

            stem = os.path.splitext(os.path.basename(image_path))[0]
            for k in variant_indices:
                prompt_text = selected_prompts[(k - 1) % len(selected_prompts)]
                input_payload = _build_responses_input(prompt_text, [b64])

                try:
                    kwargs = {
                        "model": model,
                        "input": input_payload,
                        "text": {"format": {"type": "text"}},
                        "reasoning": {"effort": reasoning_effort},
                        "store": True
                    }
                    if "deep-research" in model:
                        kwargs["tools"] = [{"type": "web_search_preview"}]
                    resp = client.responses.create(**kwargs)
                    text = getattr(resp, "output_text", None)
                    if not text:
                        try:
                            text = resp.output[0].content[0].text
                        except Exception:
                            text = ""
                    text = (text or "").strip()
                except Exception as e:
                    console.print(
                        f"API error for {image_path} (variant {k}): {e}", style="bold red")
                    continue

                out_name = _infer_output_name(image_path)
                # Insert variant index
                base, ext = os.path.splitext(out_name)
                out_name_k = f"{base}_{k}{ext}"
                out_path = os.path.join(out_dir, out_name_k)
                try:
                    with open(out_path, "w") as f:
                        f.write(text + "\n")
                    console.print(f"Variant saved: {out_path}", style="green")
                    sys.stdout.flush()
                    processed += 1
                except Exception as e:
                    console.print(
                        f"Failed writing {out_path}: {e}", style="bold red")

    if latex_items:
        for stem, text_src in latex_items:
            for k in variant_indices:
                prompt_text = selected_prompts[(k - 1) % len(selected_prompts)]
                input_payload = _build_responses_input(
                    prompt_text, [], [text_src])

                try:
                    kwargs = {
                        "model": model,
                        "input": input_payload,
                        "text": {"format": {"type": "text"}},
                        "reasoning": {"effort": reasoning_effort},
                        "store": True
                    }
                    if "deep-research" in model:
                        kwargs["tools"] = [{"type": "web_search_preview"}]
                    resp = client.responses.create(**kwargs)
                    out_text = getattr(resp, "output_text", None)
                    if not out_text:
                        try:
                            out_text = resp.output[0].content[0].text
                        except Exception:
                            out_text = ""
                    out_text = (out_text or "").strip()
                except Exception as e:
                    console.print(
                        f"API error for latex item {stem} (variant {k}): {e}", style="bold red")
                    continue

                short_id = re.sub(r'^[Pp]roblem_', '', stem)
                out_name = f"variant_{short_id}_{k}.tex"
                out_path = os.path.join(out_dir, out_name)
                try:
                    with open(out_path, "w") as f:
                        f.write(out_text + "\n")
                    console.print(f"Variant saved: {out_path}", style="green")
                    sys.stdout.flush()
                    processed += 1
                except Exception as e:
                    console.print(
                        f"Failed writing {out_path}: {e}", style="bold red")

    console.print(
        f"Completed {processed} file(s). Output in {out_dir}", style="green")
