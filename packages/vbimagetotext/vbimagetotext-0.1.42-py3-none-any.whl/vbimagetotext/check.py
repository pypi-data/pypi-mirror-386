import click
import os
import re
import sys
import json
import glob
import tempfile
from typing import List, Tuple

from rich.console import Console
from openai import OpenAI


CHECK_PROMPT = (
    "You are an expert problem checker and LaTeX typesetter. You will receive a LaTeX MCQ snippet that starts at \\item and ends after \\end{solution}.\n"
    "Task: Verify mathematical correctness, internal consistency, dimensional sanity, and that the marked option (\\ans) matches the solution.\n"
    "If any inconsistency or error is found, FIX IT: adjust the statement/context, numbers, options, and/or solution steps so that everything is consistent.\n"
    "Strict output: Return ONLY the corrected LaTeX snippet from \\item up to and including \\end{solution}. No preamble, no commentary, no extra text. Keep inline math in $...$."
)

CHECK_PROMPT = r"""
You are an expert problem checker and LaTeX typesetter.

INPUT: One LaTeX MCQ snippet that starts at \item and ends at \end{solution} (includes options, solution, and \ans).

TASK:
1. Verify full correctness:
   - Check every mathematical and logical step in the solution.
   - Recalculate all arithmetic accurately.
   - Ensure dimensional/unit consistency.
   - Ensure the marked option (\ans) matches the final computed result.
   - Guarantee exactly one correct option. If multiple or none are correct, minimally adjust problem data, options, or solution so that there is a unique correct choice.

2. If errors/inconsistencies exist:
   - Fix the problem statement, numbers, options, and/or solution so everything is self-consistent.
   - Preserve notation; if new symbols are introduced, define them.
   - Align units and rounding conventions consistently.
   - Adjust \ans to the correct option.

3. Formatting requirements:
   - Preserve the structure:
        \item ... (problem + optional diagram)
        \begin{tasks}(2) ... \end{tasks}
        \begin{solution} ... \end{solution}
        \ans{...}
   - Solution must use \begin{align*}...\end{align*}.
   - Show one calculation step per line.
   - Use \intertext{} only for short explanations between steps.
   - Use $...$ for inline math; display equations as needed.
   - No blank lines inside align*.
   - Ensure LaTeX compiles (balanced braces/environments).

STRICT OUTPUT:
Return ONLY the corrected LaTeX snippet from \item up to and including \end{solution}.
Do not include any commentary, explanation, code fences, or extra text.
"""


def _split_variant_sample(sample_path: str) -> Tuple[str, str, str]:
    """Parse a sample like src/variant/variant_1_1.tex -> (dir, prefix 'variant_', ext '.tex')."""
    dirname = os.path.dirname(sample_path)
    filename = os.path.basename(sample_path)
    m = re.match(r"^(.*?)(\d+)_(\d+)(\.[^.]+)$", filename)
    if not m:
        raise click.BadParameter(
            "Input filename must end with '<prefix><A>_<B><ext>', e.g., variant_1_1.tex"
        )
    prefix, _, _, ext = m.groups()
    return dirname, prefix, ext


def _build_responses_input(prompt_text: str, latex_text: str):
    return [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt_text},
                {"type": "input_text", "text": latex_text},
            ],
        }
    ]


def _read_file_text(client: OpenAI, file_id: str) -> str:
    stream = client.files.content(file_id)
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


def _extract_output_text_from_body(body) -> str:
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
                if isinstance(item, dict):
                    content = item.get("content")
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict):
                                t = c.get("text")
                                if isinstance(t, str) and t.strip():
                                    parts.append(t)
            if parts:
                return "\n".join(parts)
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
    help="Check and correct LaTeX MCQ variants via Responses Batch API; outputs to variant_checked/"
)
@click.option(
    "-i",
    "--input",
    "input_sample",
    type=click.Path(exists=True),
    required=False,
    help="Sample variant file path (e.g., src/variant/variant_1_1.tex) used with -R/-r to expand",
)
@click.option(
    "-R",
    "--Variant-range",
    "range_A",
    nargs=2,
    type=int,
    default=None,
    help="Inclusive range for the VARIANT index (second) in variant_<problem>_<variant>.tex",
)
@click.option(
    "-r",
    "--range",
    "range_B",
    nargs=2,
    type=int,
    default=None,
    help="Inclusive range for the PROBLEM index (first) in variant_<problem>_<variant>.tex",
)
@click.option(
    "-o",
    "--out-dir",
    type=str,
    default="src/variant_checked",
    show_default=True,
    help="Directory to write checked files",
)
@click.option(
    "--model",
    type=str,
    default="o3",
    show_default=True,
    help="Model to use for checking",
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
def check(input_sample, range_A, range_B, out_dir, model, batch_list, batch_limit, batch_pick, batch_action, batch_status_id, batch_download_id):
    console = Console()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        console.print(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.",
            style="bold red",
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Batch utilities
    if batch_list or batch_status_id or batch_download_id:
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

            console.print(
                f"Batch {batch.id} status: {batch.status}", style="green")
            if batch_download_id:
                out_id = getattr(batch, 'output_file_id', None)
                if not out_id:
                    console.print(
                        "Batch has no output_file_id yet (not completed).", style="yellow")
                    sys.exit(1)
                os.makedirs(out_dir, exist_ok=True)
                try:
                    text = _read_file_text(client, out_id)
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
                    body = (obj.get("response") or {}).get("body") or {}
                    out_text = _extract_output_text_from_body(body).strip()
                    out_name = f"{custom_id}.tex"
                    out_path = os.path.join(out_dir, out_name)
                    try:
                        with open(out_path, "w") as f:
                            f.write(out_text + "\n")
                        console.print(f"Saved: {out_path}", style="green")
                        saved += 1
                    except Exception as e:
                        console.print(
                            f"Failed writing {out_path}: {e}", style="bold red")

                console.print(
                    f"Wrote {saved} result file(s) to {out_dir}", style="green")
        return

    if not input_sample or not (range_A and range_B):
        console.print(
            "Provide -i sample like src/variant/variant_1_1.tex along with -R A1 A2 and -r B1 B2",
            style="bold red",
        )
        sys.exit(1)

    try:
        dirname, prefix, ext = _split_variant_sample(input_sample)
    except click.BadParameter as e:
        console.print(str(e), style="bold red")
        sys.exit(1)

    # Map: -r (range_B) -> problem index (first); -R (range_A) -> variant index (second)
    problem_start, problem_end = range_B
    variant_start, variant_end = range_A

    batch_lines: List[dict] = []
    for problem_idx in range(problem_start, problem_end + 1):
        for variant_idx in range(variant_start, variant_end + 1):
            path = os.path.join(
                dirname, f"{prefix}{problem_idx}_{variant_idx}{ext}")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                latex_text = f.read()

            body = {
                "model": model,
                "input": _build_responses_input(CHECK_PROMPT, latex_text),
            }
            custom_id = f"variant_{problem_idx}_{variant_idx}"
            batch_lines.append({
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/responses",
                "body": body,
            })

    if not batch_lines:
        console.print(
            "No matching input files found for the given ranges.", style="bold red")
        sys.exit(1)

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".jsonl") as tf:
        for line in batch_lines:
            tf.write(json.dumps(line) + "\n")
        tf_path = tf.name

    try:
        upload = client.files.create(file=open(tf_path, "rb"), purpose="batch")
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
            "Use --batch-status/--batch-download to retrieve results.", style="dim")
    except Exception as e:
        console.print(f"Batch enqueue failed: {e}", style="bold red")
        sys.exit(1)
