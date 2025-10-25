import os
import click
import subprocess
from typing import Optional, List

from openai import OpenAI
from rich.console import Console
import base64
import pyperclip

from .prompts import switch_prompt
from .choice_option import ChoiceOption


console = Console()


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _call_gpt5_sketch(prompt_text: str, image_paths: List[str]) -> str:
    client = OpenAI()

    # Build inputs for Responses API
    dev_input = {
        "role": "developer",
        "content": [
            {"type": "input_text",
                "text": "You convert sketches to well-posed LaTeX physics problems."}
        ],
    }

    user_content: List[dict] = [{"type": "input_text", "text": prompt_text}]
    for p in image_paths:
        b64 = _encode_image(p)
        ext = os.path.splitext(p)[1].lower().lstrip(".") or "png"
        if ext not in ["png", "jpg", "jpeg", "gif", "webp"]:
            ext = "png"
        user_content.append({
            "type": "input_image",
            "image_url": f"data:image/{ext};base64,{b64}",
        })

    user_input = {"role": "user", "content": user_content}

    resp = client.responses.create(
        model="gpt-5",
        input=[dev_input, user_input],
        text={
            "format": {"type": "text"},
            "verbosity": "medium",
        },
        reasoning={"effort": "medium", "summary": "auto"},
        tools=[],
        store=True,
    )

    return resp.output[1].content[0].text


@click.command(help="Turn sketch images (main_*.jpeg) into a LaTeX problem using gpt-5.")
@click.option(
    "-i",
    "--input-image",
    type=click.Path(exists=True),
    required=True,
    help="Path to the first image in the sequence (e.g., main_1.jpeg)",
)
@click.option(
    "-r",
    "--ranges",
    nargs=2,
    default=([1, 1]),
    type=click.Tuple([int, int]),
    show_default=True,
    help="Range to process for main_{i}.jpeg",
)
@click.option(
    "-p",
    "--prompt",
    cls=ChoiceOption,
    type=click.Choice([
        "sketch_to_problem_simple_gpt_5",
        "sketch_to_math_problem_gpt_5",
        "sketch_to_math_mcq_gpt_5",
        "sketch_to_math_subjective_gpt_5",
        "prompt",
    ], case_sensitive=False),
    prompt=True,
    default=1,
    show_default=True,
    help="Prompt to use for sketch to LaTeX problem",
)
def sketchtotex(input_image: str, ranges, prompt: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("OPENAI_API_KEY not set", style="bold red")
        return

    if prompt == "prompt":
        prompt = click.prompt("Enter a custom instruction", type=str)
    else:
        prompt = switch_prompt(prompt)

    start, end = ranges
    for i in range(start, end + 1):
        dirname = os.path.dirname(input_image)
        filename = os.path.basename(input_image)
        extension = os.path.splitext(filename)[1]
        basename = filename.split('_')[0]
        image_path = os.path.join(dirname, f"{basename}_{i}{extension}")

        if not os.path.exists(image_path):
            console.print(f"Missing image: {image_path}", style="yellow")
            continue

        try:
            result = _call_gpt5_sketch(prompt, [image_path])
        except Exception as e:
            console.print(f"Error from gpt-5: {e}", style="bold red")
            continue

        # Clipboard + save file
        pyperclip.copy(result)
        out_dir = "./src/src_tex_sketch"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"problem_{i}.tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)

        try:
            subprocess.run(f'bat "{out_path}"', shell=True)
        except Exception:
            pass


if __name__ == "__main__":
    sketchtotex()
