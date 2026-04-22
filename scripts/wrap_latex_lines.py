#!/usr/bin/env python3
"""Wrap long lines in LaTeX sources for editor readability (LaTeX treats single newlines as space)."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

DEFAULT_WIDTH = 78


def wrap_physical_line(line: str, width: int) -> list[str]:
    """Return one or more lines (without trailing newline)."""
    stripped_right = line.rstrip("\n\r")
    if len(stripped_right) <= width:
        return [stripped_right]

    lead = len(stripped_right) - len(stripped_right.lstrip(" "))
    prefix = stripped_right[:lead]
    body = stripped_right[lead:]
    avail = max(width - lead, 50)

    if not body.strip():
        return [stripped_right]

    chunks = textwrap.wrap(
        body,
        width=avail,
        break_long_words=False,
        break_on_hyphens=True,
    )
    if not chunks:
        return [stripped_right]

    out = [prefix + chunks[0]]
    cont = " " * lead
    out.extend(cont + c for c in chunks[1:])

    # Single newline in LaTeX inserts a space; breaks after '-' would split
    # compounds (e.g. verv-en- / venn). Comment out the newline with '%'.
    for i in range(len(out) - 1):
        t = out[i].rstrip()
        if t.endswith("-"):
            out[i] = t + "%"
    return out


def process_file(path: Path, width: int, dry_run: bool) -> int:
    raw = path.read_text(encoding="utf-8")
    # Normalise to \n for processing; restore final newline convention
    had_final_nl = raw.endswith("\n")
    lines = raw.split("\n")
    out_lines: list[str] = []
    changed = False

    for line in lines:
        # Full-line comment: do not reflow
        if line.lstrip().startswith("%"):
            out_lines.append(line)
            continue
        if len(line) <= width:
            out_lines.append(line)
            continue

        wrapped = wrap_physical_line(line, width)
        if len(wrapped) > 1 or (wrapped and wrapped[0] != line):
            changed = True
        out_lines.extend(wrapped)

    new_text = "\n".join(out_lines)
    if had_final_nl and not new_text.endswith("\n"):
        new_text += "\n"
    elif not had_final_nl and new_text.endswith("\n"):
        new_text = new_text.rstrip("\n")

    if changed and not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return 1 if changed else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = 0
    for p in args.paths:
        if p.is_file() and p.suffix == ".tex":
            total += process_file(p, args.width, args.dry_run)
    print(f"Reformatted {total} file(s).")


if __name__ == "__main__":
    main()
