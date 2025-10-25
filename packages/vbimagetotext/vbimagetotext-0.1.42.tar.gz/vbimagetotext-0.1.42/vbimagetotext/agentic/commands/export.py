"""Export artifacts to a zip archive.

Command: `export`
"""

import os
import zipfile
from pathlib import Path
import click


@click.command("export", help="Zip selected outputs for a batch or directory")
@click.option("--batch", help="Batch id to export (optional)")
@click.option("-d", "--dir", "dir_path", type=click.Path(file_okay=False), help="Export from this directory instead of batch artifacts")
@click.option("--kind", type=click.Choice(["variants", "animations"], case_sensitive=False), default="variants", show_default=True, help="When exporting by --batch, choose which outputs to include")
@click.option("-o", "--output", required=True, help="Output zip path")
@click.pass_context
def export_cmd(ctx: click.Context, batch: str | None, dir_path: str | None, kind: str, output: str) -> None:
    """Create a zip containing artifacts from a directory or batch folder."""
    ws = ctx.obj["workspace"]
    targets: list[str] = []
    if dir_path:
        targets = sorted([str(p) for p in Path(dir_path).rglob("*.tex")])
    elif batch:
        base = os.path.join(ws, "variants" if kind == "variants" else "animations", batch)
        if not os.path.isdir(base):
            click.echo(f"No such batch directory: {base}")
            return
        glob_pat = "*.tex" if kind == "variants" else "*.py"
        targets = sorted(str(p) for p in Path(base).rglob(glob_pat))
    else:
        raise click.UsageError("Provide --batch or --dir")

    if not targets:
        click.echo("Nothing to export.")
        return

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    common_prefix = os.path.commonpath([os.path.dirname(targets[0])] + [os.path.dirname(p) for p in targets])
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in targets:
            arc = os.path.relpath(p, start=common_prefix)
            zf.write(p, arcname=arc)
    click.echo(f"Wrote {output} with {len(targets)} files")

