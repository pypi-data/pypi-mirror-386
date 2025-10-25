import os
import glob
import re
import json
import tempfile
from pathlib import Path
import zipfile
import click
from rich.console import Console
from openai import OpenAI


SIM_ANIM_TEMPLATE = """
from manim import *

class ProblemAnimation(Scene):
    def construct(self):
        title = Text("{title}", font_size=36).to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Placeholder animation; replace with model-generated logic later
        note = Text("Auto-generated stub animation", font_size=28)
        self.play(FadeIn(note))
        self.wait(1)

        tri = VGroup(
            Arrow(ORIGIN, RIGHT*2, buff=0, color=GREEN),
            Arrow(RIGHT*2, RIGHT*2 + UP*1, buff=0, color=BLUE),
            Arrow(ORIGIN, RIGHT*2 + UP*1, buff=0, color=YELLOW)
        ).shift(DOWN)
        labels = VGroup(
            MathTex(r"\\vec{a}").next_to(tri[0], DOWN),
            MathTex(r"\\vec{b}").next_to(tri[1], RIGHT),
            MathTex(r"\\vec{a}+\\vec{b}").next_to(tri[2], UP+LEFT)
        )
        self.play(Create(tri), Write(labels))
        self.wait(2)
""".strip()


def _anim_script_for(stem: str) -> str:
    title = stem.replace("_", " ").title()
    return SIM_ANIM_TEMPLATE.replace("{title}", title)


@click.group(help="Generate and manage Manim animations from problem/variant TeX files.")
def simulate():
    pass


PROMPT_MANIM = (
    "You are an expert educator and Manim animator. Read the LaTeX problem below and produce a single Python script that uses Manim (from manim import *) to visually simulate or illustrate the scenario. "
    "Constraints: 1) Return ONLY valid Python code, no backticks, no explanations. 2) Include exactly one Scene subclass (e.g., class ProblemAnimation(Scene):). 3) Avoid external assets. 4) Prefer simple primitives: Text, MathTex, Arrow, Dot, Line, VGroup, animations like GrowArrow, MoveAlongPath. 5) Keep it 30–60 seconds long at normal speed. 6) Add concise on-screen labels for vectors/quantities if relevant. 7) If the problem is conceptual without numbers, animate the relationships qualitatively. 8) Do not include a main guard or CLI code."
)


def _build_responses_input_for_manim(prompt_text: str, latex_text: str):
    return [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt_text},
                {"type": "input_text", "text": f"LaTeX problem snippet:\n{latex_text}"},
            ],
        }
    ]


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


def _get_batch_output_file_id(batch) -> str:
    candidates = ["output_file_id", "outputFileId",
                  "results_file_id", "response_file_id"]
    for key in candidates:
        try:
            val = getattr(batch, key, None)
        except Exception:
            val = None
        if isinstance(val, str) and val:
            return val
        if isinstance(val, list) and val:
            return val[0]
    files_obj = getattr(batch, "files", None)
    if isinstance(files_obj, dict):
        for key in ["output", "result", "responses"]:
            val = files_obj.get(key)
            if isinstance(val, str) and val:
                return val
            if isinstance(val, list) and val:
                return val[0]
    return ""


