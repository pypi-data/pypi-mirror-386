"""Extract TikZ diagrams recursively from .tex files into a JSONL bank.

Command: `tikz-extract`
"""

from __future__ import annotations

import os
import re
import json
import uuid
import time
from pathlib import Path
from typing import Iterable, List, Dict, Any

import click


TIKZ_ENV_RE = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", re.DOTALL)
LIB_RE = re.compile(r"\\usetikzlibrary\{([^}]*)\}")
PKG_RE = re.compile(r"\\usepackage\{([^}]*)\}")


def _extract_meta_comments(text: str) -> Dict[str, Any]:
    chapter = None
    topics: List[str] = []
    for line in text.splitlines()[:50]:  # only scan top of file for metadata
        s = line.strip()
        if s.lower().startswith('% chapter:') and chapter is None:
            chapter = s.split(':', 1)[1].strip() or None
        if s.lower().startswith('% topics:') and not topics:
            # crude parse for [a, b]
            if '[' in s and ']' in s:
                inside = s[s.find('[')+1:s.find(']')]
                topics = [t.strip() for t in inside.split(',') if t.strip()]
    return {"chapter": chapter, "topics": topics}


def _scan_libraries(text: str) -> Dict[str, List[str]]:
    libs: List[str] = []
    for m in LIB_RE.finditer(text):
        for item in m.group(1).split(','):
            it = item.strip()
            if it:
                libs.append(it)
    pkgs: List[str] = []
    for m in PKG_RE.finditer(text):
        for item in m.group(1).split(','):
            it = item.strip()
            if it:
                pkgs.append(it)
    # de-duplicate
    def _uniq(xs: Iterable[str]) -> List[str]:
        out: List[str] = []
        seen = set()
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
    return {"libraries": _uniq(libs), "packages": _uniq(pkgs)}


def _iter_tex_files(root: str, pattern: str) -> Iterable[Path]:
    yield from Path(root).rglob(pattern)


@click.command("tikz-extract", help="Recursively extract tikzpicture blocks into a JSONL bank")
@click.option("--root", required=True, type=click.Path(exists=True, file_okay=False), help="Root folder to scan for .tex files")
@click.option("--pattern", default="*.tex", show_default=True, help="Glob pattern to match under --root")
@click.option("--out", "out_path", default=None, help="Output JSONL path (defaults to workspace/meta/tikz_bank.jsonl)")
@click.option("--append", is_flag=True, help="Append to existing output JSONL instead of overwriting")
@click.option("--write-snippets", is_flag=True, help="Also write each snippet to workspace/meta/tikz_bank/snippets/<id>.tex")
@click.pass_context
def tikz_extract_cmd(ctx: click.Context, root: str, pattern: str, out_path: str | None, append: bool, write_snippets: bool) -> None:
    ws = ctx.obj["workspace"]
    bank_dir = os.path.join(ws, "meta", "tikz_bank")
    os.makedirs(bank_dir, exist_ok=True)
    out_path = out_path or os.path.join(ws, "meta", "tikz_bank.jsonl")

    mode = "a" if (append and os.path.exists(out_path)) else "w"
    if mode == "w":
        # start fresh
        open(out_path, "w").close()

    count_files = 0
    count_blocks = 0

    with open(out_path, mode) as out_f:
        for fp in _iter_tex_files(root, pattern):
            if not fp.is_file():
                continue
            try:
                text = fp.read_text(errors="ignore")
            except Exception:
                continue
            metas = _extract_meta_comments(text)
            libs = _scan_libraries(text)
            blocks = list(TIKZ_ENV_RE.finditer(text))
            if not blocks:
                continue
            count_files += 1
            for m in blocks:
                snippet = m.group(0).strip()
                rec = {
                    "id": uuid.uuid4().hex[:12],
                    "source_path": str(fp),
                    "rel_path": os.path.relpath(str(fp), start=root),
                    "chapter": metas.get("chapter"),
                    "topics": metas.get("topics", []),
                    "tikz": snippet,
                    "libraries": libs.get("libraries", []),
                    "packages": libs.get("packages", []),
                    "created_at": int(time.time()),
                }
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count_blocks += 1
                if write_snippets:
                    snip_dir = os.path.join(bank_dir, "snippets")
                    os.makedirs(snip_dir, exist_ok=True)
                    Path(os.path.join(snip_dir, f"{rec['id']}.tex")).write_text(snippet)

    click.echo(f"Scanned {count_files} file(s); extracted {count_blocks} tikzpicture block(s) → {out_path}")

