import os
import time
import uuid
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from ..imagestolatex import transcribe_to_latex
from ..extractanswer import extract_answer_letters_from_content


def ensure_dirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def validate_problem_snippet(tex: str) -> Dict[str, bool]:
    has_item = "\\item" in tex
    has_tasks = "\\begin{tasks}" in tex and "\\task" in tex
    has_solution = "\\begin{solution}" in tex and "\\end{solution}" in tex
    return {"item": has_item, "tasks": has_tasks, "solution": has_solution}


def stage_extract_primary(image_path: str, model: str, effort: str, out_dir: str, index: int = 1) -> Dict[str, object]:
    # Lazy import to avoid circular import during CLI registration
    from ..scan import run_scan
    tex, meta, usage = run_scan(
        image_path=image_path, model=model, effort=effort)
    valid = validate_problem_snippet(tex)
    out_path = os.path.join(out_dir, f"problem_{index}.tex")
    ensure_dirs(out_dir)

    # Format metadata as LaTeX comments
    meta_header = ""
    if meta:
        # If classifier provided chapter/topics, add normalized comment lines first
        ch = meta.get("chapter") if isinstance(meta, dict) else None
        tps = meta.get("topics") if isinstance(meta, dict) else None
        try:
            if ch:
                if isinstance(tps, list):
                    tlist = ", ".join(str(x) for x in tps)
                elif isinstance(tps, str):
                    tlist = tps
                else:
                    tlist = ""
                meta_header += f"% chapter: {ch}\n"
                meta_header += f"% topics: [{tlist}]\n"
        except Exception:
            pass
        meta_header += f"% Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        meta_header += f"% Source image: {os.path.basename(image_path)}\n"
        # Avoid repeating chapter/topics metadata lines; they are normalized above
        skip_keys = {"chapter", "topics", "topic"}
        for key, value in meta.items():
            if key in skip_keys:
                continue
            # Format key for display (e.g., 'contains_diagram' -> 'Contains Diagram')
            display_key = key.replace('_', ' ').title()
            meta_header += f"% {display_key}: {value}\n"
        meta_header += "\n"

    # Prepend header and write to file
    Path(out_path).write_text(meta_header + tex)

    return {"problems": [out_path], "meta": meta, "usage": usage, "valid": valid}


def stage_extract_fallback(image_path: str, model: str, out_dir: str, start_index: int = 1) -> Dict[str, object]:
    tmp_dir = os.path.join(out_dir, f".tmp_{uuid.uuid4().hex[:8]}")
    ensure_dirs(tmp_dir)
    res = transcribe_to_latex(image_path=image_path,
                              model=model, output_dir=tmp_dir)
    written = [str(p) for p in res.get("problems", [])]
    problems: List[str] = []
    validations: List[Dict[str, bool]] = []
    try:
        for offset, src in enumerate(written, start=0):
            dst = os.path.join(out_dir, f"problem_{start_index + offset}.tex")
            content = Path(src).read_text()
            Path(dst).write_text(content)
            problems.append(dst)
            validations.append(validate_problem_snippet(content))
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass
    return {"problems": problems, "combined": res.get("combined_path"), "validations": validations}


def stage_answers(problem_paths: List[str], answer_key_path: str) -> List[str]:
    ensure_dirs(os.path.dirname(answer_key_path) or ".")
    answers: List[str] = []
    for fp in problem_paths:
        content = Path(fp).read_text()
        answers.append(extract_answer_letters_from_content(content))
    with open(answer_key_path, "w") as out:
        out.write("\\begin{multicols}{5}\n")
        out.write("    \\begin{enumerate}\n")
        for ans in answers:
            out.write(f"        \\item {ans}\n")
        out.write("    \\end{enumerate}\n")
        out.write("\\end{multicols}\n")
    return answers
