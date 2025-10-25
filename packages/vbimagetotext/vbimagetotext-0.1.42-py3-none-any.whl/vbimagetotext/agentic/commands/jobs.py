"""List jobs with optional filters.

Command: `jobs`
"""

import click

from ..db import connect


@click.command("jobs", help="List jobs; filter by batch/stage")
@click.option("--batch")
@click.option("--stage", type=click.Choice(["ingest", "classify", "extract", "variants", "qa", "verify", "animate"], case_sensitive=False))
@click.option("--limit", default=50, show_default=True, type=int)
@click.pass_context
def jobs_cmd(ctx: click.Context, batch: str | None, stage: str | None, limit: int) -> None:
    """Show rows from the `jobs` table with optional filters."""
    db_path = ctx.obj["db_path"]
    q = "SELECT id, batch_id, stage, status, attempts, model, started_at, finished_at, duration_ms FROM jobs"
    clauses = []
    params: list = []
    if batch:
        clauses.append("batch_id = ?")
        params.append(batch)
    if stage:
        clauses.append("stage = ?")
        params.append(stage)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    with connect(db_path) as conn:
        rows = conn.execute(q, params).fetchall()
    if not rows:
        click.echo("No jobs found.")
        return
    click.echo(f"{'id':<8} {'batch':<8} {'stage':<9} {'status':<9} {'att':<4} {'model':<10} {'start':<12} {'finish':<12} {'ms':<6}")
    for r in rows:
        jid, bid, stg, status, att, model, st, fin, ms = r
        click.echo(f"{jid[:8]:<8} {str(bid)[:8]:<8} {stg:<9} {status:<9} {att:<4} {str(model)[:10]:<10} {st or '-':<12} {fin or '-':<12} {ms or '-':<6}")

