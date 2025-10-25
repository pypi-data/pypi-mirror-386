"""Stub for classification stage.

Command: `classify`
"""

import click


@click.command("classify", help="Classify images via o4-mini (stub)")
@click.option("--model", default="o4-mini", show_default=True)
@click.option("--effort", default="low", type=click.Choice(["low", "medium", "high"]))
@click.pass_context
def classify_cmd(ctx: click.Context, model: str, effort: str) -> None:  # noqa: ARG001 - ctx reserved for future use
    """Prints the intended classification action (currently a stub)."""
    click.echo(f"[stub] Would classify with model={model} effort={effort}")

