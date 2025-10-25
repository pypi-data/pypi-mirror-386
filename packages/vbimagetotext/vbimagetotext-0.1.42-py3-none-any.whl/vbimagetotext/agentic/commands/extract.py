"""Extract LaTeX from ingested images using primary/fallback stages.

Command: `extract`
"""

import os
import time
import uuid
import subprocess
from pathlib import Path
import click

from ..db import connect
from ..runner import stage_extract_primary, stage_extract_fallback


@click.command("extract", help="Extract LaTeX via vision model (stub)")
@click.option("--model", default="vision-alias", show_default=True)
@click.option("--resume", is_flag=True, help="Skip images that have already been processed")
@click.pass_context
def extract_cmd(ctx: click.Context, model: str, resume: bool) -> None:
    """Run extraction over images in `ingest/images` and write `problem_*.tex`."""
    ws = ctx.obj["workspace"]
    db_path = ctx.obj["db_path"]

    img_root = os.path.join(ws, "ingest", "images")
    patterns = ["*.png", "*.jpg", "*.jpeg"]
    imgs: list[str] = []
    for pat in patterns:
        imgs.extend(str(p) for p in Path(img_root).glob(pat))
    imgs = sorted(imgs)
    if not imgs:
        click.echo("No images found under ingest/images")
        return

    def _index_of(path: str) -> int:
        b = os.path.basename(path)
        try:
            import re as _re
            m = _re.search(r"(\d+)(?=\.[^.]+$)", b)
        except Exception:
            m = None
        return int(m.group(1)) if m else 1

    imgs = sorted(set(imgs), key=_index_of)

    out_dir = os.path.join(ws, "outputs", "tex", "problems")
    total_problems = 0
    processed = 0

    processed_images = set()
    if resume:
        with connect(db_path) as conn:
            cur = conn.execute("SELECT input_ref FROM jobs WHERE stage = 'extract' AND status = 'done'")
            processed_images = {row[0] for row in cur.fetchall()}
        click.echo(f"🔄 Resume mode: Found {len(processed_images)} already processed images")

    filtered_imgs = [img for img in imgs if not resume or img not in processed_images]
    if resume and len(filtered_imgs) < len(imgs):
        click.echo(f"⏭️  Skipping {len(imgs) - len(filtered_imgs)} already processed images")

    if not filtered_imgs:
        click.echo("✅ All images have already been processed!")
        return

    for i, image_path in enumerate(filtered_imgs, 1):
        idx = _index_of(image_path)
        jid = uuid.uuid4().hex[:12]
        started = int(time.time())
        click.echo(f"[{i}/{len(filtered_imgs)}] Processing {os.path.basename(image_path)}...")
        try:
            click.echo("  → Classifying and extracting LaTeX...")
            res = stage_extract_primary(image_path=image_path, model=model, effort="medium", out_dir=out_dir, index=idx)
            problems: list[str] = res.get("problems", [])  # type: ignore[assignment]
            valid = res.get("valid", {})
            final_meta = res.get("meta", {})
            if not (valid.get("solution") and valid.get("item")):
                click.echo("  → Primary extraction incomplete, trying fallback...")
                fb = stage_extract_fallback(image_path=image_path, model=model, out_dir=out_dir, start_index=idx)
                problems = [str(p) for p in fb.get("problems", [])]

            finished = int(time.time())
            duration_ms = (finished - started) * 1000
            click.echo(f"  ✓ Generated {len(problems)} problem(s) in {duration_ms/1000:.1f}s")

            if final_meta:
                click.echo(
                    f"    🏷️  Classified as: {final_meta.get('type', 'unknown')} | {final_meta.get('subject', 'unknown')} | {final_meta.get('topic', 'unknown')} | {final_meta.get('difficulty', 'unknown')}")
                if final_meta.get('contains_diagram'):
                    click.echo("    📊 Contains diagram: Yes")

            for prob_path in problems:
                try:
                    # Prefer bat with no paging and default style; let it print directly
                    click.echo(f"    📄 Preview of {os.path.basename(prob_path)}:")
                    subprocess.run(["bat", "--paging=never", prob_path], timeout=10, check=False)
                except Exception:
                    try:
                        # Fallback: print entire file raw
                        content = Path(prob_path).read_text()
                        click.echo(content)
                    except Exception as e:  # noqa: BLE001
                        click.echo(f"    ⚠️  Could not preview {prob_path}: {e}")

            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, None, "extract", image_path, "done", 1, started, finished, duration_ms, model, None, None, None),
                )
                for p in problems:
                    try:
                        size = os.path.getsize(p)
                    except OSError:
                        size = None
                    conn.execute(
                        "INSERT OR REPLACE INTO artifacts (id, job_id, kind, path, bytes, checksum, created_at) VALUES (?,?,?,?,?,?,?)",
                        (uuid.uuid4().hex[:12], jid, "problem_tex", p, size, None, finished),
                    )
                conn.commit()
            processed += 1
            total_problems += len(problems)
        except Exception as e:  # noqa: BLE001
            finished = int(time.time())
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, None, "extract", image_path, "failed", 1, started, finished, (finished-started)*1000, model, None, None, str(e)),
                )
                conn.commit()
            click.echo(f"[extract] failed for {image_path}: {e}")

    click.echo(f"Extracted {total_problems} problem(s) from {processed} image(s) to {out_dir}")
