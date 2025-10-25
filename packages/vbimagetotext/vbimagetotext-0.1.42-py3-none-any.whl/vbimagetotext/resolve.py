# resolving.py

import click
import os
import subprocess
import base64
from typing import Optional, List, Dict, Union

from openai import OpenAI
import pyperclip
from rich.console import Console

# Assuming prompts.py is in the same directory or package level
try:
    from .prompts import switch_prompt
    # Assuming ChoiceOption is also available
    from .choice_option import ChoiceOption
except ImportError:
    # Fallback for running as a standalone script might require adjustment
    print("Warning: Could not import from local package. Assuming prompts/ChoiceOption are available.")
    # You might need to define a placeholder or adjust imports if not running as part of the package
    def switch_prompt(p): return f"Using prompt key: {p}"  # Placeholder

    class ChoiceOption(click.Option):
        pass  # Placeholder


# --- OpenAI Interaction Logic (Adapted from solution_o4_mini.py) ---

# Load API key from environment variable at the module level
api_key = os.getenv("OPENAI_API_KEY")
console = Console()


def encode_image(image_path: str) -> str:
    """Encodes an image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        console.print(
            f"Error: Image file not found at {image_path}", style="bold red")
        raise
    except Exception as e:
        console.print(
            f"Error encoding image {image_path}: {e}", style="bold red")
        raise


def call_openai_vision(
    prompt_text: str,
    model: str,
    image_paths: Optional[List[str]] = None,
    text_input: Optional[str] = None,
    api_key: str = api_key,
    system_prompt: Optional[str] = None,
) -> Optional[str]:
    """
    Calls the OpenAI API with text, optional images, or just text input.

    Args:
        prompt_text (str): The main instruction prompt text.
        model (str): The OpenAI model to use (e.g., "gpt-4o-mini", "gpt-4o").
        image_paths (Optional[List[str]]): List of paths to image files.
        text_input (Optional[str]): Text input (e.g., from a .tex file).
        api_key (str): OpenAI API key.
        system_prompt (Optional[str]): An optional system prompt.

    Returns:
        Optional[str]: The response content from the model, or None on error.
    """
    if not api_key:
        console.print(
            "Error: API key is missing. Set the OPENAI_API_KEY environment variable.", style="bold red")
        return None

    try:
        client = OpenAI(api_key=api_key)

        # --- Construct the user message content ---
        user_content: List[Dict[str, Union[str, Dict[str, str]]]] = []

        # Add the main instruction prompt part first
        user_content.append({"type": "text", "text": prompt_text})

        # Add text input if provided (e.g., from .tex file)
        if text_input:
            user_content.append(
                {"type": "text", "text": f"\n\n### Input Content:\n{text_input}"})

        # Add image parts if provided
        if image_paths:
            for image_path in image_paths:
                try:
                    base64_image = encode_image(image_path)
                    _, ext = os.path.splitext(image_path)
                    mime_type = f"image/{ext[1:].lower()}" if ext and len(
                        ext) > 1 else "image/png"
                    if mime_type not in ["image/png", "image/jpeg", "image/gif", "image/webp"]:
                        mime_type = "image/png"

                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    })
                except Exception as e:
                    # Error handled in encode_image, but we stop processing here
                    console.print(
                        f"Halting due to error processing image {image_path}", style="bold red")
                    return None  # Indicate failure

        # --- System Prompt ---
        effective_system_prompt = system_prompt or \
            "You are an expert physicist and mathematician. Provide rigorous, clear, step-by-step solutions or analyses based on the prompt and provided context (text/images). Use precise LaTeX formatting where appropriate."

        # --- API Call ---
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": effective_system_prompt},
                {"role": "user", "content": user_content}
            ],
            # max_tokens=4000 # Optional: Adjust as needed
        )

        response_text = response.choices[0].message.content

        pyperclip.copy(response_text or "")  # Copy response to clipboard
        print(f"\n--- Generated Response ({model}) ---")
        console.print(response_text or "[No Content Received]")
        print("-------------------------------------\n")

        return response_text.strip() if response_text else ""

    except Exception as e:
        console.print(
            f"Error calling OpenAI API or processing response with {model}: {e}", style="bold red")
        return None  # Indicate failure


# --- Click Command Logic (Adapted from gptloop.py) ---

@click.command(
    help="Process images or TeX files using OpenAI models and save the response."
)
@click.option(
    "-i",
    "--input-file",  # Renamed for clarity
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to the input image (.png) or TeX (.tex) file",
)
@click.option(
    '-r',
    '--ranges',
    nargs=2,
    default=([1, 1]),
    type=click.Tuple([int, int]),
    show_default=True,
    help="Range of file indices to process (e.g., for base_1.png to base_5.png)",
)
@click.option(
    "-p",
    "--prompt",
    cls=ChoiceOption,
    type=click.Choice(
        [
            "mcq_single_correct_problem_only_solution_with_o3",
            "mcq_single_correct_problem_refine_solution_o3",
            "prompt",
        ],
        case_sensitive=False),
    prompt="Select the prompt type",
    default=2,
    show_default=True,
    help="Prompt key defining the task for the AI model",
)
@click.option(
    "-m",
    "--model",
    cls=ChoiceOption,
    type=click.Choice(
        [
            "o3",
            "o4-mini",
        ],
        case_sensitive=False),
    prompt="Select the model",  # Make model selection interactive
    default=1,
    show_default=True,
    help="OpenAI model to use for processing",
)
@click.option(
    "--out-dir",
    type=click.Path(file_okay=False, writable=True),
    default="./resolved",
    show_default=True,
    help="Directory to save the output files."
)
def resolve(input_file, ranges, prompt, model, out_dir):
    """
    Processes a range of image or TeX files based on the input file pattern,
    using the specified prompt and OpenAI model.
    """
    start_index, end_index = ranges
    if start_index > end_index:
        console.print(
            f"Error: Start range ({start_index}) cannot be greater than end range ({end_index}).", style="bold red")
        return

    # Create output directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)
    console.print(
        f"Output will be saved to: {os.path.abspath(out_dir)}", style="blue")

    dirname = os.path.dirname(input_file)
    filename = os.path.basename(input_file)
    extension = os.path.splitext(filename)[1].lower()
    base_parts = os.path.splitext(filename)[0].split('_')

    # Try to determine the base name (handle cases like 'problem_1' or just 'image')
    base_name = "_".join(base_parts[:-1]) if len(
        base_parts) > 1 and base_parts[-1].isdigit() else os.path.splitext(filename)[0]
    if not base_name:  # Fallback if splitting logic fails
        base_name = "output"
    print(f"Detected base name: '{base_name}', extension: '{extension}'")

    actual_prompt_text = switch_prompt(prompt)
    if not actual_prompt_text:
        console.print(
            f"Error: Could not retrieve prompt text for key '{prompt}'.", style="bold red")
        return

    processed_count = 0
    error_count = 0

    for i in range(start_index, end_index + 1):
        current_file_path = os.path.join(
            dirname, f"{base_name}_{i}{extension}")
        # Always save as .tex? Or base on input? Let's default to .tex
        output_file_path = os.path.join(
            out_dir, f"{base_name}_{i}{extension if extension == '.tex' else '.tex'}")

        console.print(
            f"\nProcessing file {i}: {current_file_path} -> {output_file_path}", style="bold cyan")

        if not os.path.exists(current_file_path):
            console.print(
                f"Warning: Input file not found: {current_file_path}. Skipping.", style="yellow")
            error_count += 1
            continue

        input_text_content = None
        input_image_paths = None

        try:
            # Add other image types if needed (jpg, etc.)
            if extension == ".png":
                input_image_paths = [current_file_path]
            elif extension == ".tex":
                with open(current_file_path, "r", encoding='utf-8') as f:
                    input_text_content = f.read()
            else:
                console.print(
                    f"Error: Unsupported file extension '{extension}' for {current_file_path}. Skipping.", style="red")
                error_count += 1
                continue

            # Call the generalized OpenAI function
            result_text = call_openai_vision(
                prompt_text=actual_prompt_text,
                model=model,
                image_paths=input_image_paths,
                text_input=input_text_content
            )

            if result_text is not None:  # Check if API call was successful
                # Save the result to the output file
                with open(output_file_path, "w", encoding='utf-8') as f_out:
                    f_out.write(result_text)
                console.print(
                    f"Successfully processed and saved: {output_file_path}", style="green")

                # Optional: Display output file content using bat
                try:
                    subprocess.run(['bat', output_file_path],
                                   check=True, capture_output=True)
                except FileNotFoundError:
                    console.print(
                        f"(Info: 'bat' command not found, cannot display {output_file_path})", style="dim")
                except subprocess.CalledProcessError as e:
                    console.print(
                        f"(Warning: 'bat' command failed: {e})", style="yellow")

                processed_count += 1
            else:
                console.print(
                    f"Error processing file {current_file_path}. See previous errors.", style="red")
                error_count += 1

        except Exception as e:
            console.print(
                f"General error processing file {current_file_path}: {e}", style="bold red")
            error_count += 1

    console.print(
        f"\nProcessing Complete. {processed_count} files successfully processed, {error_count} errors.", style="bold blue")


if __name__ == "__main__":
    resolve()
