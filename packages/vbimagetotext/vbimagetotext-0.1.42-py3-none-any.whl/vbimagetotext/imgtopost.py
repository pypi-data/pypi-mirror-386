import click
import os
import subprocess

from .gptvision import gptvision
from .choice_option import ChoiceOption
from .functions_imgtopost import gen_main_tex


@click.command(
    help="Process images using OpenAI's GPT-4 Vision model and extract the response."
)
@click.option(
    "-i",
    "--image",
    type=click.Path(exists=True),
    required=True,
    help="Path to the image file",
)
@click.option(
    "-r",
    "--ranges",
    nargs=2,
    default=([1, 1]),
    type=click.Tuple([int, int]),
    show_default=True,
    help="Range of pages to extract text from",
)
@click.option(
    "-p",
    "--prompt",
    cls=ChoiceOption,
    type=click.Choice(
        [
            "maths_inequality",
            "prompt",
        ],
        case_sensitive=False),
    prompt=True,
    default=1,
    show_default=True,
    help="Prompt to use for the completion",
)
@click.option(
    "-t",
    "--title",
    type=str,
    default="Inequalities",
    help="Title of the post",
)
@click.pass_context
def imgtopost(ctx, image, ranges, prompt, title):
    for i in range(ranges[0], ranges[1] + 1):
        print(image)
        dirname = os.path.dirname(image)
        filename = os.path.basename(image)
        extension = os.path.splitext(filename)[1]
        basename = filename.split('_')[0]
        image_path = os.path.join(dirname, f"{basename}_{i}{extension}")
        ctx.invoke(gptvision, image=[image_path],
                   prompt=prompt, model="gpt-4o", max_tokens=2000)
        os.makedirs(f"./problems/problem_{i}", exist_ok=True)
        subprocess.run(
            f"pbpaste >> ./problems/problem_{i}/draft.tex", shell=True)
        gen_main_tex(title, i)


if __name__ == "__main__":
    imgtopost()
