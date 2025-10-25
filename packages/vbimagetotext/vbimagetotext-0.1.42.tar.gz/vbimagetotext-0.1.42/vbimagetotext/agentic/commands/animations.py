"""Create Manim animation script stubs for problems and record a batch.

Command: `animations`
"""

import os
import time
import glob
import uuid
from pathlib import Path
import click

from ..db import connect


ANIM_TEMPLATE = """
from manim import *

class ProblemAnimation(Scene):
    def construct(self):
        title = Text("{title}", font_size=36).to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # TODO: This is a placeholder. Replace with model-generated animation logic.
        note = Text("Auto-generated stub animation", font_size=28)
        self.play(FadeIn(note))
        self.wait(1)

        # Example vector triangle (as in river-boat problems)
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


def make_anim_script(problem_path: str) -> str:
    """Generate a simple Manim script using the filename as the title."""
    stem = Path(problem_path).stem
    title = stem.replace("_", " ").title()
    return ANIM_TEMPLATE.replace("{title}", title)


@click.command("animations", help="Create Manim animation scripts per problem and record a batch (no API calls yet)")
@click.option("-d", "--dir", "dir_path", default=None, show_default=False, type=click.Path(file_okay=False), help="Directory containing source .tex (defaults to workspace/outputs/tex/problems)")
@click.option("--pattern", default="problem_*.tex", show_default=True, help="Glob pattern to match inside --dir (e.g., problem_*.tex or variant_*.tex)")
@click.option("--batch-name", default=None, help="Optional human-readable batch name")
@click.option("--batch-id", default=None, help="Optional batch id (uuid). Defaults to a random id")
@click.pass_context
def animations_cmd(ctx: click.Context, dir_path: str | None, pattern: str, batch_name: str | None, batch_id: str | None) -> None:
    """Create stub animation .py files for each matching TeX file and log jobs/artifacts."""
    ws = ctx.obj["workspace"]
    db_path = ctx.obj["db_path"]

    if dir_path is None:
        dir_path = os.path.join(ws, "outputs", "tex", "problems")

    files = sorted(glob.glob(os.path.join(dir_path, pattern)))
    if not files:
        click.echo(f"No files matching {pattern} under {dir_path}")
        return

    bid = batch_id or uuid.uuid4().hex[:12]
    bname = batch_name or f"animations_{time.strftime('%Y%m%d_%H%M%S')}"
    now = int(time.time())

    out_root = os.path.join(ws, "animations", bid)
    os.makedirs(out_root, exist_ok=True)

    with connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO batches (id, name, created_at, total_items, completed_items, failed_items, status) VALUES (?,?,?,?,?,?,?)",
            (bid, bname, now, len(files), 0, 0, "running"),
        )
        conn.commit()

    created = 0
    failed = 0

    for fp in files:
        stem = Path(fp).stem
        out_py = os.path.join(out_root, f"{stem}.py")
        jid = uuid.uuid4().hex[:12]
        started = int(time.time())
        try:
            script = make_anim_script(fp)
            Path(out_py).write_text("# Source: " + fp + "\n" + script)
            finished = int(time.time())
            duration_ms = (finished - started) * 1000
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, bid, "animate", fp, "done", 1, started, finished, duration_ms, None, None, None, None),
                )
                size = os.path.getsize(out_py)
                conn.execute(
                    "INSERT OR REPLACE INTO artifacts (id, job_id, kind, path, bytes, checksum, created_at) VALUES (?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex[:12], jid, "animation_py", out_py, size, None, finished),
                )
                conn.commit()
            created += 1
        except Exception as e:
            finished = int(time.time())
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, bid, "animate", fp, "failed", 1, started, finished, (finished-started)*1000, None, None, None, str(e)),
                )
                conn.commit()
            failed += 1

    with connect(db_path) as conn:
        status = "done" if failed == 0 else ("partial" if created else "failed")
        conn.execute(
            "UPDATE batches SET completed_items = ?, failed_items = ?, status = ? WHERE id = ?",
            (created, failed, status, bid),
        )
        conn.commit()

    click.echo(f"Animation batch {bid}: {created} created, {failed} failed")
    click.echo(f"Animations at: {out_root}")

