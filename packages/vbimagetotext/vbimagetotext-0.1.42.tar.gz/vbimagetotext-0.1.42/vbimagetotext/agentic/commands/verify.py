"""Verify LaTeX snippets compile by wrapping and building with latexmk.

Command: `verify`
"""

import os
import glob
from pathlib import Path
import click

from ..verify_utils import LATEX_TEMPLATE, verify_tex_file


@click.command("verify", help="Compile .tex snippets under a wrapper and report pass/fail")
@click.option("-d", "--dir", "dir_path", default=None, show_default=False, type=click.Path(file_okay=False), help="Directory containing problem_*.tex or variant_*.tex (defaults to workspace/outputs/tex/problems)")
@click.option("--template", type=click.Path(dir_okay=False), help="Custom LaTeX template with %CONTENT% placeholder")
@click.option("--timeout", default=45, show_default=True, type=int)
@click.option("--log-lines", default=20, show_default=True, type=int)
@click.option("--keep-build", is_flag=True, help="Keep build artifacts and PDFs")
@click.option("--variants-only", is_flag=True, help="Only verify variant_*.tex files (ignores problem_*.tex)")
@click.pass_context
def verify_cmd(ctx: click.Context, dir_path: str | None, template: str | None, timeout: int, log_lines: int, keep_build: bool, variants_only: bool) -> None:
    """Build problem or variant TeX files and report pass/fail per file."""
    ws = ctx.obj["workspace"]

    if dir_path is None:
        dir_path = os.path.join(ws, "outputs", "tex", "problems")

    if variants_only:
        variant_files = sorted(glob.glob(os.path.join(dir_path, "variant_*.tex")))
        variant_files.extend(sorted(glob.glob(os.path.join(dir_path, "**/variant_*.tex"), recursive=True)))
        files = variant_files
        if not files:
            click.echo(f"No variant_*.tex found under {dir_path}")
            return
        click.echo(f"Found {len(files)} variant file(s) to verify")
    else:
        problem_files = sorted(glob.glob(os.path.join(dir_path, "problem_*.tex")))
        variant_files = sorted(glob.glob(os.path.join(dir_path, "variant_*.tex")))
        variant_files.extend(sorted(glob.glob(os.path.join(dir_path, "**/variant_*.tex"), recursive=True)))
        files = problem_files + variant_files
        if not files:
            click.echo(f"No problem_*.tex or variant_*.tex found under {dir_path}")
            return
        file_type = "problems" if problem_files and not variant_files else "variants" if variant_files and not problem_files else "problems and variants"
        click.echo(f"Found {len(files)} {file_type} file(s) to verify")

    tpl = Path(template).read_text() if template else LATEX_TEMPLATE

    passed = 0
    failed = 0
    click.echo(f"🔍 Found {len(files)} problem file(s) to verify")
    click.echo(f"📝 Using LaTeX template with custom \\ans and solution commands")
    click.echo(f"⏱️  Timeout: {timeout}s per file")
    click.echo()

    for i, fp in enumerate(files, 1):
        name = Path(fp).stem
        click.echo(f"[{i}/{len(files)}] Verifying {name}.tex...")
        ok, details, workdir = verify_tex_file(ws, fp, timeout=timeout, keep_build=keep_build, template_str=tpl)
        if ok:
            passed += 1
            click.echo("  ✓ PASSED")
        else:
            failed += 1
            click.echo("  ❌ FAILED")
            tail = "\n".join(details.splitlines()[-log_lines:]) if details else ""
            click.echo(f"  📋 Error details:\n{tail}\n{'-'*60}")
        if keep_build:
            click.echo(f"  📁 Build kept at: {workdir}")

    click.echo()
    if failed == 0:
        click.echo(f"✅ Verify summary: {passed} passed, {failed} failed")
        click.echo("🎉 All problems compiled successfully!")
    else:
        click.echo(f"⚠️  Verify summary: {passed} passed, {failed} failed")
        click.echo(f"🔧 {failed} problem(s) need fixing")

    # Per-file build directory paths printed above when --keep-build is set
