import click
import os
import subprocess
import sys
import re
import json
from typing import List

from PIL import Image
import requests
from rich.console import Console

from .choice_option import ChoiceOption
from .functions import encode_image


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
    '-r',
    '--ranges',
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
            "prompt",
        ],
        case_sensitive=False),
    prompt=True,
    default=1,
    show_default=True,
    help="Prompt to use for the completion",
)
@click.option(
    "-m",
    "--model",
    cls=ChoiceOption,
    type=click.Choice(
        [
            "gpt-4.1",
            "gpt-4.1-mini",
            "o4-mini",
            "o3",
        ],
        case_sensitive=False),
    prompt=True,
    default=4,
    show_default=True,
    help="Prompt to use for the completion",
)
def crop(image, ranges, prompt, model):
    """
    Process images using OpenAI's GPT-4 Vision model and extract the response.
    """
    console = Console()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        console.print(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.", style="bold red")
        sys.exit(1)

    # Ask the user for a custom prompt if they selected the placeholder "prompt" option.
    if prompt == "prompt":
        prompt_text = click.prompt(
            "Enter the prompt you would like to send to the vision model (leave blank for default)", default="")
        if prompt_text.strip():
            prompt = prompt_text
        else:
            prompt = (
                "You are an OCR cropping assistant. The provided image contains several problems laid out vertically. "
                "Return *only* a JSON array of pixel Y-coordinates (integers) indicating the top edge of each problem, "
                "in ascending order from top to bottom. Use the original resolution of the image. "
                "Do not return any explanations, keys, or markdown fences – the output must be raw JSON, e.g.  [0, 235, 912, 1430]."
            )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Helper to send one image to the model and get bounding boxes
    def get_bounding_boxes(image_path: str) -> List[List[int]]:
        base64_image = encode_image(image_path)

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        },
                    ],
                }
            ],
            # "max_tokens": 500,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            console.print(
                f"Error: API request failed with status code {response.status_code}.", style="bold red")
            sys.exit(1)

        message_content = response.json(
        )["choices"][0]["message"]["content"].strip()

        # Attempt to extract the first JSON array found in the response
        match = re.search(r"\[[\s\S]*\]", message_content)
        if not match:
            console.print(
                "Failed to parse bounding boxes from the model response:", style="bold red")
            console.print(message_content)
            sys.exit(1)

        try:
            boxes = json.loads(match.group(0))
            print(boxes)
        except json.JSONDecodeError as e:
            console.print(f"JSON decode error: {e}", style="bold red")
            console.print(message_content)
            sys.exit(1)

        # The model might return:
        #  A) list of y-coords  -> [y1, y2, ...]
        #  B) list of 4-tuples -> conventional bounding boxes / width-height boxes.

        # Case A detection – first element is a number not a list/dict
        if boxes and isinstance(boxes[0], (int, float)):
            return [float(v) for v in boxes]  # plain y

        norm_boxes: list = []
        for item in boxes:
            if isinstance(item, dict):
                bbox = item.get("bbox") or item.get(
                    "box") or item.get("coordinates")
            else:
                bbox = item

            if not (isinstance(bbox, list) and len(bbox) == 4):
                console.print(
                    "Unexpected bbox/y format returned by model.", style="bold red")
                console.print(boxes)
                sys.exit(1)

            # Convert potential [x, y, width, height] -> [x1, y1, x2, y2]
            x1, y1, v3, v4 = [float(v) for v in bbox]

            # We'll disambiguate later when we have image dims
            norm_boxes.append([x1, y1, v3, v4])
        return norm_boxes

    # ---------------- Processing loop ---------------- #
    start_page, end_page = ranges
    problem_counter = 1

    for page_number in range(start_page, end_page + 1):
        # Infer page-specific image path (mirroring logic used in imgtopost)
        dirname = os.path.dirname(image)
        filename = os.path.basename(image)
        base, ext = os.path.splitext(filename)

        if "_" in base:
            base_prefix = base.split("_")[0]
            image_path = os.path.join(
                dirname, f"{base_prefix}_{page_number}{ext}")
        else:
            # If the input image itself is the only file, ignore range indexing
            if page_number == start_page:
                image_path = image
            else:
                console.print(
                    f"Cannot construct filename for page {page_number}.", style="bold yellow")
                continue

        if not os.path.exists(image_path):
            console.print(
                f"Image file {image_path} does not exist.", style="bold red")
            continue

        console.print(
            f"Processing {image_path} with model {model}…", style="cyan")

        bboxes = get_bounding_boxes(image_path)

        img = Image.open(image_path)
        # If returned list is just y-coords, switch to vertical-slice mode
        if bboxes and isinstance(bboxes[0], (int, float)):
            ys = sorted([max(0, min(y, img.height)) for y in bboxes])
            ys.append(img.height)  # bottom sentinel

            for idx in range(len(ys) - 1):
                top_px = int(ys[idx])
                bot_px = int(ys[idx + 1])
                if bot_px - top_px < 20:  # ignore tiny
                    continue
                cropped = img.crop((0, top_px, img.width, bot_px))
                output_name = f"problem_{problem_counter}.png"
                cropped.save(output_name)
                console.print(f"Saved {output_name}", style="green")
                problem_counter += 1
            continue  # proceed to next page

        # Otherwise proceed with bbox logic
        # Crop and save each problem (accounting for potential scaling)
        # Determine scaling factors between model-coordinates and original image
        max_x2 = max(b[2] for b in bboxes)
        max_y2 = max(b[3] for b in bboxes)

        # Protect against division by zero / malformed boxes
        if max_x2 == 0 or max_y2 == 0:
            console.print(
                "Invalid bounding boxes returned (max coordinate is 0). Skipping page.", style="bold red")
            continue

        scale_x = img.width / max_x2
        scale_y = img.height / max_y2

        for bbox in bboxes:
            x1, y1, v3, v4 = bbox

            # Interpret bounding-box format:
            # Case A: coordinates already (x1,y1,x2,y2)          – v3> x1 and v4>y1 and v3<=img.width
            # Case B: (x1,y1,width,height) pixels                – x1+v3 <= img.width + tolerance
            # Case C: coordinates normalised (0–1)               – max(x1,y1,v3,v4) <=1

            tolerance = 5  # pixels

            if max(x1, y1, v3, v4) <= 1.0:  # Normalised [0,1]
                x2 = v3 * img.width
                y2 = v4 * img.height
                x1 = x1 * img.width
                y1 = y1 * img.height
            else:
                # Decide between width/height vs x2/y2
                width_mode = (x1 + v3 <= img.width +
                              tolerance) and (y1 + v4 <= img.height + tolerance)
                if width_mode:
                    x2 = x1 + v3
                    y2 = y1 + v4
                else:
                    x2 = v3
                    y2 = v4

            # After deciding, ensure ints for scaling
            x1, y1, x2, y2 = [float(x1), float(y1), float(x2), float(y2)]

            # Clamp coordinates to image bounds
            nx1 = max(0, min(int(x1 * scale_x), img.width))
            ny1 = max(0, min(int(y1 * scale_y), img.height))
            nx2 = max(0, min(int(x2 * scale_x), img.width))
            ny2 = max(0, min(int(y2 * scale_y), img.height))

            if nx2 <= nx1 or ny2 <= ny1:
                console.print(
                    "Skipped a malformed bbox after scaling.", style="bold yellow")
                continue

            cropped = img.crop((nx1, ny1, nx2, ny2))
            output_name = f"problem_{problem_counter}.png"
            cropped.save(output_name)
            console.print(f"Saved {output_name}", style="green")
            problem_counter += 1

    console.print("✅ Cropping finished.", style="bold green")
