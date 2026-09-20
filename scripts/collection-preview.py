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
import re
import subprocess
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
                {"file": "/workspace/movies/genre.yml"},
                {"file": "/workspace/movies/subgenre-rules.yml"},
                {"file": "/workspace/movies/cities.yml"},
                {"file": "/workspace/movies/universes.yml"},
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
    # Keep TV membership in named TMDb show IDs with no external curated lists.
    # Fix the template contract so episode expansion and download settings cannot
    # enter the preview through a later template change.
    #
    expected_show_template = {
        "builder_level": "show",
        "file_poster": "/config/assets/posters/playlist/<<collection_name>>.png",
        "collection_order": "alpha",
        "sync_mode": "sync",
    }
    if set(shows) != {"templates", "collections"} or shows["templates"] != {
        "shuffle": expected_show_template
    }:
        raise ValueError("TV preview must use the safe show-only template.")
    expected_shows = {
        "Adult Animation",
        "Saturday Morning Cartoons",
        "Classic Sitcoms",
        "Modern Sitcoms",
    }
    if set(shows["collections"]) != expected_shows:
        raise ValueError("TV preview must contain the four curated collections.")
    for name, definition in shows["collections"].items():
        if set(definition) != {"template", "summary", "tmdb_show"} or definition[
            "template"
        ] != {
            "name": "shuffle",
        }:
            raise ValueError("Unexpected TV collection source or writer behavior.")
        ids = definition["tmdb_show"]
        if (
            not isinstance(ids, list)
            or not ids
            or any(type(i) is not int or i <= 0 for i in ids)
            or len(ids) != len(set(ids))
        ):
            raise ValueError("TMDb show IDs must be unique positive integers.")
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


def check_id_comments(definitions, builder):
    """Require readable inline names beside each explicit TMDb ID."""
    for definition in definitions.values():
        ids = definition.get(builder)
        if ids is None:
            continue
        for index in range(len(ids)):
            comment = ids.ca.items.get(index)
            if not comment or not comment[0] or not comment[0].value.strip("# \n"):
                raise ValueError(
                    "Every TMDb ID needs its title or collection name comment."
                )


