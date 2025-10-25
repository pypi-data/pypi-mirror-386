"""Initialize workspace and state database.

Command: `init-db`

Creates the workspace directory structure and initializes the SQLite DB
used for tracking batches, jobs, artifacts, metrics, and events.
"""

import os
import click

from ..db import init_db, ensure_workspace


@click.command("init-db", help="Initialize SQLite state DB and workspace folders")
@click.pass_context
def init_db_cmd(ctx: click.Context) -> None:
    """Create workspace folders and initialize the SQLite database.

    Uses `ctx.obj['workspace']` for the workspace path and writes the DB to
    `ctx.obj['db_path']`.
    """
    ws = ctx.obj["workspace"]
    ensure_workspace(ws)
    dbp = init_db(ctx.obj["db_path"])
    for rel in [
        "ingest/images",
        "meta",
        "outputs/tex/problems",
        "variants",
        "logs",
        "build",
    ]:
        os.makedirs(os.path.join(ws, rel), exist_ok=True)
    click.echo(f"Initialized workspace at {ws}\nDB: {dbp}")

