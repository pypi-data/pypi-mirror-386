"""Agentic commands package.

Each subcommand is defined in its own module and exported here via
`register_commands(group)` which attaches them to the top-level Click group.
"""

from typing import Callable

import click


def register_commands(group: click.Group) -> None:
    """Attach all agentic subcommands to the provided Click group.

    Import is done inside the function to avoid import cycles.
    """
    from .init_db import init_db_cmd
    from .batches import batches_cmd
    from .jobs import jobs_cmd
    from .export import export_cmd
    from .verify import verify_cmd
    from .animations import animations_cmd
    from .ingest import ingest_cmd
    from .classify import classify_cmd
    from .extract import extract_cmd
    from .variants import variants_cmd
    from .run import run_cmd
    from .tikz_extract import tikz_extract_cmd
    from .tikz_export import tikz_export_cmd

    group.add_command(init_db_cmd)
    group.add_command(batches_cmd)
    group.add_command(jobs_cmd)
    group.add_command(export_cmd)
    group.add_command(verify_cmd)
    group.add_command(animations_cmd)
    group.add_command(ingest_cmd)
    group.add_command(classify_cmd)
    group.add_command(extract_cmd)
    group.add_command(variants_cmd)
    group.add_command(run_cmd)
    group.add_command(tikz_extract_cmd)
    group.add_command(tikz_export_cmd)