def rule_names(genres, themes):
    """Allow only the seven genre rules and six isolated ranked theme searches."""
    genre_template = {
        "file_poster": "/config/assets/posters/genre/<<poster_id>>.jpg",
        "sort_title": "!060_<<collection_name>>",
        "collection_order": "title.asc",
        "sync_mode": "sync",
    }
    if set(genres) != {"templates", "collections"} or genres["templates"] != {
        "genre": genre_template
    }:
        raise ValueError("Genre preview must use the safe artwork template.")
    expected_genres = {
        "Horror Movies": "Horror",
        "LGBTQ+ Movies": "LGBTQ+",
        "Sports Movies": "Sport",
        "Spy Movies": "Spy",
        "Stand-up Comedy": "Stand-Up Comedy",
        "War Movies": "War",
        "Western Movies": "Western",
    }
    if set(genres["collections"]) != set(expected_genres):
        raise ValueError("Genre preview must contain the seven supported genres.")
    for name, definition in genres["collections"].items():
        native = name in {"Horror Movies", "War Movies", "Western Movies"}
        builder = "plex_search" if native else "tmdb_keyword"
        if set(definition) != {"template", "summary", "schedule", builder}:
            raise ValueError("Unexpected genre source or writer behavior.")
        if definition["template"] != {
            "name": "genre",
            "poster_id": expected_genres[name],
        }:
            raise ValueError("Unexpected genre template variables.")
        if native:
            if definition[builder] != {"all": {"genre": expected_genres[name]}}:
                raise ValueError("Native genre previews must use only genre tags.")
        else:
            ids = definition[builder]
            if (
                not isinstance(ids, list)
                or not ids
                or any(type(i) is not int or i <= 0 for i in ids)
                or len(ids) != len(set(ids))
            ):
                raise ValueError("TMDb keyword IDs must be unique positive integers.")

    #
    # Keep only provider search rules in the selected file, with no list writers,
    # external templates, arbitrary search overrides, or static movie additions.
    #
    expected_templates = {
        "ranked_theme": {
            "collection_mode": "hide",
            "collection_order": "release",
            "delete_not_scheduled": False,
            "limit": 250,
            "sort_title": "!061_<<collection_name>>",
            "sync_mode": "sync",
            "visible_home": False,
            "visible_library": False,
            "visible_shared": False,
        },
        "tmdb_theme": {
            "tmdb_discover": {
                "with_keywords": "<<keywords>>",
                "with_original_language": "en",
                "vote_average.gte": 5,
                "vote_count.gte": 1000,
                "sort_by": "vote_average.desc",
                "limit": 1000,
            }
        },
    }
    if (
        set(themes) != {"templates", "collections"}
        or themes["templates"] != expected_templates
    ):
        raise ValueError("Theme preview must use the safe ranked search templates.")
    expected_themes = {
        "Top Rated in Mindfuck",
        "Top Rated in Outerspace",
        "Top Rated in Philosophical",
        "Top Rated in Survival",
        "Top Rated in Time Travel",
        "Top Rated in True Story",
    }
    if set(themes["collections"]) != expected_themes:
        raise ValueError("Theme preview must contain the six supported themes.")
    for name, definition in themes["collections"].items():
        allowed = {"template", "summary", "schedule", "file_poster"}
        if name == "Top Rated in Mindfuck":
            allowed.add("imdb_search")
            if definition.get("imdb_search") != {
                "keyword": "mindbender",
                "type": "movie,tv_movie",
                "rating.gte": 5,
                "votes.gte": 1000,
                "language": "en",
                "sort_by": "rating.desc",
                "limit": 1000,
            } or definition["template"] != [{"name": "ranked_theme"}]:
                raise ValueError("Mindfuck preview must use the IMDb keyword rule.")
        else:
            templates = definition.get("template", [])
            if (
                len(templates) != 2
                or templates[0] != {"name": "ranked_theme"}
                or set(templates[1]) != {"name", "keywords"}
                or templates[1]["name"] != "tmdb_theme"
                or not isinstance(templates[1]["keywords"], str)
                or not re.fullmatch(
                    r"[1-9]\d*(?:\|[1-9]\d*)*", templates[1]["keywords"]
                )
            ):
                raise ValueError(
                    "Theme keywords must be explicit OR-separated TMDb IDs."
                )
        if set(definition) != allowed:
            raise ValueError("Unexpected theme source or writer behavior.")
        if not re.fullmatch(
            r"/config/assets/posters/subgenre_top/subgenre_top_[a-z-]+\.png",
            definition["file_poster"],
        ):
            raise ValueError("Theme posters must use local subgenre artwork.")
    return list(genres["collections"]) + list(themes["collections"])


def location_universe_names(cities, universes):
    """Allow city keywords and native universe builders without external writers."""
    city_template = {
        "file_poster": "/config/assets/posters/cities/<<city>>.png",
        "sort_title": "!105_<<collection_name>>",
        "collection_order": "title.asc",
        "content_rating": "R",
        "summary": "Stories unfolding across the streets and skyline of <<city>>.",
        "sync_mode": "sync",
        "schedule": "weekly(saturday)",
    }
    universe_template = {
        "file_poster": "/config/assets/posters/franchise/<<poster_id>>.jpg",
        "sort_title": "!106_<<collection_name>>",
        "collection_order": "release",
        "sync_mode": "sync",
        "minimum_items": 3,
    }
    city_sources = {
        "Chicago Collection": ("Chicago", "tmdb_keyword"),
        "Detroit Collection": ("Detroit", "tmdb_keyword"),
        "Las Vegas Collection": ("Las Vegas", "tmdb_keyword"),
        "Los Angeles Collection": ("Los Angeles", "tmdb_keyword"),
        "New York Collection": ("New York", "tmdb_keyword"),
        "Washington D.C. Collection": ("Washington DC", "tmdb_keyword"),
    }
    universe_sources = {
        "Marvel Cinematic Universe": ("Marvel Cinematic Universe", "tmdb_keyword"),
        "DC Universe": ("DC Universe", "tmdb_keyword"),
        "Star Trek Universe": ("Star Trek", "tmdb_collection"),
        "Alien / Predator": ("Alien Predator", "tmdb_collection"),
        "X-Men Collection": ("X-Men", "tmdb_collection"),
    }
    names = []
    for source, template_name, template, expected, poster_key in (
        (cities, "city", city_template, city_sources, "city"),
        (universes, "universe", universe_template, universe_sources, "poster_id"),
    ):
        if set(source) != {"templates", "collections"} or source["templates"] != {
            template_name: template
        }:
            raise ValueError(
                "City and universe previews must use safe local templates."
            )
        if set(source["collections"]) != set(expected):
            raise ValueError("Unexpected city or universe collection names.")
        for name, definition in source["collections"].items():
            poster, builder = expected[name]
            allowed = {"template", builder}
            if template_name == "universe":
                allowed.add("summary")
            if set(definition) != allowed or definition["template"] != {
                "name": template_name,
                poster_key: poster,
            }:
                raise ValueError(
                    "Unexpected city or universe source or writer behavior."
                )
            ids = definition[builder]
            if (
                not isinstance(ids, list)
                or not ids
                or any(type(value) is not int or value <= 0 for value in ids)
                or len(ids) != len(set(ids))
            ):
                raise ValueError("TMDb source IDs must be unique positive integers.")
            names.append(name)
    return names


