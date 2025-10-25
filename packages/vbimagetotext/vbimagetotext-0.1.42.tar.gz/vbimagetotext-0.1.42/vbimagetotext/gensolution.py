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
            f"Path must contain an index number, e.g., Problem_1.png: {sample_path}"
        )
    prefix, _, ext = match.groups()
    return dirname, prefix, ext


def _build_responses_input(prompt_text: str, image_b64_list: List[str]):
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
    help="Generate ONLY the LaTeX solution environment for chemistry problems from images across a range, saving to src/solution/problem_{i}.tex"
)
@click.option(
    "-i",
    "--image",
    "image_sample",
    type=click.Path(exists=True),
    required=True,
    help="Path to a sample problem image (e.g., images/Problem_1.png)",
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
    help="Model to use for solution generation",
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
def gensolution(image_sample, problem_range, model, reasoning_effort):
    console = Console()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        console.print(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.",
            style="bold red",
        )
        sys.exit(1)

    image_dir, image_prefix, image_ext = _split_pattern(image_sample)

    os.makedirs(os.path.join("src", "solution"), exist_ok=True)

    client = OpenAI(api_key=api_key)

    start, end = problem_range
    generated_count = 0
    for i in range(start, end + 1):
        image_path = os.path.join(image_dir, f"{image_prefix}{i}{image_ext}")

        if not os.path.exists(image_path):
            console.print(
                f"Skipping missing image: {image_path}", style="yellow")
            continue

        base64_image = encode_image(image_path)

        prompt_text = (
            "You are an expert chemistry tutor. Analyze the attached problem image and produce ONLY the LaTeX solution environment for the chemistry problem depicted. "
            "Do NOT restate the problem. Do NOT include options or any non-solution text.\n\n"
            "CRITICAL OUTPUT CONSTRAINT: Return EXACTLY and ONLY a LaTeX snippet that starts with \\begin{solution} and ends with \\end{solution}. "
            "Use an align* environment inside the solution for step-by-step derivations, one step per line. "
            "Use short explanatory text between lines with \\intertext{...} (wrap any math in $...$). "
            "Wrap every mathematical symbol or expression in inline math $...$. "
            "For chemical equations or species, use mhchem style if appropriate, e.g., \\ce{H2 + O2 -> H2O}. "
            "No preamble, no document environment, no comments, no extra text outside the solution environment."
        )

        input_payload = _build_responses_input(prompt_text, [base64_image])

        try:
            resp = client.responses.create(
                model=model,
                input=input_payload,
                reasoning={"effort": reasoning_effort},
                # response_format={"type": "latex"},
            )

            solution_text = getattr(resp, "output_text", None)
            if not solution_text:
                try:
                    solution_text = resp.output[0].content[0].text
                except Exception:
                    solution_text = ""
            solution_text = (solution_text or "").strip()
        except Exception as e:
            console.print(
                f"Error generating solution for problem {i}: {e}", style="bold red")
            continue

        # Extract solution environment if present; otherwise wrap
        m = re.search(
            r"\\begin{solution}([\s\S]*?)\\end{solution}", solution_text, re.DOTALL)
        if m:
            final_solution = f"\\begin{{solution}}{m.group(1)}\\end{{solution}}"
        else:
            final_solution = f"\\begin{{solution}}\n{solution_text}\n\\end{{solution}}"

        out_path = os.path.join("src", "solution", f"problem_{i}.tex")
        with open(out_path, "w") as out:
            out.write(final_solution + "\n")

        console.print(
            f"Solution for problem {i} saved to {out_path}", style="green")
        sys.stdout.flush()

        generated_count += 1

    console.print(
        f"Generated {generated_count} solution file(s) in src/solution/", style="green")