@simulate.command("generate", help="Generate Manim scripts into src/animations from input .tex files (supports Responses API and batch)")
@click.option("-d", "--dir", "dir_path", default="src/src_tex", show_default=True, type=click.Path(file_okay=False))
@click.option("--pattern", default="problem_*.tex", show_default=True, help="Glob inside --dir (e.g., problem_*.tex or variant_*.tex)")
@click.option("-r", "--range", "range_", nargs=2, type=int, default=None, help="Inclusive start end indices; expands filenames using a sample matched by --pattern")
@click.option("-o", "--output-dir", default="src/animations", show_default=True, type=click.Path(file_okay=False))
@click.option("--model", default="o3", show_default=True, help="Model (e.g., o3, gpt-5)")
@click.option("--effort", default="high", type=click.Choice(["low", "medium", "high"]), show_default=True, help="Reasoning effort for Responses API")
@click.option("--use-batch", is_flag=True, default=False, help="Enqueue batch via OpenAI Batches API instead of immediate generation")
@click.option("--batch-status", default=None, help="Check status of a batch id")
@click.option("--batch-download", default=None, help="Download results for a completed batch id into --output-dir")
@click.option("--batch-list", is_flag=True, default=False, help="List recent batches")
@click.option("--batch-limit", default=20, show_default=True, type=int, help="How many recent batches to list")
@click.option("--batch-pick", is_flag=True, default=False, help="After listing, interactively pick a batch by number")
@click.option("--batch-action", type=click.Choice(["status", "download"], case_sensitive=False), default="status", show_default=True, help="Action for picked batch")
def generate_cmd(dir_path: str, pattern: str, output_dir: str, model: str, effort: str, use_batch: bool, batch_status: str | None, batch_download: str | None, batch_list: bool, batch_limit: int, batch_pick: bool, batch_action: str, range_: tuple[int, int] | None):
    console = Console()
    files = sorted(glob.glob(os.path.join(dir_path, pattern)))
    # Range expansion (single numeric index like problem_1.tex)
    if range_ is not None:
        start, end = range_
        sample = None
        for p in files:
            if re.match(r"^(.*?)(\d+)(\.[^.]+)$", os.path.basename(p)):
                sample = p
                break
        if sample is None:
            console.print(
                "Could not infer filename pattern from --pattern; ensure at least one matching file like problem_1.tex exists.", style="bold red")
            return
        m = re.match(r"^(.*?)(\d+)(\.[^.]+)$", os.path.basename(sample))
        prefix, _, ext = m.groups()
        base_dir = os.path.dirname(sample)
        files = [os.path.join(base_dir, f"{prefix}{i}{ext}")
                 for i in range(start, end + 1)]
    os.makedirs(output_dir, exist_ok=True)

    api_key = os.getenv("OPENAI_API_KEY")
    if (use_batch or batch_status or batch_download or batch_list or batch_pick) and not api_key:
        console.print("OPENAI_API_KEY not set", style="bold red")
        return

    client = OpenAI(api_key=api_key) if api_key else None

    # Batch utilities
    # Guard: if user provided only --batch-action without any batch control flags, show help and exit
    if batch_action and not (batch_status or batch_download or batch_list or batch_pick):
        console.print("--batch-action requires either --batch-list/--batch-pick or --batch-status/--batch-download.", style="yellow")
        return

    if batch_list:
        try:
            listing = client.batches.list(limit=batch_limit)
        except Exception as e:
            console.print(f"Failed to list batches: {e}", style="bold red")
            return
        items = getattr(listing, "data", []) or []
        if not items:
            console.print("No batches found.", style="yellow")
            return
        console.print("Recent batches:")
        for idx, it in enumerate(items, start=1):
            console.print(f"{idx:>2}. {it.id}  status={getattr(it,'status','?')}", style="dim")
        if batch_pick:
            choice = click.prompt("Select a batch by number", type=click.IntRange(1, len(items)))
            picked = items[choice - 1].id
            if batch_action == "status":
                batch_status = picked
            else:
                batch_download = picked
        else:
            # If only listing was requested, exit without running generation
            return
    if batch_status:
        try:
            b = client.batches.retrieve(batch_status)
            console.print(f"Batch {b.id} status: {getattr(b, 'status', '?')}")
            return
        except Exception as e:
            console.print(f"Failed to retrieve batch: {e}", style="bold red")
            return

    if batch_download:
        try:
            b = client.batches.retrieve(batch_download)
            out_id = _get_batch_output_file_id(b)
            if not out_id:
                console.print(
                    "Batch not completed or no output file id.", style="yellow")
                return
            text = _read_file_text(client, out_id)
            saved = 0
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                stem = obj.get("custom_id") or f"anim_{saved+1}"
                body = ((obj.get("response") or {}).get("body") or {})
                code = _extract_output_text_from_body(body).strip()
                if not code:
                    continue
                out_py = os.path.join(output_dir, f"{stem}.py")
                Path(out_py).write_text(code)
                console.print(f"Saved: {out_py}", style="green")
                saved += 1
            console.print(f"Wrote {saved} file(s) to {output_dir}")
            return
        except Exception as e:
            console.print(f"Failed batch download: {e}", style="bold red")
            return

    if use_batch:
        if not files:
            console.print(
                f"No files matching {pattern} under {dir_path}", style="bold red")
            return
        batch_lines: list[dict] = []
        for fp in files:
            stem = Path(fp).stem
            latex_text = Path(fp).read_text()
            body = {
                "model": model,
                "reasoning": {"effort": effort},
                "input": _build_responses_input_for_manim(PROMPT_MANIM, latex_text),
            }
            batch_lines.append({
                "custom_id": stem,
                "method": "POST",
                "url": "/v1/responses",
                "body": body,
            })
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".jsonl") as tf:
            for line in batch_lines:
                tf.write(json.dumps(line) + "\n")
            tf_path = tf.name
        try:
            upload = client.files.create(
                file=open(tf_path, "rb"), purpose="batch")
            batch = client.batches.create(
                input_file_id=upload.id, endpoint="/v1/responses", completion_window="24h")
            console.print(
                f"Enqueued batch {batch.id} with {len(batch_lines)} items.", style="green")
            console.print(
                "Use: vbimagetotext simulate generate --batch-status <id> or --batch-download <id>")
        except Exception as e:
            console.print(f"Batch enqueue failed: {e}", style="bold red")
        return

    # Immediate generation (non-batch)
    if not files:
        click.echo(f"No files matching {pattern} under {dir_path}")
        return
    if not api_key:
        console.print("OPENAI_API_KEY not set", style="bold red")
        return
    created = 0
    for fp in files:
        stem = Path(fp).stem
        if not os.path.exists(fp):
            console.print(f"Skipping missing file: {fp}", style="yellow")
            continue
        latex_text = Path(fp).read_text()
        try:
            # omit temperature: some Responses models (o3/gpt-5) don't accept it
            resp = client.responses.create(
                model=model,
                reasoning={"effort": effort},
                input=_build_responses_input_for_manim(
                    PROMPT_MANIM, latex_text),
            )
            code = getattr(resp, "output_text", None)
            if not code:
                try:
                    code = resp.output[0].content[0].text
                except Exception:
                    code = ""
            code = (code or "").strip()
        except Exception as e:
            msg = str(e)
            # Retry once with a minimal payload if invalid_request occurs
            if "Unsupported parameter" in msg or "invalid_request" in msg:
                try:
                    resp = client.responses.create(
                        model=model,
                        input=_build_responses_input_for_manim(
                            PROMPT_MANIM, latex_text),
                    )
                    code = getattr(resp, "output_text", None)
                    if not code:
                        try:
                            code = resp.output[0].content[0].text
                        except Exception:
                            code = ""
                    code = (code or "").strip()
                except Exception as e2:
                    console.print(
                        f"API error for {fp}: {e2}", style="bold red")
                    continue
            else:
                console.print(f"API error for {fp}: {e}", style="bold red")
                continue

        if not code:
            console.print(f"Empty response for {fp}", style="yellow")
            continue

        out_py = os.path.join(output_dir, f"{stem}.py")
        Path(out_py).write_text(code)
        console.print(f"Wrote {out_py}")
        created += 1
    console.print(f"Generated {created} animation script(s) in {output_dir}")


@simulate.command("status", help="Show count of animations in output directory")
@click.option("-o", "--output-dir", default="src/animations", show_default=True, type=click.Path(file_okay=False))
def status_cmd(output_dir: str):
    if not os.path.isdir(output_dir):
        click.echo(f"No directory: {output_dir}")
        return
    files = sorted(Path(output_dir).glob("*.py"))
    click.echo(f"{len(files)} animation script(s) in {output_dir}")
    for p in files[:20]:
        click.echo(f"- {p}")
    if len(files) > 20:
        click.echo(f"... (+{len(files)-20} more)")


@simulate.command("export", help="Zip animations from output directory")
@click.option("-o", "--output-dir", default="src/animations", show_default=True, type=click.Path(file_okay=False))
@click.option("-f", "--file", "zip_path", required=True, help="Output zip file path")
def export_cmd(output_dir: str, zip_path: str):
    if not os.path.isdir(output_dir):
        click.echo(f"No directory: {output_dir}")
        return
    files = sorted(Path(output_dir).glob("*.py"))
    if not files:
        click.echo("No animation .py files to export")
        return
    os.makedirs(os.path.dirname(zip_path) or ".", exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(str(p), arcname=p.name)
    click.echo(f"Wrote {zip_path} with {len(files)} files")
