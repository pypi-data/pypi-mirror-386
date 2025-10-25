import os
import re
import click


def extract_top_level_items(tex: str) -> list[str]:
    """
    Extract top-level \\item blocks from all top-level enumerate environments.

    - Processes all enumerate environments in the file (e.g., for sections A, B, etc.)
    - Returns a list of strings, each starting with "\\item" that represents one
      whole problem (including any nested enumerate, tasks, tikz, etc.).
    """
    token_re = re.compile(
        r"\\begin\{enumerate\}|\\end\{enumerate\}|\\item\b", re.MULTILINE)
    depth = 0
    in_segment = False
    item_starts: list[int] = []
    segment_bounds: list[tuple[int, int]] = []
    current_segment_start = -1

    # First pass: find all top-level enumerate environments
    for m in token_re.finditer(tex):
        tok = m.group(0)
        if tok.startswith("\\begin{enumerate"):
            if depth == 0:
                current_segment_start = m.start()
                in_segment = True
            depth += 1
            continue

        if tok.startswith("\\end{enumerate"):
            depth -= 1
            if depth == 0 and in_segment:
                segment_bounds.append((current_segment_start, m.end()))
                in_segment = False
            continue

        # Track items only in top-level enumerate
        if tok.startswith("\\item") and depth == 1 and in_segment:
            item_starts.append(m.start())

    # Build items from all segments
    items: list[str] = []
    current_items: list[int] = []
    current_segment_idx = 0

    for pos in sorted(item_starts):
        # Find which segment this item belongs to
        while (current_segment_idx < len(segment_bounds) and
               pos > segment_bounds[current_segment_idx][1]):
            # Process items from previous segment
            if current_items:
                seg_start, seg_end = segment_bounds[current_segment_idx]
                for i, s in enumerate(current_items):
                    if i == len(current_items) - 1:  # Last item in segment
                        e = seg_end  # Include up to end of enumerate
                    else:
                        e = current_items[i + 1]
                    snippet = tex[s:e].strip()
                    if snippet:
                        items.append(snippet)
                current_items = []
            current_segment_idx += 1

        if current_segment_idx < len(segment_bounds):
            current_items.append(pos)

    # Process items from the last segment
    if current_items and current_segment_idx < len(segment_bounds):
        seg_start, seg_end = segment_bounds[current_segment_idx]
        for i, s in enumerate(current_items):
            if i == len(current_items) - 1:  # Last item in final segment
                e = seg_end  # Include up to end of enumerate
            else:
                e = current_items[i + 1]
            snippet = tex[s:e].strip()
            if snippet:
                items.append(snippet)

    return items


def extract_direct_items(tex: str) -> list[str]:
    """
    Extract \\item blocks that appear directly in the document.
    Handles nested environments (enumerate, multicols) and maintains their structure.
    """
    items: list[str] = []
    current_item = []
    in_item = False
    env_depth = 0
    env_stack = []

    lines = tex.split('\n')
    for line in lines:
        line_strip = line.strip()

        # Track environment depth
        if '\\begin{' in line_strip:
            env_name = re.search(r'\\begin\{(.*?)\}', line_strip)
            if env_name:
                env_stack.append(env_name.group(1))
                if in_item:  # If we're in an item, keep the environment
                    current_item.append(line)
                continue

        if '\\end{' in line_strip:
            if env_stack:  # Match corresponding environment
                env_stack.pop()
                if in_item:  # Keep the environment closure if we're in an item
                    current_item.append(line)
                continue

        # Handle items
        if line_strip.startswith('\\item') and not env_stack:  # Only top-level items
            if in_item:
                items.append('\n'.join(current_item))
                current_item = []
            current_item.append(line)
            in_item = True
        elif in_item:
            current_item.append(line)

    if current_item:  # Add the last item
        items.append('\n'.join(current_item))

    return [item.strip() for item in items if item.strip()]


@click.command(help="Extract \\item problems from LaTeX file into individual problem_*.tex files.")
@click.option(
    "-i",
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to LaTeX main file (e.g., main.tex)",
)
@click.option(
    "-o",
    "--output-dir",
    default="src/src_tex",
    show_default=True,
    type=click.Path(file_okay=False),
    help="Directory to write problem_*.tex files",
)
@click.option(
    "--prefix",
    default="problem_",
    show_default=True,
    help="Filename prefix for extracted problems",
)
@click.option(
    "--start-index",
    default=1,
    show_default=True,
    type=int,
    help="Starting index for numbering output files",
)
@click.option(
    "--direct-items",
    is_flag=True,
    default=False,
    help="Extract \\item blocks that appear directly in the document (not in enumerate)",
)
def extractitem(input_file: str, output_dir: str, prefix: str, start_index: int, direct_items: bool):
    with open(input_file, "r") as f:
        tex = f.read()

    items = extract_direct_items(
        tex) if direct_items else extract_top_level_items(tex)
    if not items:
        click.echo(
            "No \\item blocks found." if direct_items else
            "No top-level \\item blocks found inside an enumerate environment."
        )
        return

    os.makedirs(output_dir, exist_ok=True)

    count = 0
    for idx, snippet in enumerate(items, start=start_index):
        out_path = os.path.join(output_dir, f"{prefix}{idx}.tex")
        with open(out_path, "w") as out:
            out.write(snippet)
        count += 1
        click.echo(f"Wrote {out_path}")

    click.echo(f"✅ Extracted {count} problem(s) to {output_dir}")


if __name__ == "__main__":
    extractitem()
