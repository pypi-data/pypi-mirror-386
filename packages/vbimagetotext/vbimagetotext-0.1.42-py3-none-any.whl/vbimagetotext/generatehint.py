import click
import os
import re
import sys
from typing import Tuple, List

from rich.console import Console
from openai import OpenAI

from .functions import encode_image


def _split_pattern(sample_path: str) -> Tuple[str, str, str]:
    dirname = os.path.dirname(sample_path)
    filename = os.path.basename(sample_path)
    match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
    if not match:
        raise click.BadParameter(
            f"Path must contain an index number, e.g., Problem_1.png or problem_1.tex: {sample_path}"
        )
    prefix, _, ext = match.groups()
    return dirname, prefix, ext


def _build_responses_input(prompt_text: str, image_b64_list: List[str]):
    """
    Build input payload for Responses API: user message containing prompt text and images.
    """
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

    return [
        {
            "role": "user",
            "content": content_items,
        }
    ]


@click.command(
    help="Generate concise hints for problems. Supports (A) image + solution .tex pairs, or (B) a single .tex containing both problem and solution. Saves to src/hint/problem_{i}.tex"
)
@click.option(
    "-i",
    "--input",
    "inputs",
    type=click.Path(exists=True),
    required=True,
    multiple=True,
    help="Provide either two sample paths (image then solution .tex), or a single .tex sample that contains both problem and solution.",
)
@click.option(
    "-r",
    "--range",
    "problem_range",
    nargs=2,
    type=int,
    required=True,
    help="Range of problems to process (start end), inclusive.",
)
@click.option(
    "--model",
    type=str,
    default="gpt-5",
    show_default=True,
    help="Model to use for hint generation",
)
@click.option(
    "--reasoning-effort",
    "reasoning_effort",
    cls=click.Option,
    type=click.Choice(["minimal", "low", "medium", "high"],
                      case_sensitive=False),
    default="medium",
    show_default=True,
    help="Reasoning effort level",
)
def generatehint(inputs, problem_range, model, reasoning_effort):
    console = Console()

    if len(inputs) == 2:
        mode = "pair"
        image_sample, solution_sample = inputs
    elif len(inputs) == 1:
        mode = "single_tex"
        tex_sample = inputs[0]
        if not tex_sample.lower().endswith(".tex"):
            raise click.BadParameter(
                "Single-input mode requires a .tex sample that contains both problem and solution."
            )
    else:
        raise click.BadParameter(
            "Provide either two inputs (image + solution .tex) or a single .tex sample containing both."
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        console.print(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.",
            style="bold red",
        )
        sys.exit(1)

    if mode == "pair":
        image_dir, image_prefix, image_ext = _split_pattern(image_sample)
        sol_dir, sol_prefix, sol_ext = _split_pattern(solution_sample)
    else:
        tex_dir, tex_prefix, tex_ext = _split_pattern(tex_sample)

    os.makedirs(os.path.join("src", "hint"), exist_ok=True)

    client = OpenAI(api_key=api_key)

    start, end = problem_range
    generated_count = 0
    for i in range(start, end + 1):
        if mode == "pair":
            image_path = os.path.join(
                image_dir, f"{image_prefix}{i}{image_ext}")
            tex_path = os.path.join(sol_dir, f"{sol_prefix}{i}{sol_ext}")

            if not os.path.exists(image_path):
                console.print(
                    f"Skipping missing image: {image_path}", style="yellow")
                continue
            if not os.path.exists(tex_path):
                console.print(
                    f"Skipping missing solution: {tex_path}", style="yellow")
                continue

            with open(tex_path, "r") as f:
                solution_tex = f.read()

            m = re.search(
                r"\\begin{solution}([\s\S]*?)\\end{solution}", solution_tex, re.DOTALL)
            solution_inner = m.group(1).strip() if m else solution_tex.strip()

            base64_image = encode_image(image_path)

            prompt_text = (
                "You are a helpful tutor. Given a problem image and its solution context, "
                "produce only a concise, high-level hint describing the core idea or first step to approach the problem. "
                "Do NOT reveal the full solution, intermediate steps, formulas, or final numeric answer. "
                "Return 1-3 short sentences in LaTeX. Wrap every mathematical symbol or expression in inline math using $...$. "
                "Avoid code fences and display math."
                "Solution context (for your analysis, do not reveal steps or final results):\n" +
                solution_inner
            )

            input_payload = _build_responses_input(prompt_text, [base64_image])
        else:
            tex_path = os.path.join(tex_dir, f"{tex_prefix}{i}{tex_ext}")
            if not os.path.exists(tex_path):
                console.print(
                    f"Skipping missing tex: {tex_path}", style="yellow")
                continue
            with open(tex_path, "r") as f:
                tex_full = f.read()

            # Extract solution inner and problem text (portion before solution)
            m = re.search(
                r"\\begin{solution}([\s\S]*?)\\end{solution}", tex_full, re.DOTALL)
            solution_inner = m.group(1).strip() if m else ""
            prob_text = tex_full[: m.start()].strip(
            ) if m else tex_full.strip()

            prompt_text = (
                "You are a helpful tutor. Given a problem and its solution context, "
                "produce only a concise, high-level hint describing the core idea or first step to approach the problem. "
                "Do NOT reveal the full solution, intermediate steps, formulas, or final numeric answer. "
                "Return 1-3 short sentences in LaTeX. Wrap every mathematical symbol or expression in inline math using $...$. "
                "Avoid code fences and display math.\n\n"
                f"Problem:\n{prob_text}\n\nSolution context (for your analysis, do not reveal steps or final results):\n{solution_inner}"
            )

            # Text-only input (no images)
            input_payload = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt_text},
                    ],
                }
            ]

        try:
            resp = client.responses.create(
                model=model,
                input=input_payload,
                reasoning={"effort": reasoning_effort},
                # response_format={"type": "latex"},
            )

            hint_text = getattr(resp, "output_text", None)
            if not hint_text:
                try:
                    hint_text = resp.output[0].content[0].text
                except Exception:
                    hint_text = ""
            hint_text = (hint_text or "").strip()
        except Exception as e:
            console.print(
                f"Error generating hint for problem {i}: {e}", style="bold red")
            continue

        # Ensure LaTeX-friendly minimal wrapper
        if not hint_text.lower().startswith("hint"):
            hint_text = f"Hint: {hint_text}"

        out_path = os.path.join("src", "hint", f"problem_{i}.tex")
        with open(out_path, "w") as out:
            out.write(hint_text + "\n")

        console.print(
            f"Hint for problem {i} saved to {out_path}", style="green")
        sys.stdout.flush()

        generated_count += 1

    console.print(
        f"Generated {generated_count} hint file(s) in src/hint/", style="green")
