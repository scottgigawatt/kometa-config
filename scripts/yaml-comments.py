#!/usr/bin/env python3

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# yaml-comments.py: Align related YAML inline comments without rewriting values.
#
# Purpose: Keep two spaces after the longest entry in each adjacent comment group.
# Usage: python scripts/yaml-comments.py [--fix] tracked-file.yml [...]
#

"""Check or align YAML comments using parser locations, not hash-character guesses."""

import argparse
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.tokens import CommentToken


def align_comments(source: str) -> str:
    """Align adjacent inline comments at the same indentation level.

    Args:
        source: YAML source with comments and original line endings.

    Returns:
        Source with comment spacing normalized; values and standalone comments remain intact.

    Raises:
        ruamel.yaml.YAMLError: If the source is not valid YAML.
    """
    lines = source.splitlines(keepends=True)
    positions: dict[int, int] = {}
    visited: set[int] = set()

    def visit(value: object) -> None:
        """Collect actual comment tokens while avoiding repeated YAML aliases."""
        if id(value) in visited:
            return
        visited.add(id(value))
        if isinstance(value, CommentToken):
            row, column = value.start_mark.line, value.start_mark.column
            if (
                row < len(lines)
                and column < len(lines[row])
                and lines[row][column] == "#"
                and lines[row][:column].strip()
            ):
                positions[row] = column
        elif isinstance(value, (CommentedMap, CommentedSeq)):
            visit(value.ca.comment)
            visit(value.ca.end)
            for comments in value.ca.items.values():
                visit(comments)
            for child in value.values() if isinstance(value, CommentedMap) else value:
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    for document in YAML().load_all(source):
        visit(document)

    #
    # Blank lines, standalone comments, and indentation changes end a logical group.
    # Parser locations leave quoted hashes and literal block contents untouched.
    #
    groups: list[list[int]] = []
    for row in sorted(positions):
        indent = len(lines[row]) - len(lines[row].lstrip())
        previous = groups[-1][-1] if groups else None
        if (
            previous is not None
            and row == previous + 1
            and indent == len(lines[previous]) - len(lines[previous].lstrip())
        ):
            groups[-1].append(row)
        else:
            groups.append([row])
    for group in groups:
        width = max(len(lines[row][: positions[row]].rstrip()) for row in group) + 2
        for row in group:
            column = positions[row]
            lines[row] = lines[row][:column].rstrip().ljust(width) + lines[row][column:]
    return "".join(lines)


def main() -> None:
    """Check explicit source files or apply comment-only formatting when requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix", action="store_true", help="Apply comment spacing changes."
    )
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    changed = []
    for path in args.files:
        source = path.read_text(encoding="utf-8")
        formatted = align_comments(source)
        if source != formatted:
            changed.append(path)
            if args.fix:
                path.write_text(formatted, encoding="utf-8")
            else:
                print(f"Inline comments need alignment: {path}")
    if changed and not args.fix:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
