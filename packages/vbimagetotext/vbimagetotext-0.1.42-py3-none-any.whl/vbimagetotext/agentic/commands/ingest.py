"""Ingest images into the workspace.

Command: `ingest`
"""

import os
import shutil
import zipfile
from pathlib import Path
import click


@click.command("ingest", help="Ingest images from file/zip/folder into workspace (stub)")
@click.option("-i", "--input", required=True, type=click.Path())
@click.pass_context
def ingest_cmd(ctx: click.Context, input: str) -> None:
    """Copy images from a file, zip, or directory into `ingest/images`."""
    ws = ctx.obj["workspace"]
    img_dir = os.path.join(ws, "ingest", "images")
    os.makedirs(img_dir, exist_ok=True)
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    copied = 0
    click.echo(f"📁 Ingesting from: {input}")
    try:
        if os.path.isdir(input):
            click.echo("  → Scanning directory for images...")
            for p in Path(input).rglob("*"):
                if p.is_file() and p.suffix.lower() in exts:
                    shutil.copy2(str(p), os.path.join(img_dir, p.name))
                    copied += 1
                    if copied <= 5:
                        click.echo(f"    ✓ Copied {p.name}")
                    elif copied == 6:
                        click.echo("    ... (showing first 5 files)")
        elif os.path.isfile(input) and input.lower().endswith(".zip"):
            click.echo("  → Extracting from ZIP archive...")
            with zipfile.ZipFile(input, "r") as zf:
                for name in zf.namelist():
                    if Path(name).suffix.lower() in exts:
                        out_path = os.path.join(img_dir, os.path.basename(name))
                        with zf.open(name) as zf_f, open(out_path, "wb") as out_f:
                            out_f.write(zf_f.read())
                        copied += 1
                        if copied <= 5:
                            click.echo(f"    ✓ Extracted {os.path.basename(name)}")
                        elif copied == 6:
                            click.echo("    ... (showing first 5 files)")
        elif os.path.isfile(input):
            if Path(input).suffix.lower() in exts:
                click.echo("  → Copying single file...")
                shutil.copy2(input, os.path.join(img_dir, os.path.basename(input)))
                copied += 1
                click.echo(f"    ✓ Copied {os.path.basename(input)}")
            else:
                click.echo(f"  ❌ File {input} is not a supported image format")
                return
        else:
            click.echo(f"❌ Unknown input: {input}")
            return
    except Exception as e:
        click.echo(f"❌ Ingest failed: {e}")
        return
    click.echo(f"✅ Ingested {copied} file(s) into {img_dir}")

