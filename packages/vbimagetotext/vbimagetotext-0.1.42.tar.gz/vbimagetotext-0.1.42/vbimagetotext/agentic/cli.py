"""Agentic CLI: command group and command registration.

This module defines the top-level `agent` Click group and wires in
subcommands implemented under `vbimagetotext.agentic.commands`.
"""

import os
import click

from .db import DEFAULT_WORKSPACE
from .commands import register_commands


@click.group(help="Agentic pipeline commands (self-contained, Responses API oriented).")
@click.option("--workspace", default=DEFAULT_WORKSPACE, show_default=True, help="Workspace directory for state and artifacts")
@click.pass_context
def agent(ctx: click.Context, workspace: str):
    """Top-level Click group for the agentic workflow.

    Stores `workspace` and computed `db_path` in Click context for use by
    all subcommands.
    """
    ctx.ensure_object(dict)
    ctx.obj["workspace"] = workspace
    ctx.obj["db_path"] = os.path.join(workspace, "state.db")


# Register all subcommands from the commands package
register_commands(agent)

