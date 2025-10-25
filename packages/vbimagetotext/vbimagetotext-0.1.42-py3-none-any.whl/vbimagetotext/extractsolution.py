import click
import os
import re


@click.command(
    help="Extract solution environments from a sequence of LaTeX problem files."
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
    required=True,
    help="Range of problems to extract (start end), inclusive.",
)
def extractsolution(input_file, problem_range):
    """
    Given a sample problem file path like src/src_tex/problem_1.tex and a range,
    read each problem file in that range and extract the solution environment to
    src/solution/problem_{i}.tex one-by-one.
    """
    start, end = problem_range

    dirname = os.path.dirname(input_file)
    filename = os.path.basename(input_file)

    match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
    if not match:
        raise click.BadParameter(
            "Input file name must contain an index number, e.g., problem_1.tex"
        )

    prefix, _, ext = match.groups()

    os.makedirs(os.path.join("src", "solution"), exist_ok=True)

    extracted_count = 0
    for i in range(start, end + 1):
        current_filename = f"{prefix}{i}{ext}"
        current_path = os.path.join(dirname, current_filename)

        if not os.path.exists(current_path):
            print(f"Skipping missing file: {current_path}")
            continue

        with open(current_path, "r") as f:
            content = f.read()

        matches = re.findall(
            r"\\begin{solution}(.*?)\\end{solution}", content, re.DOTALL | re.MULTILINE
        )

        if not matches:
            print(f"No solution found in {current_path}")
            continue

        out_path = os.path.join("src", "solution", f"problem_{i}.tex")
        with open(out_path, "w") as out:
            out.write("\\begin{solution}" + matches[0] + "\\end{solution}")

        extracted_count += 1

    print(f"Extracted {extracted_count} solution(s) to src/solution/")
