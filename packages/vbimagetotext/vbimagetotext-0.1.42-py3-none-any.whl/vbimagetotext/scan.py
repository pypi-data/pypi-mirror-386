import os
import click
import itertools
import random
import sys
import threading
import time
import subprocess
import platform
from .prompt_kinds import get_prompt_for_type
from .llm.classify import classify_image
from .llm.solve import solve_with_images
from .llm.utils import estimate_cost_inr_from_usage


PROMPT_TYPES = [
    "mcq_sc",
    "mcq_mc",
    "passage",
    "subjective",
    "match",
    "assertion_reason",
]


def run_scan(image_path: str, model: str = "o4-mini", effort: str = "medium") -> tuple[str, dict, dict]:
    """
    Programmatic API to classify an image and solve it to LaTeX.

    Returns a tuple of (latex_snippet, meta, usage_by_stage)
    where meta includes keys like type/subject/topic and usage_by_stage has
    keys 'classify' and 'solve'.
    """
    # Stage 1: classify
    try:
        meta, usage_cls = classify_image(
            image_path, model=model, allowed_types=PROMPT_TYPES)
    except Exception:
        meta, usage_cls = {"type": "mcq_sc"}, {
            "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    ptype = meta.get("type", "mcq_sc")
    try:
        prompt_text = get_prompt_for_type(ptype)
    except Exception:
        prompt_text = get_prompt_for_type("mcq_sc")

    system_prompt = (
        "You are an expert physicist/mathematician. Use precise LaTeX. "
        "For any diagrams, use base TikZ only: define scalar parameters first with \\def, "
        "then \\coordinate, then \\draw elements; keep diagrams minimal."
    )

    # Stage 2: solve
    latex_snippet, usage_solve = solve_with_images(
        prompt_text,
        image_paths=[image_path],
        model=model,
        system_prompt=system_prompt,
        reasoning_effort=effort,
    )

    return latex_snippet, meta, {"classify": usage_cls, "solve": usage_solve}


@click.command(help="Auto-scan an image, classify type, and extract solution without manual prompt selection.")
@click.option("-i", "--image", type=click.Path(exists=True), required=True, help="Path to the image file")
@click.option("-r", "--ranges", nargs=2, default=([1, 1]), type=click.Tuple([int, int]), show_default=True, help="Range of pages to process")
@click.option("-m", "--model", type=click.Choice(["o4-mini", "o3", "gpt-5"], case_sensitive=False), default="o4-mini", show_default=True, help="Model to use")
@click.option("-e", "--effort", type=click.STRING, default="medium", show_default=True)
def scan(image: str, ranges: tuple[int, int], model: str, effort: str):
    # Iterate same as gptloop naming convention: basename_{i}.ext
    if image.endswith(".png") or image.endswith(".jpg") or image.endswith(".jpeg"):
        caffeinate_proc = None
        try:
            # Keep display/system awake on macOS while scan runs
            if platform.system() == "Darwin":
                try:
                    # prevent display and idle sleep
                    caffeinate_proc = subprocess.Popen(["caffeinate", "-di"])
                except Exception:
                    caffeinate_proc = None

            for i in range(ranges[0], ranges[1] + 1):
                dirname = os.path.dirname(image)
                filename = os.path.basename(image)
                extension = os.path.splitext(filename)[1]
                basename = filename.split('_')[0]
                image_path = os.path.join(
                    dirname, f"{basename}_{i}{extension}")
                sp = Spinner(label="Classifying + Solving",
                             quotes=PHYSICS_QUOTES)
                sp.start()
                try:
                    result, meta, usage = run_scan(
                        image_path=image_path, model=model, effort=effort)
                except Exception as e:
                    sp.stop()
                    click.echo(f"[scan] Error on {image_path}: {e}")
                    continue
                finally:
                    sp.stop()
                usage_cls = usage.get(
                    "classify", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
                usage_solve = usage.get(
                    "solve", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
                inr_in_cls, inr_out_cls, inr_tot_cls = estimate_cost_inr_from_usage(
                    model, usage_cls)
                inr_in_sol, inr_out_sol, inr_tot_sol = estimate_cost_inr_from_usage(
                    model, usage_solve)
                click.echo(
                    f"Classify tokens: in={usage_cls.get('input_tokens', 0)}, out={usage_cls.get('output_tokens', 0)}, total={usage_cls.get('total_tokens', 0)} | est. cost ₹{inr_tot_cls:.2f}")
                click.echo(
                    f"Solve tokens: in={usage_solve.get('input_tokens', 0)}, out={usage_solve.get('output_tokens', 0)}, total={usage_solve.get('total_tokens', 0)} | est. cost ₹{inr_tot_sol:.2f}")

                if result:
                    # Prepend rich metadata as TeX comments for traceability
                    meta_lines = [
                        f"% type: {meta.get('type', '')}",
                        f"% subject: {meta.get('subject', '')}",
                        f"% topic: {meta.get('topic', '')}",
                        f"% difficulty: {meta.get('difficulty', '')}",
                        f"% contains_diagram: {meta.get('contains_diagram', False)}",
                        f"% source_image: {image_path}",
                    ]
                    final = ("\n".join(meta_lines) + "\n" + result).strip()
                    out_path = f"./src/src_tex/problem_{i}.tex"
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    with open(out_path, "w") as f:
                        f.write(final)
                    try:
                        # Print without paging and without blocking the next iteration
                        subprocess.Popen(["bat", "--paging=never", out_path])
                    except Exception:
                        pass
                    click.echo(f"Saved: {out_path}")
        finally:
            if caffeinate_proc is not None:
                try:
                    caffeinate_proc.terminate()
                except Exception:
                    pass
    else:
        click.echo("Only image inputs are supported for 'scan' (e.g., .png/.jpg)")


# Spinner and quotes
PHYSICS_QUOTES = [
    "Energy is conserved — especially the energy you save by thinking first.",
    "Assume a frictionless mind; add friction only where needed.",
    "Everything falls — good ideas just reach the ground faster.",
    "Entropy always wins; tidy your derivations before it does.",
    "Vectors have direction — so should your reasoning.",
    "Measure twice, propagate uncertainties once.",
]
MATH_QUOTES = [
    "When in doubt, complete the square (or change the basis).",
    "Differentiate problems; integrate insights.",
    "Definitions are the lemmas of understanding.",
    "Compact arguments, open minds.",
    "Symmetry is a proof you haven’t written yet.",
    "Check the edge cases; that’s where the truth leaks out.",
]

# Extra set for programming-related runs if needed in the future
PROGRAMMING_QUOTES = [
    "Make it work, make it right, make it fast.",
    "Naming is a design decision, not a formality.",
    "Prefer clarity over cleverness.",
    "Fast is fine, but accurate logs are priceless.",
    "Readability is a feature.",
    "Delete code bravely; keep tests kindly.",
]


class Spinner:
    def __init__(self, label: str, quotes: list[str]):
        self.label = label
        self.quotes = quotes
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        def run():
            frames = itertools.cycle(["|", "/", "-", "\\"])
            q = random.choice(self.quotes) if self.quotes else ""
            i = 0
            while not self._stop.is_set():
                frame = next(frames)
                # Clear the entire line, then print fresh content to avoid leftovers from longer previous quotes
                sys.stdout.write("\r\x1b[2K" + f"{frame} {self.label} — {q}")
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1
                if i % 30 == 0 and self.quotes:
                    q = random.choice(self.quotes)
            # Clear line on stop
            sys.stdout.write("\r\x1b[2K\r")
            sys.stdout.flush()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
