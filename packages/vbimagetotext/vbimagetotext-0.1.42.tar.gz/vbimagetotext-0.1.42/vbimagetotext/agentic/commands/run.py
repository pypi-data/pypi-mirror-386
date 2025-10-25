"""End-to-end pipeline runner with integrated verification and retry.

Command: `run`
"""

import os
import time
import uuid
import subprocess
from pathlib import Path
import click

from ..runner import stage_extract_primary, stage_extract_fallback, stage_answers
from ..db import connect
from ..verify_utils import verify_tex_file, LATEX_TEMPLATE


@click.command("run", help="Run extract → verify per file (with retry), then build answers")
@click.option("--resume", is_flag=True, help="Skip already processed images")
@click.option("--timeout", default=45, show_default=True, type=int, help="Verify timeout per file (seconds)")
@click.option("--verify-retries", default=2, show_default=True, type=int, help="Additional extract+verify attempts if verification fails (primary→fallback→primary-high)")
@click.option("--keep-build", is_flag=True, help="Keep per-file verification build artifacts")
@click.pass_context
def run_cmd(ctx: click.Context, resume: bool, timeout: int, verify_retries: int, keep_build: bool) -> None:
    """Extract and verify each image sequentially; retry extraction on verify failure.

    - Primary extraction, then verify each produced problem_*.tex
    - If any verification fails, try fallback extraction and re-verify
    - After processing all images, build an answer key for verified problems
    """
    ws = ctx.obj["workspace"]
    db_path = ctx.obj["db_path"]
    img_root = os.path.join(ws, "ingest", "images")
    patterns = ["*.png", "*.jpg", "*.jpeg"]
    imgs: list[str] = []
    for pat in patterns:
        imgs.extend(str(p) for p in Path(img_root).glob(pat))
    imgs = sorted(imgs)
    if not imgs:
        click.echo("No images ingested. Run: vbimagetotext agent ingest -i <path>")
        return

    # Helper to sort images by numeric index in filename if present
    def _index_of(path: str) -> int:
        b = os.path.basename(path)
        try:
            import re as _re
            m = _re.search(r"(\d+)(?=\.[^.]+$)", b)
        except Exception:
            m = None
        return int(m.group(1)) if m else 1

    imgs = sorted(set(imgs), key=_index_of)

    # Resume: skip images already successfully processed (jobs with status=done for stage extract)
    if resume:
        with connect(db_path) as conn:
            cur = conn.execute("SELECT input_ref FROM jobs WHERE stage = 'extract' AND status = 'done'")
            processed_images = {row[0] for row in cur.fetchall()}
        imgs_f = [img for img in imgs if img not in processed_images]
        if len(imgs_f) < len(imgs):
            click.echo(f"🔄 Resume: skipping {len(imgs) - len(imgs_f)} already processed image(s)")
        imgs = imgs_f

    if not imgs:
        click.echo("✅ All images have already been processed!")
        return

    out_dir = os.path.join(ws, "outputs", "tex", "problems")
    os.makedirs(out_dir, exist_ok=True)

    click.echo(f"🚀 Processing {len(imgs)} image(s) with integrated verification")

    verified_problems: list[str] = []

    for i, image_path in enumerate(imgs, 1):
        idx = _index_of(image_path)
        jid = uuid.uuid4().hex[:12]
        started = int(time.time())
        click.echo(f"[{i}/{len(imgs)}] Extracting from {os.path.basename(image_path)}...")
        problems: list[str] = []
        try:
            # Build attempt plan: primary → fallback → primary(high) … up to verify_retries
            attempt_plan = []
            if verify_retries <= 0:
                attempt_plan = [("primary", "medium")]
            elif verify_retries == 1:
                attempt_plan = [("primary", "medium"), ("fallback", None)]
            else:
                attempt_plan = [("primary", "medium"), ("fallback", None), ("primary", "high")]

            success = False
            def _preview_file(prob_path: str) -> None:
                try:
                    # Use bat with no paging and default style; let it print directly
                    click.echo(f"    📄 Preview of {os.path.basename(prob_path)}:")
                    subprocess.run(["bat", "--paging=never", prob_path], timeout=10, check=False)
                    return
                except Exception:
                    pass
                # Fallback: print entire file raw
                try:
                    content = Path(prob_path).read_text()
                    click.echo(f"    📄 Preview of {os.path.basename(prob_path)}:")
                    click.echo(content)
                except Exception as e:
                    click.echo(f"    ⚠️  Could not preview {prob_path}: {e}")

            for a_idx, (mode, effort_level) in enumerate(attempt_plan, 1):
                if mode == "primary":
                    if effort_level is None:
                        effort_level = "medium"
                    click.echo(f"  → Attempt {a_idx}: primary extraction (effort={effort_level})")
                    res = stage_extract_primary(image_path=image_path, model="o4-mini", effort=effort_level, out_dir=out_dir, index=idx)
                    problems = list(res.get("problems", []))
                else:
                    click.echo(f"  → Attempt {a_idx}: fallback extraction")
                    fb = stage_extract_fallback(image_path=image_path, model="o4-mini", out_dir=out_dir, start_index=idx)
                    problems = [str(p) for p in fb.get("problems", [])]

                # Verify extracted problems
                all_ok = True
                tmp_verified: list[str] = []
                # Show previews before verification
                for p in problems:
                    _preview_file(p)
                for p in problems:
                    ok, details, _ = verify_tex_file(ws, p, timeout=timeout, keep_build=keep_build, template_str=LATEX_TEMPLATE)
                    if ok:
                        tmp_verified.append(p)
                    else:
                        all_ok = False
                        click.echo(f"    ❌ Verify failed for {os.path.basename(p)}")

                if all_ok and problems:
                    for p in tmp_verified:
                        if p not in verified_problems:
                            verified_problems.append(p)
                    success = True
                    break

            if not success:
                raise RuntimeError("verify_failed")

            finished = int(time.time())
            duration_ms = (finished - started) * 1000
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, None, "extract", image_path, "done", 1, started, finished, duration_ms, "o4-mini", None, None, None),
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
            click.echo(f"  ✓ Extracted and verified {len(problems)} problem(s)")
        except Exception as e:  # noqa: BLE001
            finished = int(time.time())
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, None, "extract", image_path, "failed", 1, started, finished, (finished-started)*1000, "o4-mini", None, None, str(e)),
                )
                conn.commit()
            click.echo(f"  ✖ Extraction/verification failed for {os.path.basename(image_path)}")

    if not verified_problems:
        click.echo("No verified problems to answer.")
        return

    click.echo("📋 Generating answer key for verified problems...")
    ans_path = os.path.join(ws, "outputs", "tex", "answer_key.tex")
    _ = stage_answers(verified_problems, ans_path)
    click.echo(f"✅ Pipeline complete! Wrote answers to {ans_path}")
