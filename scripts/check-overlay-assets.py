#!/usr/bin/env python3

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# check-overlay-assets.py: Check custom artwork against the pinned Defaults.
#
# Purpose: Reject missing artwork and divergent test overlay definitions without
#          accessing Plex, private configuration, or the full artwork checkout.
# Usage: Run through make validate inside the pinned Kometa image.
#

"""Check local overlay coverage using tracked paths and pinned Kometa Defaults."""

import re
from pathlib import Path

from ruamel.yaml import YAML


def check_assets(source: Path, defaults: Path, tracked: set[str]) -> list[str]:
    """Return artwork coverage errors without loading images or private settings.

    Args:
        source: Root of the tracked YAML snapshot mounted by the validator.
        defaults: Overlay catalog directory from the pinned Kometa image.
        tracked: Case-sensitive Git paths available in a complete checkout.

    Returns:
        Missing-artwork and test/production parity errors; empty on success.

    Raises:
        OSError: If a required source or Defaults file cannot be read.
    """
    yaml = YAML(typ="safe")
    config = yaml.load((source / "config.yml").read_text())
    preview = yaml.load((source / "tests/kometa/config.yml").read_text())
    errors = []

    #
    # Evaluate the complete movie and show overlay sets against the same source.
    #
    for production, test in [("Movies", "test_movie_lib"), ("TV Shows", "test_tv_lib")]:
        files = config["libraries"][production]["overlay_files"]
        if files != preview["libraries"][test]["overlay_files"]:
            errors.append(f"{test}: overlay definitions differ from {production}")

        for entry in files:
            if "default" not in entry:
                continue
            name = entry["default"]
            variables = entry.get("template_variables", {})
            if "file" not in variables:
                errors.append(f"{name}: custom artwork override is missing")
                continue
            catalog = yaml.load((defaults / f"{name}.yml").read_text())

            #
            # Defaults keys select file aliases; resolution also selects variants.
            # Unsupported artwork must be explicitly disabled, not silently lost.
            #
            for overlay_name, overlay in catalog["overlays"].items():
                values = overlay.get("variables", {})
                key = str(values.get("key", overlay_name))
                alt = str(values.get("alt", ""))
                if any(
                    variables.get(flag) is False
                    for flag in (f"use_{key}", f"use_{alt}", f"use_{key}_{alt}")
                ):
                    continue
                artwork = variables.get(f"file_{key}", variables["file"])
                artwork = artwork.replace("<<overlay_name>>", str(overlay_name))
                artwork = artwork.replace("<<key>>", key)
                if artwork.removeprefix("config/") not in tracked:
                    errors.append(f"{name}/{overlay_name}: missing {artwork}")

    #
    # Check local ribbons and backgrounds too, resolving the status template.
    # Git's names are authoritative even on case-insensitive macOS filesystems.
    #
    for name in (
        "chart-award-ribbons",
        "corner-background",
        "series-status",
        "network-fallback",
    ):
        text = (source / f"overlays/{name}.yml").read_text()
        for reference in re.findall(
            r"^\s+file: (config/overlays/[^\n]+)", text, re.MULTILINE
        ):
            paths = [reference]
            if "<<status>>" in reference:
                paths = [
                    reference.replace("<<status>>", status)
                    for status in ("airing", "returning", "ended", "cancelled")
                ]
            for artwork in paths:
                if artwork.removeprefix("config/") not in tracked:
                    errors.append(f"{name}: missing {artwork}")
    return errors


def main() -> None:
    """Report artwork errors and exit unsuccessfully when coverage is incomplete."""

    #
    # Use Git's file inventory so sparse CI checkouts need no artwork downloads.
    #
    tracked_files = set(Path("/config/overlay-files").read_text().split("\0"))
    failures = check_assets(
        Path("/workspace"), Path("/defaults/overlays"), tracked_files
    )
    for failure in failures:
        print(f"Overlay check: {failure}")
    if failures:
        raise SystemExit(1)
    print("Custom overlay artwork and test/production parity checks passed.")


if __name__ == "__main__":
    main()
