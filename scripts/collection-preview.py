#!/usr/bin/env python3

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# collection-preview.py: Validate and run movie and TV collection previews.
#
# Purpose: Select actual source builders and reject unsafe preview configuration.
# Usage: Run inside the pinned image through make validate or test-collections.
#

import argparse
import os
from pathlib import Path

from ruamel.yaml import YAML


def preview_names(franchises, config, smoke, shows):
    """Return selected names after checking fixture isolation and source safety."""
    if set(franchises) != {"templates", "collections"} or set(
        franchises["templates"]
    ) != {"franchise"}:
        raise ValueError(
            "Franchise source must not load additional templates or metadata."
        )
    if set(config) != {"libraries", "settings", "plex", "tmdb"}:
        raise ValueError("Preview must configure only fixtures, Plex, and TMDb.")
    expected = {
        "test_movie_lib": {
            "collection_files": [
                {"file": "/workspace/movies/franchise.yml"},
                {"file": "/workspace/tests/kometa/collections.yml"},
            ]
        },
        "test_tv_lib": {
            "collection_files": [
                {"file": "/workspace/shows/shuffle.yml"},
                {"file": "/workspace/tests/kometa/collections.yml"},
            ]
        },
    }
    if config["libraries"] != expected:
        raise ValueError("Preview library names or collection files are unsafe.")
    settings = config["settings"]
    if settings.get("run_order") != ["collections"] or any(
        settings.get(key) is not False
        for key in ("delete_below_minimum", "delete_not_scheduled", "playlist_report")
    ):
        raise ValueError("Preview must disable deletion, playlists, and other runs.")
    plex = config["plex"]
    if plex.get("url") != "<<plexurl>>" or plex.get("token") != "<<plextoken>>":
        raise ValueError("Preview Plex credentials must use secret substitutions.")
    if config["tmdb"].get("apikey") != "<<tmdbapikey>>":
        raise ValueError("Preview TMDb credentials must use secret substitutions.")
    if any(
        plex.get(key) is not False
        for key in ("clean_bundles", "empty_trash", "optimize")
    ):
        raise ValueError("Preview must disable Plex maintenance.")

    #
    # A narrow template allowlist prevents future download or list-sync settings
    # from being inherited silently by this fixture-only command.
    #
    template = franchises["templates"]["franchise"]
    allowed_template = {
        "file_poster",
        "sort_title",
        "collection_order",
        "sync_mode",
        "schedule",
    }
    if (
        set(template) - allowed_template
        or template.get("collection_order") != "release"
    ):
        raise ValueError(
            "Franchise template must remain release-ordered and read-only outside Plex."
        )
    names = []
    for name, definition in franchises["collections"].items():
        if "trakt_list" in definition:
            raise ValueError("Franchise definitions must not depend on Trakt lists.")
        if "tmdb_collection" not in definition:
            continue
        allowed = {"template", "tmdb_collection", "summary", "sort_title"}
        if (
            set(definition) - allowed
            or definition["template"].get("name") != "franchise"
        ):
            raise ValueError(
                "TMDb preview definitions must use the safe franchise template."
            )
        if set(definition["template"]) != {"name", "poster_id"}:
            raise ValueError("Unexpected franchise template variables.")
        ids = definition["tmdb_collection"]
        if (
            not isinstance(ids, list)
            or not ids
            or any(type(i) is not int or i <= 0 for i in ids)
        ):
            raise ValueError(
                "TMDb collection IDs must be a nonempty list of positive integers."
            )
        if "|" in name:
            raise ValueError("Collection names must not contain the CLI separator.")
        names.append(name)
    if not names:
        raise ValueError("No native franchise builders selected.")

    #
    # Public owner-controlled TV lists need no Trakt credentials or account writes.
    # Fix the template contract so movie expansion and download settings cannot
    # enter the preview through a later template change.
    #
    expected_show_template = {
        "builder_level": "show",
        "trakt_list": "https://trakt.tv/users/scottgigawatt/lists/<<list_slug>>",
        "file_poster": "/config/assets/posters/playlist/<<collection_name>>.png",
        "collection_order": "alpha",
        "sync_mode": "sync",
        "sonarr_add_missing": False,
        "sonarr_add_existing": False,
        "sonarr_search": False,
    }
    if set(shows) != {"templates", "collections"} or shows["templates"] != {
        "shuffle": expected_show_template
    }:
        raise ValueError("TV preview must use the safe show-only template.")
    expected_shows = {
        "Adult Animation": "adult-animation",
        "Saturday Morning Cartoons": "saturday-morning-cartoons",
        "Classic Sitcoms": "classic-sitcoms",
        "Modern Sitcoms": "modern-sitcoms",
    }
    if set(shows["collections"]) != set(expected_shows):
        raise ValueError("TV preview must contain the four curated collections.")
    for name, definition in shows["collections"].items():
        if set(definition) != {"template", "summary"} or definition["template"] != {
            "name": "shuffle",
            "list_slug": expected_shows[name],
        }:
            raise ValueError("Unexpected TV collection source or writer behavior.")
        names.append(name)

    #
    # Validate smoke definitions too, since the same run touches both fixtures.
    #
    if set(smoke) != {"collections"}:
        raise ValueError("Smoke source must contain collections only.")
    allowed_smoke = {
        "plex_search",
        "collection_mode",
        "collection_order",
        "sync_mode",
        "visible_home",
        "visible_library",
        "visible_shared",
    }
    for name, definition in smoke["collections"].items():
        if set(definition) - allowed_smoke or "|" in name:
            raise ValueError("Unexpected smoke collection behavior.")
        names.append(name)
    return names


def load_preview(source):
    """Load tracked source files and verify every collection ID has a name comment."""
    yaml = YAML()
    path = source / "movies/franchise.yml"
    franchises = yaml.load(path.read_text())
    for definition in franchises["collections"].values():
        ids = definition.get("tmdb_collection")
        if ids is None:
            continue
        for index in range(len(ids)):
            comment = ids.ca.items.get(index)
            if not comment or not comment[0] or not comment[0].value.strip("# \n"):
                raise ValueError(
                    "Every TMDb collection ID needs its collection name comment."
                )
    config = yaml.load((source / "tests/kometa/collections-config.yml").read_text())
    smoke = yaml.load((source / "tests/kometa/collections.yml").read_text())
    shows = yaml.load((source / "shows/shuffle.yml").read_text())
    return preview_names(franchises, config, smoke, shows), config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    selected, preview = load_preview(Path("/workspace"))
    if args.run:
        #
        # Check the copied runtime as well as source before enabling Plex writes.
        # Use exec so Kometa receives signals and owns the container exit status.
        #
        if YAML(typ="safe").load(Path("/config/config.yml").read_text()) != preview:
            raise ValueError(
                "Runtime configuration does not match the checked preview."
            )
        os.execvp(
            "python",
            [
                "python",
                "/kometa.py",
                "--config",
                "/config/config.yml",
                "--read-only-config",
                "--no-missing",
                "--collections-only",
                "--ignore-schedules",
                "--run-collections",
                "|".join(selected),
                "--run",
            ],
        )
    print(
        f"Collection preview isolation and ID comments passed ({len(selected)} definitions)."
    )
