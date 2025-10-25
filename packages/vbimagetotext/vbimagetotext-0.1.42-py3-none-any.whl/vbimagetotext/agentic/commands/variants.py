"""Generate variants for each problem TeX file using an LLM.

Command: `variants`
"""

import os
import time
import glob
import uuid
from pathlib import Path
import click

from ..db import connect
from ..curriculum import format_for_prompt, validate_selection, topics_for
from ..verify_utils import verify_tex_file, LATEX_TEMPLATE
from ...llm.solve import solve_with_images


@click.command("variants", help="Generate N variants per problem using LLM")
@click.option("--model", default="gpt-5", show_default=True, help="Model to use for variant generation")
@click.option("--effort", default="high", type=click.Choice(["low", "medium", "high"]), show_default=True, help="Reasoning effort for variant generation")
@click.option("--per-problem", default=3, show_default=True, type=int, help="Number of variants to create per problem")
@click.option("--verify-timeout", default=45, show_default=True, type=int, help="Verification timeout (seconds)")
@click.option("--verify-retries", default=1, show_default=True, type=int, help="Number of regeneration attempts if a variant fails verification")
@click.option("-d", "--dir", "dir_path", default=None, show_default=False, type=click.Path(file_okay=False), help="Directory containing problem_*.tex (defaults to workspace/outputs/tex/problems)")
@click.option("--resume", is_flag=True, help="Skip problems that have already been processed")
@click.option("--batch-name", default=None, help="Optional human-readable batch name")
@click.option("--batch-id", default=None, help="Optional batch id (uuid). Defaults to a random id")
@click.pass_context
def variants_cmd(ctx: click.Context, model: str, effort: str, per_problem: int, dir_path: str | None, resume: bool, batch_name: str | None, batch_id: str | None, verify_timeout: int, verify_retries: int) -> None:
    """Create `variant_*.tex` files for each `problem_*.tex` and record jobs/artifacts."""
    ws = ctx.obj["workspace"]
    db_path = ctx.obj["db_path"]

    if dir_path is None:
        dir_path = os.path.join(ws, "outputs", "tex", "problems")

    files = sorted(glob.glob(os.path.join(dir_path, "problem_*.tex")))
    if not files:
        click.echo(f"No problem_*.tex found under {dir_path}")
        return

    if resume:
        with connect(db_path) as conn:
            cur = conn.execute(
                """
                SELECT DISTINCT j.input_ref
                FROM jobs j
                JOIN artifacts a ON j.id = a.job_id
                WHERE j.stage = 'variants' AND a.kind = 'variant_tex'
                """
            )
            processed_files = {row[0] for row in cur.fetchall()}
        original_count = len(files)
        files = [f for f in files if f not in processed_files]
        skipped_count = original_count - len(files)
        if skipped_count > 0:
            click.echo(
                f"🔄 Resume mode: Found and skipped {skipped_count} already processed problem(s)")

    if not files:
        click.echo("✅ All problems have already been processed!")
        return

    bid = batch_id or uuid.uuid4().hex[:12]
    bname = batch_name or f"variants_{time.strftime('%Y%m%d_%H%M%S')}"
    now = int(time.time())

    out_root = os.path.join(ws, "variants", bid)
    os.makedirs(out_root, exist_ok=True)

    with connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO batches (id, name, created_at, total_items, completed_items, failed_items, status) VALUES (?,?,?,?,?,?,?)",
            (bid, bname, now, len(files), 0, 0, "running"),
        )
        conn.commit()

    created = 0
    failed = 0
    click.echo(
        f"🎯 Generating {per_problem} variants per problem using {model} with {effort} effort")
    click.echo(f"📁 Found {len(files)} problem file(s) to process")
    click.echo()

    for i, fp in enumerate(files, 1):
        problem_name = Path(fp).stem
        problem_dir = os.path.join(out_root, problem_name)
        os.makedirs(problem_dir, exist_ok=True)

        full_content = Path(fp).read_text()
        lines = full_content.split('\n')
        metadata_lines = [
            line for line in lines if line.strip().startswith('%')]
        snippet_lines = [
            line for line in lines if not line.strip().startswith('%')]
        # Remove any pre-existing chapter/topics lines to avoid repetition
        def _keep_meta(line: str) -> bool:
            s = line.strip().lower()
            return not (s.startswith('% chapter:') or s.startswith('% topics:') or s.startswith('% topic:'))

        metadata_header = "\n".join([ln for ln in metadata_lines if _keep_meta(ln)])
        snippet = "\n".join(snippet_lines).strip()

        click.echo(f"[{i}/{len(files)}] Processing {problem_name}...")
        jid = uuid.uuid4().hex[:12]
        started = int(time.time())

        try:
            variants_created = 0
            for k in range(1, per_problem + 1):
                click.echo(f"  → Generating variant {k}/{per_problem}...")
                try:
                    curriculum_text = format_for_prompt()
                    def _gen_variant() -> str:
                        return solve_with_images(
                            images=[],
                            prompt=f"""
You are an expert {problem_name.replace('_', ' ')} 
physics tutor.

Task:
- Generate 1 variant of the following LaTeX problem, keeping style and difficulty comparable.
- Choose exactly 1 chapter from the allowed list below and 1–3 topics that belong to that chapter.
- At the very top of your response, include metadata comment lines:
  % chapter: <Chapter>
  % topics: [topic1, topic2]
- Then output only the LaTeX snippet (no extra prose) using the same environments, including a clear solution and preserving any \ans calls.

Allowed chapters and topics:
{curriculum_text}

Original snippet:
\n{snippet}\n
""",
                            system_prompt="You are a helpful, detail-oriented math/physics tutor. Generate high-quality problem variants that respect the given chapter/topic list.",
                            reasoning_effort=effort,
                        )
                    variant_content = _gen_variant()

                    if variant_content.strip():
                        # Attempt to parse chapter/topics metadata from the model output
                        chosen_chapter = None
                        chosen_topics: list[str] = []
                        for line in variant_content.splitlines()[:5]:
                            s = line.strip()
                            if s.lower().startswith('% chapter:'):
                                chosen_chapter = s.split(':', 1)[1].strip()
                            if s.lower().startswith('% topics:') and '[' in s and ']' in s:
                                inside = s[s.find('[')+1:s.find(']')]
                                chosen_topics = [t.strip() for t in inside.split(',') if t.strip()]

                        is_valid, missing = (False, [])
                        if chosen_chapter:
                            is_valid, missing = validate_selection(chosen_chapter, chosen_topics or [])

                        # Fallback: inherit chapter/topics from original metadata if available
                        if not is_valid:
                            for line in metadata_lines:
                                low = line.lower()
                                if low.startswith('% chapter:'):
                                    chosen_chapter = line.split(':', 1)[1].strip()
                                if low.startswith('% topics:') and '[' in line and ']' in line:
                                    inside = line[line.find('[')+1:line.find(']')]
                                    chosen_topics = [t.strip() for t in inside.split(',') if t.strip()]
                            if chosen_chapter and not chosen_topics:
                                # Pick 1 topic from chapter list as a minimal default
                                tlist = topics_for(chosen_chapter)
                                if tlist:
                                    chosen_topics = [tlist[0]]

                        variant_path = os.path.join(
                            problem_dir, f"variant_{k}.tex")
                        new_header = f"""{metadata_header}
%
% Variant {k} of {problem_name} generated at {time.strftime('%Y-%m-%d %H:%M:%S')}
% Generated using {model} with {effort} effort
"""
                        # Normalize chapter/topics metadata at the top
                        if chosen_chapter:
                            new_header = (f"% chapter: {chosen_chapter}\n% topics: [{', '.join(chosen_topics)}]\n" + new_header)
                        if not new_header.endswith('\n\n'):
                            new_header += '\n'
                        Path(variant_path).write_text(new_header + variant_content.strip())

                        # Verify the created variant; retry up to verify_retries times if it fails
                        ok, details, _ = verify_tex_file(ws, variant_path, timeout=verify_timeout, keep_build=False, template_str=LATEX_TEMPLATE)
                        retries = 0
                        while not ok and retries < verify_retries:
                            retries += 1
                            click.echo(f"    ↻ Verify failed; regenerating (attempt {retries}/{verify_retries})...")
                            variant_content_retry = _gen_variant()
                            if not variant_content_retry.strip():
                                click.echo("    ✖ Empty retry response; skipping record")
                                break
                            Path(variant_path).write_text(new_header + variant_content_retry.strip())
                            ok, details, _ = verify_tex_file(ws, variant_path, timeout=verify_timeout, keep_build=False, template_str=LATEX_TEMPLATE)
                        if not ok:
                            click.echo("    ✖ Variant still fails verification; skipping record")
                            continue

                        variants_created += 1
                        click.echo(f"    ✓ Created variant_{k}.tex (verified)")
                    else:
                        click.echo(f"    ⚠️  Empty response for variant {k}")
                except Exception as e:  # noqa: BLE001
                    click.echo(f"    ❌ Failed to generate variant {k}: {e}")
                    continue

            finished = int(time.time())
            duration_ms = (finished - started) * 1000
            click.echo(
                f"  ✓ Generated {variants_created}/{per_problem} variants in {duration_ms/1000:.1f}s")

            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, bid, "variants", fp, "done", 1, started,
                     finished, duration_ms, model, None, None, None),
                )
                for k in range(1, variants_created + 1):
                    variant_path = os.path.join(
                        problem_dir, f"variant_{k}.tex")
                    try:
                        size = os.path.getsize(variant_path)
                    except OSError:
                        size = None
                    conn.execute(
                        "INSERT OR REPLACE INTO artifacts (id, job_id, kind, path, bytes, checksum, created_at) VALUES (?,?,?,?,?,?,?)",
                        (uuid.uuid4().hex[:12], jid, "variant_tex",
                         variant_path, size, None, finished),
                    )
                conn.commit()
            created += 1
        except Exception as e:  # noqa: BLE001
            finished = int(time.time())
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (id, batch_id, stage, input_ref, status, attempts, started_at, finished_at, duration_ms, model, prompt_version, seed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (jid, bid, "variants", fp, "failed", 1, started, finished,
                     (finished-started)*1000, model, None, None, str(e)),
                )
                conn.commit()
            failed += 1

    with connect(db_path) as conn:
        status = "done" if failed == 0 else (
            "partial" if created else "failed")
        conn.execute(
            "UPDATE batches SET completed_items = ?, failed_items = ?, status = ? WHERE id = ?",
            (created, failed, status, bid),
        )
        conn.commit()

    click.echo(
        f"Batch {bid} created: {created} problems processed, {failed} failed")
    click.echo(f"Variants at: {out_root}")
