"""Utilities for verifying LaTeX snippets by compiling with latexmk.

Exposes:
- `LATEX_TEMPLATE`: default wrapper template with %CONTENT% placeholder.
- `wrap_snippet(snippet, template)`: injects content into the template.
- `verify_tex_file(workspace, file_path, timeout=45, keep_build=False, template_str=None)`
   Compiles a single TeX snippet file by wrapping it and running latexmk.
   Returns (passed: bool, details: str, workdir: str)
"""

from __future__ import annotations

import os
import time
import subprocess
from pathlib import Path
from typing import Tuple


LATEX_TEMPLATE = r"""\documentclass[preview,border=5mm, 10pt]{standalone}
\usepackage{amsmath,amssymb,siunitx,physics,tasks,enumitem}
\usepackage{tikz}
\usepackage{xcolor}
\usetikzlibrary{optics}
\usepackage[utopia]{mathdesign}
% Custom commands for answer marking and solutions
\newcommand{\ans}{\textcolor{red!95}{\textit{\quad Ans.}}}
\newenvironment{solution}{\color{red!85!black}$\Rightarrow$}{}
% Optional: custom package if your snippets depend on it
% \usepackage{v-test-paper}
\begin{document}
\begin{enumerate}[leftmargin=*,label=\arabic*.]
%CONTENT%
\end{enumerate}
\end{document}
"""


def wrap_snippet(snippet: str, template: str = LATEX_TEMPLATE) -> str:
    return template.replace("%CONTENT%", snippet.strip())


def verify_tex_file(
    workspace: str,
    file_path: str,
    timeout: int = 45,
    keep_build: bool = False,
    template_str: str | None = None,
) -> Tuple[bool, str, str]:
    """Compile a single TeX snippet file; return (passed, details, workdir).

    - Creates a temporary build dir under `<workspace>/build/verify_<ts>/<stem>`.
    - Wraps the snippet using `template_str` or default `LATEX_TEMPLATE`.
    - On success, returns (True, "", workdir). If `keep_build` is False, cleans aux.
    - On failure/timeout, returns (False, tail_or_error, workdir).
    """
    tpl = template_str or LATEX_TEMPLATE
    build_root = os.path.join(workspace, "build", f"verify_{int(time.time())}")
    name = Path(file_path).stem
    workdir = os.path.join(build_root, name)
    os.makedirs(workdir, exist_ok=True)

    snippet = Path(file_path).read_text()
    wrapped = wrap_snippet(snippet, tpl)
    Path(os.path.join(workdir, "main.tex")).write_text(wrapped)

    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"]
    try:
        subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=True)
        if not keep_build:
            try:
                subprocess.run(["latexmk", "-c"], cwd=workdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        return True, "", workdir
    except subprocess.TimeoutExpired:
        return False, f"Timed out after {timeout}s", workdir
    except subprocess.CalledProcessError:
        log_path = os.path.join(workdir, "main.log")
        if os.path.exists(log_path):
            tail = "\n".join(Path(log_path).read_text(errors="ignore").splitlines()[-30:])
        else:
            tail = "Compilation failed; log not found"
        return False, tail, workdir