def load_preview(source):
    """Load tracked source files and verify collection and show ID comments."""
    yaml = YAML()
    path = source / "movies/franchise.yml"
    franchises = yaml.load(path.read_text())
    config = yaml.load((source / "tests/kometa/collections-config.yml").read_text())
    smoke = yaml.load((source / "tests/kometa/collections.yml").read_text())
    shows = yaml.load((source / "shows/shuffle.yml").read_text())
    genres = yaml.load((source / "movies/genre.yml").read_text())
    themes = yaml.load((source / "movies/subgenre-rules.yml").read_text())
    cities = yaml.load((source / "movies/cities.yml").read_text())
    universes = yaml.load((source / "movies/universes.yml").read_text())
    names = preview_names(franchises, config, smoke, shows)
    names.extend(rule_names(genres, themes))
    names.extend(location_universe_names(cities, universes))
    check_id_comments(franchises["collections"], "tmdb_collection")
    check_id_comments(shows["collections"], "tmdb_show")
    check_id_comments(genres["collections"], "tmdb_keyword")
    check_id_comments(cities["collections"], "tmdb_keyword")
    check_id_comments(universes["collections"], "tmdb_keyword")
    check_id_comments(universes["collections"], "tmdb_collection")
    for definition in themes["collections"].values():
        for template in definition["template"]:
            if "keywords" in template:
                comment = template.ca.items.get("keywords")
                if not comment or not comment[2] or not comment[2].value.strip("# \n"):
                    raise ValueError(
                        "Every TMDb keyword query needs a descriptive comment."
                    )
    return names, config


def check_run_summary(log, names):
    """Reject failed or missing collection results even when Kometa exits zero."""
    if "[ERROR]" in log or "[CRITICAL]" in log:
        raise ValueError(
            "Collection preview logged errors; inspect the private runtime log."
        )
    remaining = set(names)
    for line in log.splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 6 or cells[0] not in names:
            continue
        if not re.fullmatch(
            r"(?:Unchanged|Created|Modified)(?: and Updated .+)?|Updated .+|Ignored|Minimum [1-9]\d* Not Met",
            cells[-1],
        ):
            raise ValueError(
                "Collection preview failed; inspect the private runtime log."
            )
        remaining.discard(cells[0])
    if remaining:
        raise ValueError(
            "Collection preview summary is incomplete; inspect the private runtime log."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    selected, preview = load_preview(Path("/workspace"))
    if args.run:
        #
        # Check the copied runtime as well as source before enabling Plex writes.
        # Check the fresh run summary because Kometa can report errors and exit zero.
        #
        if YAML(typ="safe").load(Path("/config/config.yml").read_text()) != preview:
            raise ValueError(
                "Runtime configuration does not match the checked preview."
            )
        log_path = Path("/config/logs/meta.log")
        previous = log_path.stat().st_mtime_ns if log_path.exists() else None
        subprocess.run(
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
            check=True,
        )
        if not log_path.exists() or log_path.stat().st_mtime_ns == previous:
            raise ValueError("Collection preview did not produce a fresh runtime log.")
        check_run_summary(log_path.read_text(), selected)
    print(
        f"Collection preview isolation and ID comments passed ({len(selected)} definitions)."
    )
