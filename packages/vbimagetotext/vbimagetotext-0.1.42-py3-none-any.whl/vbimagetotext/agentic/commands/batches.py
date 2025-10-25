"""List batches and their progress.

Command: `batches`
"""

import click

from ..db import connect


@click.command("batches", help="List batches with progress")
@click.pass_context
def batches_cmd(ctx: click.Context) -> None:
    """Show rows from the `batches` table ordered by creation time."""
    db_path = ctx.obj["db_path"]
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT id, name, total_items, completed_items, failed_items, status, created_at FROM batches ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    if not rows:
        click.echo("No batches found.")
        return
    click.echo(f"{'id':<8} {'name':<16} {'done/total':<12} {'failed':<8} {'status':<10} {'created':<20}")
    for r in rows:
        bid, name, total, done, failed, status, created = r
        click.echo(f"{bid[:8]:<8} {str(name)[:16]:<16} {done}/{total:<12} {failed:<8} {status:<10} {created}")

