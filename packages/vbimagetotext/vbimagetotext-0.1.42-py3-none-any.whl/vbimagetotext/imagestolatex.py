import os
import click
import re
import json
from pathlib import Path
from rich.console import Console
import requests
from .functions import encode_image
from .choice_option import ChoiceOption


def call_vision_api(image_path: str, prompt: str, model: str, max_tokens: int, api_key: str) -> str:
    """Send image to OpenAI vision model and return raw response text."""
    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"}},
                ],
            }
        ],
        # "max_tokens": max_tokens,
    }

    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def split_problems(latex: str) -> list[str]:
    """Split combined LaTeX into individual problem snippets from \item to \end{solution}."""
    pattern = re.compile(r"\\item[\s\S]*?\\end{solution}")
    matches = pattern.findall(latex)
    if matches:
        return matches
    # Fallback: split by \item even if no solution env
    parts = re.split(r"(?=\\item)", latex)
    return [p.strip() for p in parts if p.strip()]


def transcribe_to_latex(image_path: str, prompt: str | None = None, model: str = "gpt-4.1", max_tokens: int = 3000, output_dir: str | None = None) -> dict:
    """
    Programmatic API: call vision model to transcribe an image to LaTeX and optionally
    split into per-problem snippets.

    Returns dict with keys: latex (str), combined_path (str|None), problems (List[str] or paths if output_dir)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    DEFAULT_PROMPT = (
        "Please transcribe the entire page into LaTeX. Represent each numbered problem using an enumerate environment; "
        "start every problem with \\item followed by the question text exactly as shown. For options, use a tasks environment "
        "with two columns (\\begin{tasks}(2) ... \\end{tasks}). Do not include any preamble or \\documentclass lines. "
        "Return only the LaTeX snippet from the first \\item through the last problem, nothing else."
    )

    if not prompt:
        prompt = DEFAULT_PROMPT

    latex = call_vision_api(image_path, prompt, model, max_tokens, api_key)

    problems = split_problems(latex)
    combined_path: str | None = None
    written: list[str] = []
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        combined_path = str(Path(output_dir) / "combined.tex")
        Path(combined_path).write_text(latex)
        for idx, snippet in enumerate(problems, start=1):
            fp = Path(output_dir) / f"problem_{idx}.tex"
            Path(fp).write_text(snippet)
            written.append(str(fp))
    return {"latex": latex, "combined_path": combined_path, "problems": (written or problems)}


@click.command(help="Generate LaTeX for all problems in an image and split into separate .tex files.")
@click.option(
    "-i",
    "--image",
    type=click.Path(exists=True),
    required=True,
    help="Path to the image file"
)
@click.option(
    "-p",
    "--prompt",
    default="",
    help="Custom prompt (optional). If omitted, uses the built-in simple LaTeX extraction prompt.",
)
@click.option("-m", "--model", default="gpt-4.1", show_default=True, type=str, help="OpenAI vision-capable model")
@click.option("--max-tokens", default=3000, show_default=True, type=int)
@click.option("-o", "--output-dir", default="problems", show_default=True, type=str, help="Directory to save individual problem tex files")
def imagestolatex(image: str, prompt: str, model: str, max_tokens: int, output_dir: str):
    console = Console()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("OPENAI_API_KEY not set", style="bold red")
        return

    DEFAULT_PROMPT = (
        "Please transcribe the entire page into LaTeX. Represent each numbered problem using an enumerate environment; "
        "start every problem with \\item followed by the question text exactly as shown. For options, use a tasks environment "
        "with two columns (\\begin{tasks}(2) ... \\end{tasks}). Do not include any preamble or \documentclass lines. "
        "Return only the LaTeX snippet from the first \\item through the last problem, nothing else."
    )

    if not prompt:
        prompt = DEFAULT_PROMPT

    console.print("Calling model…", style="cyan")
    latex = call_vision_api(image, prompt, model, max_tokens, api_key)

    console.rule("Model Response (raw)")
    console.print(latex, style="magenta")
    console.rule()

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    combined_path = Path(output_dir) / "combined.tex"
    combined_path.write_text(latex)
    console.print(f"Saved combined LaTeX to {combined_path}", style="green")

    problems = split_problems(latex)
    for idx, snippet in enumerate(problems, start=1):
        file_path = Path(output_dir) / f"problem_{idx}.tex"
        file_path.write_text(snippet)
        console.print(f"Wrote {file_path}", style="green")

    console.print(f"✅ Extracted {len(problems)} problems.")


if __name__ == "__main__":
    imagestolatex()
