"""Export a TikZ JSONL bank to JSONL, CSV, or prompt-ready text.

Command: `tikz-export`
"""

from __future__ import annotations

import os
import json
import csv
from pathlib import Path
from typing import Iterable, Dict, Any, List

import click


def _read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _write_csv(rows: Iterable[Dict[str, Any]], out_path: str) -> int:
    # Choose stable, LLM-friendly columns
    cols = ["id", "chapter", "topics", "source_path", "rel_path", "libraries", "packages", "tikz"]
    n = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r2 = dict(r)
            # serialize lists for CSV
            for k in ("topics", "libraries", "packages"):
                v = r2.get(k, [])
                if isinstance(v, list):
                    r2[k] = ", ".join(str(x) for x in v)
            w.writerow({k: r2.get(k, "") for k in cols})
            n += 1
    return n


def _write_prompt(rows: Iterable[Dict[str, Any]], out_path: str) -> int:
    n = 0
    lines: List[str] = []
    lines.append("# TikZ Reference Patterns\n")
    lines.append("# Use only base TikZ, parameterize scalars via \\def, define coordinates, then \\draw.\n")
    lines.append("# Avoid external images and unnecessary libraries.\n\n")
    for r in rows:
        n += 1
        ch = r.get("chapter") or ""
        tps = r.get("topics") or []
        header = f"## Reference {r.get('id')} — {ch} — {', '.join(tps)}".strip()
        lines.append(header + "\n")
        lines.append("```tex\n")
        lines.append(str(r.get("tikz", "")).rstrip() + "\n")
        lines.append("```\n\n")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return n


@click.command("tikz-export", help="Export TikZ bank to JSONL/CSV/prompt text")
@click.option("--in", "in_path", default=None, help="Input JSONL (defaults to workspace/meta/tikz_bank.jsonl)")
@click.option("--to", "format_", type=click.Choice(["jsonl", "csv", "prompt"], case_sensitive=False), default="jsonl", show_default=True)
@click.option("--out", "out_path", required=True, help="Output file path")
@click.option("--limit", default=None, type=int, help="Limit number of records in export")
@click.pass_context
def tikz_export_cmd(ctx: click.Context, in_path: str | None, format_: str, out_path: str, limit: int | None) -> None:
    ws = ctx.obj["workspace"]
    in_path = in_path or os.path.join(ws, "meta", "tikz_bank.jsonl")
    if not os.path.exists(in_path):
        raise click.UsageError(f"Input JSONL not found: {in_path}")

    rows = list(_read_jsonl(in_path))
    if limit is not None:
        rows = rows[:limit]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if format_.lower() == "jsonl":
        with open(out_path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        click.echo(f"Wrote {len(rows)} records to {out_path}")
    elif format_.lower() == "csv":
        n = _write_csv(rows, out_path)
        click.echo(f"Wrote {n} rows to {out_path}")
    else:  # prompt
        n = _write_prompt(rows, out_path)
        click.echo(f"Wrote {n} references to {out_path}")

