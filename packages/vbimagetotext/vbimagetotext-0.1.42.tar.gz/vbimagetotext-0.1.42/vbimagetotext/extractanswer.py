import click
import os
import re


@click.command(
    help="Extract correct option letters from tasks blocks across a range of problem files or from a main TeX with \\inputs (use --loop) and write answer_key.tex"
)
@click.option(
    "-i",
    "--input",
    "input_file",
    type=click.Path(exists=True),
    required=True,
    help="Path to a sample problem file (e.g., src/src_tex/problem_1.tex)",
)
@click.option(
    "-r",
    "--range",
    "problem_range",
    nargs=2,
    type=int,
    required=False,
    help="Range of problems to extract (start end), inclusive. Ignored if --loop is used.",
)
@click.option(
    "--loop",
    is_flag=True,
    help="Parse a main .tex file for \\input{...} entries (e.g., inside \\foreach) and extract answers in that order.",
)
def extractanswer(input_file, problem_range, loop):
    """
    For files like src/src_tex/problem_{i}.tex within the given range,
    parse the tasks environment and detect which option has \\ans.
    Generate answer_key.tex with items like (a), (b), (c), or (d).
    """
    dirname = os.path.dirname(input_file)
    answers = []

    def extract_from_content(content: str) -> str:
        tasks_match = re.search(
            r"\\begin{tasks}\s*\([\s\S]*?\)([\s\S]*?)\\end{tasks}",
            content,
            re.DOTALL,
        )

        if not tasks_match:
            return "(?)"

        tasks_content = tasks_match.group(1)
        parts = re.split(r"\\task\s*", tasks_content)
        task_items = parts[1:] if len(parts) > 1 else []
        if not task_items:
            return "(?)"

        correct_index = None
        for idx, item in enumerate(task_items):
            if re.search(r"\\ans(?![A-Za-z])", item):
                correct_index = idx
                break
        if correct_index is None:
            return "(?)"
        letter = chr(ord('a') + correct_index)
        return f"({letter})"

    if loop:
        # Expand simple nested \foreach loops and then scan for \input{...}
        with open(input_file, "r") as f:
            main_tex = f.read()
        # Remove LaTeX comments so commented-out \input lines are ignored
        main_tex = re.sub(r"(?<!\\)%.*", "", main_tex)

        def parse_value_list(spec: str) -> list[str]:
            spec_strip = spec.strip()
            m = re.match(r"^(-?\d+)\s*,\s*\.\.\.\s*,\s*(-?\d+)$", spec_strip)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                step = 1 if b >= a else -1
                return [str(x) for x in range(a, b + step, step)]
            # Plain comma-separated list
            return [tok.strip() for tok in spec.split(',') if tok.strip()]

        # Iteratively expand \foreach \var in {...}{ body }
        foreach_re = re.compile(
            r"\\foreach\s+\\([A-Za-z]+)\s+in\s*\{([^}]*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}",
            re.DOTALL,
        )

        expanded = main_tex
        while True:
            m = foreach_re.search(expanded)
            if not m:
                break
            var, spec, body = m.group(1), m.group(2), m.group(3)
            values = parse_value_list(spec)
            out = []
            var_pat = re.compile(r"\\" + re.escape(var) + r"(?![A-Za-z])")
            for val in values:
                out.append(var_pat.sub(str(val), body))
            expanded_body = "".join(out)
            expanded = expanded[: m.start()] + expanded_body + \
                expanded[m.end():]

        main_tex = expanded
        inputs = re.findall(r"\\input\{([^}]+)\}", main_tex)
        if not inputs:
            print("No \\input{...} entries found in main file.")
        for rel in inputs:
            if rel.strip().endswith("answer_key.tex"):
                continue
            path = rel if os.path.isabs(rel) else os.path.normpath(
                os.path.join(dirname, rel))
            if not os.path.exists(path):
                print(f"Skipping missing file: {path}")
                answers.append("(?)")
                continue
            with open(path, "r") as f:
                content = f.read()
            answers.append(extract_from_content(content))
    else:
        if not problem_range:
            raise click.BadParameter(
                "--range is required unless --loop is used.")
        start, end = problem_range

        filename = os.path.basename(input_file)
        match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
        if not match:
            raise click.BadParameter(
                "Input file name must contain an index number, e.g., problem_1.tex"
            )
        prefix, _, ext = match.groups()

        for i in range(start, end + 1):
            current_filename = f"{prefix}{i}{ext}"
            current_path = os.path.join(dirname, current_filename)

            if not os.path.exists(current_path):
                print(f"Skipping missing file: {current_path}")
                answers.append("(?)")
                continue
            with open(current_path, "r") as f:
                content = f.read()
            answers.append(extract_from_content(content))

        # No direct range parsing beyond this point; logic moved to extract_from_content()

    # Write answer_key.tex in the current working directory
    output_path = os.path.join(os.getcwd(), "answer_key.tex")
    with open(output_path, "w") as out:
        out.write("\\begin{multicols}{5}\n")
        out.write("    \\begin{enumerate}\n")
        for ans in answers:
            out.write(f"        \\item {ans}\n")
        out.write("    \\end{enumerate}\n")
        out.write("\\end{multicols}\n")

    print(f"Wrote answer key for {len(answers)} item(s) to {output_path}")


def extract_answer_letters_from_content(content: str) -> str:
    """
    Return like "(a)" from a single problem snippet content.
    """
    tasks_match = re.search(
        r"\\begin{tasks}\s*\([\s\S]*?\)([\s\S]*?)\\end{tasks}",
        content,
        re.DOTALL,
    )
    if not tasks_match:
        return "(?)"
    tasks_content = tasks_match.group(1)
    parts = re.split(r"\\task\s*", tasks_content)
    task_items = parts[1:] if len(parts) > 1 else []
    if not task_items:
        return "(?)"
    correct_index = None
    for idx, item in enumerate(task_items):
        if re.search(r"\\ans(?![A-Za-z])", item):
            correct_index = idx
            break
    if correct_index is None:
        return "(?)"
    letter = chr(ord('a') + correct_index)
    return f"({letter})"
