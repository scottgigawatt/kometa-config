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

"""Validate fixture isolation before optionally running collection previews."""

import argparse
import copy
import re
import subprocess
from pathlib import Path

from ruamel.yaml import YAML


def preview_names(franchises, config, smoke, shows) -> list[str]:
    """Select franchise, smoke, and TV collections after checking isolation.

    Args:
        franchises: Parsed franchise source with its shared template.
        config: Credential-free configuration for the two fixture libraries.
        smoke: Parsed smoke collections shared by both fixture libraries.
        shows: Parsed show-only definitions and their local template.

    Returns:
        Collection names permitted in the explicit preview run.

    Raises:
        ValueError: If a source violates the fixture or no-writer contract.
    """

    #
    # Validate library targets and service boundaries before selecting builders.
    #
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
                {"file": "/workspace/movies/franchises.yml"},
                {"file": "/workspace/movies/genres.yml"},
                {"file": "/workspace/movies/top-rated-subgenres.yml"},
                {"file": "/workspace/movies/cities.yml"},
                {"file": "/workspace/movies/universes.yml"},
                {"file": "/config/holiday-movies.yml"},
                {"file": "/workspace/tests/kometa/smoke-collections.yml"},
            ]
        },
        "test_tv_lib": {
            "collection_files": [
                {"file": "/workspace/shows/animation-and-sitcoms.yml"},
                {"file": "/config/holiday-episodes.yml"},
                {"file": "/workspace/tests/kometa/smoke-collections.yml"},
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


def check_id_comments(definitions, builder: str) -> None:
    """Require readable inline names beside each explicit TMDb ID.

    Args:
        definitions: Round-trip YAML mappings that retain inline comments.
        builder: Builder key whose ID sequence needs adjacent title comments.

    Raises:
        ValueError: If an explicit ID is missing a nonempty inline comment.
    """
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


def rule_names(genres, themes) -> list[str]:
    """Allow only the seven genre rules and 101 ranked theme searches.

    Args:
        genres: Parsed genre definitions and their shared artwork template.
        themes: Parsed ranked searches and their local templates.

    Returns:
        Genre and theme collection names permitted in the preview.

    Raises:
        ValueError: If builders, templates, or artwork violate the allowlist.
    """

    #
    # Keep local artwork and native genre rules independent of curated lists.
    #
    genre_template = {
        "file_poster": "/config/assets/posters/genre/<<poster_id>>.jpg",
        "sort_title": "!060_<<collection_name>>",
        "collection_order": "title.asc",
        "sync_mode": "sync",
        "schedule": "weekly(tuesday)",
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
        allowed = {"template", "summary", builder}
        if name == "Horror Movies":
            allowed.add("schedule")
        if set(definition) != allowed:
            raise ValueError("Unexpected genre source or writer behavior.")
        if name == "Horror Movies" and definition["schedule"] != "range(11/01-09/14)":
            raise ValueError("Horror must retain its non-Halloween schedule.")
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
    # Exact templates prevent inherited list builders, writers, or hidden filters.
    # Validate every theme, including definitions outside the selected test scope.
    #
    expected_templates = {
        "ranked_theme": {
            "file_poster": "/config/assets/posters/subgenre_top/subgenre_top_<<poster>>.png",
            "schedule": "weekly(<<day>>)",
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
            "default": {"minimum_rating": 5, "minimum_votes": 1000},
            "optional": ["keywords", "genres", "excluded_keywords"],
            "tmdb_discover": {
                "with_keywords": "<<keywords>>",
                "with_genres": "<<genres>>",
                "without_keywords": "<<excluded_keywords>>",
                "with_original_language": "en",
                "vote_average.gte": "<<minimum_rating>>",
                "vote_count.gte": "<<minimum_votes>>",
                "sort_by": "vote_average.desc",
                "limit": 1000,
            },
        },
        "imdb_theme": {
            "default": {"minimum_rating": 5, "minimum_votes": 1000},
            "optional": ["genre"],
            "imdb_search": {
                "keyword": "<<keyword>>",
                "genre": "<<genre>>",
                "language": "en",
                "type": "movie,tv_movie",
                "rating.gte": "<<minimum_rating>>",
                "votes.gte": "<<minimum_votes>>",
                "sort_by": "rating.desc",
                "limit": 1000,
            },
        },
    }
    if (
        set(themes) != {"templates", "collections"}
        or themes["templates"] != expected_templates
    ):
        raise ValueError("Theme preview must use the safe ranked search templates.")
    if len(themes["collections"]) != 101:
        raise ValueError("Theme preview must contain all 101 supported themes.")

    #
    # Preserve deliberate per-theme floors instead of silently standardizing them.
    #
    thresholds = {
        "Top Rated in Bigfoot": {"minimum_votes": 500},
        "Top Rated in Boxing": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Bugs": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Cannibals": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Caper": {"minimum_votes": 100},
        "Top Rated in Chick-flick": {"minimum_votes": 100},
        "Top Rated in Con-Artists": {"minimum_rating": 2},
        "Top Rated in Cop": {"minimum_rating": 2},
        "Top Rated in Dragons": {"minimum_rating": 3},
        "Top Rated in Experimental": {"minimum_rating": 3},
        "Top Rated in Found Footage": {"minimum_rating": 2},
        "Top Rated in Gothic": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Heartbreak": {"minimum_rating": 1, "minimum_votes": 10},
        "Top Rated in Medical": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Military": {"minimum_rating": 2},
        "Top Rated in Mockumentary": {"minimum_rating": 2},
        "Top Rated in Naval": {"minimum_rating": 2},
        "Top Rated in Outlaw": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Pandemic": {"minimum_rating": 2},
        "Top Rated in Prehistoric": {"minimum_rating": 2},
        "Top Rated in Prison": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Psychedelic": {"minimum_rating": 2},
        "Top Rated in Psychological": {"minimum_rating": 2},
        "Top Rated in Religion": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Remake": {"minimum_votes": 100},
        "Top Rated in Revenge": {"minimum_rating": 3},
        "Top Rated in Robots": {"minimum_rating": 3},
        "Top Rated in Samurai": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Space Opera": {"minimum_rating": 2},
        "Top Rated in Spaghetti Western": {"minimum_rating": 1, "minimum_votes": 10},
        "Top Rated in Splatter": {"minimum_rating": 2},
        "Top Rated in Stoner": {"minimum_rating": 1},
        "Top Rated in Stop-Motion": {"minimum_votes": 100},
        "Top Rated in Swashbuckler": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Sword & Sandal": {"minimum_rating": 3},
        "Top Rated in Sword & Sorcery": {"minimum_rating": 3},
        "Top Rated in Treasure Hunt": {"minimum_rating": 2, "minimum_votes": 100},
        "Top Rated in Whodunit?": {"minimum_rating": 2, "minimum_votes": 100},
    }
    imdb_keywords = {
        "Top Rated in Chick-flick": "chick-flick",
        "Top Rated in Epics": "epic",
        "Top Rated in Experimental": "experimental-film",
        "Top Rated in Historical Event": "historical-event",
        "Top Rated in Medical": "medical",
        "Top Rated in Melodrama": "melodrama",
        "Top Rated in Psychedelic": "psychedelic",
        "Top Rated in Spaghetti Western": "spaghetti-western",
        "Top Rated in Splatter": "splatter",
        "Top Rated in Urban Fantasy": "urban-fantasy",
        "Top Rated in Mindfuck": "mindbender",
    }
    for name, definition in themes["collections"].items():
        if (
            not name.startswith("Top Rated in ")
            or "|" in name
            or set(definition) != {"template", "summary"}
        ):
            raise ValueError("Unexpected theme source or writer behavior.")
        templates = definition["template"]
        if (
            not isinstance(templates, list)
            or len(templates) != 2
            or not isinstance(templates[0], dict)
            or set(templates[0]) != {"name", "poster", "day"}
            or templates[0]["name"] != "ranked_theme"
            or not isinstance(templates[1], dict)
        ):
            raise ValueError("Themes must use the ranked and provider templates.")
        variables = templates[1]
        floors = {k: v for k, v in variables.items() if k.startswith("minimum_")}
        if floors != thresholds.get(name, {}) or any(
            type(v) is not int for v in floors.values()
        ):
            raise ValueError("Theme rating and vote floors must remain explicit.")
        allowed = {"name", *floors}
        if name in imdb_keywords:
            expected = {"name": "imdb_theme", "keyword": imdb_keywords[name], **floors}
            if name == "Top Rated in Splatter":
                expected["genre"] = "horror"
            if variables != expected:
                raise ValueError(
                    "IMDb themes must use only their native keyword search."
                )
        else:
            allowed |= {"keywords", "genres", "excluded_keywords"}
            if variables.get("name") != "tmdb_theme" or set(variables) - allowed:
                raise ValueError("Unexpected TMDb theme variables.")
            if not (variables.get("keywords") or variables.get("genres")):
                raise ValueError("TMDb themes need a keyword or genre restriction.")
            for key, separator in (
                ("keywords", r"\|"),
                ("genres", ","),
                ("excluded_keywords", r"\|"),
            ):
                if key not in variables:
                    continue
                value = variables[key]
                if (
                    not isinstance(value, str)
                    or not re.fullmatch(rf"[1-9]\d*(?:{separator}[1-9]\d*)*", value)
                    or len(re.split(separator, value))
                    != len(set(re.split(separator, value)))
                ):
                    raise ValueError(
                        "Theme IDs must be explicit, positive, and unique."
                    )
        if not isinstance(templates[0]["poster"], str) or not re.fullmatch(
            r"[a-z]+(?:-[a-z]+)*", templates[0]["poster"]
        ):
            raise ValueError("Theme posters must use local subgenre artwork.")
        if (
            not isinstance(definition["summary"], str)
            or not definition["summary"].strip()
        ):
            raise ValueError("Themes require a viewer-facing summary.")
        if not isinstance(templates[0]["day"], str) or not re.fullmatch(
            r"monday|tuesday|wednesday|thursday|friday|saturday|sunday",
            templates[0]["day"],
        ):
            raise ValueError("Themes must retain a weekly schedule.")
    return list(genres["collections"]) + list(themes["collections"])


def location_universe_names(cities, universes) -> list[str]:
    """Allow city keywords and native universe builders without external writers.

    Args:
        cities: Parsed city keyword definitions and their local template.
        universes: Parsed universe definitions and their release-order template.

    Returns:
        The six city names and five universe names permitted in the preview.

    Raises:
        ValueError: If source names, IDs, artwork, or behavior are unapproved.
    """

    #
    # Fix template behavior so a later edit cannot silently enable side effects.
    #
    city_template = {
        "file_poster": "/config/assets/posters/cities/<<city>>.png",
        "sort_title": "!105_<<collection_name>>",
        "collection_order": "title.asc",
        "content_rating": "R",
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
    #
    # Permit only named native builders and their case-correct artwork mappings.
    #
    names = []
    for source, template_name, template, expected, poster_key in (
        (cities, "city", city_template, city_sources, "city"),
        (universes, "universe", universe_template, universe_sources, "poster_id"),
    ):
        actual_templates = copy.deepcopy(source.get("templates", {}))
        if template_name == "city":
            summary = actual_templates.get("city", {}).pop("summary", None)
            if not isinstance(summary, str) or not summary.strip():
                raise ValueError("Cities require a viewer-facing summary.")
        if set(source) != {"templates", "collections"} or actual_templates != {
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


def seasonal_names(seasonal) -> list[str]:
    """Allow native holiday sources with no downloads or hidden template behavior.

    Args:
        seasonal: Round-trip YAML containing holiday definitions and ID comments.

    Returns:
        The thirteen seasonal movie collection names permitted in the preview.

    Raises:
        ValueError: If sources, schedules, artwork, or side effects are unapproved.
    """

    #
    # Production retains scheduled deletion; the guarded fixture copy disables it.
    # All download and existing-item writes must already be off in the source.
    #
    expected_template = {
        "file_poster": "/config/assets/posters/seasonal/<<poster_id>>.jpg",
        "sort_title": "!00_<<collection_name>>",
        "collection_order": "critic_rating.desc",
        "sync_mode": "sync",
        "visible_library": True,
        "visible_home": True,
        "visible_shared": True,
        "delete_not_scheduled": True,
        "radarr_add_missing": False,
        "radarr_add_existing": False,
        "radarr_search": False,
        "radarr_upgrade_existing": False,
        "radarr_monitor_existing": False,
    }
    if set(seasonal) != {"templates", "collections"} or seasonal["templates"] != {
        "seasonal": expected_template
    }:
        raise ValueError("Seasonal preview must use the safe no-download template.")
    expected = {
        "Valentine's Day Movies": ("valentine", "02/10-02/14"),
        "St. Patrick's Day Movies": ("patrick", "03/16-03/18"),
        "Easter Movies": ("easter", "03/22-04/25"),
        "Mother's Day Movies": ("mother", "05/01-05/25"),
        "Halloween and Horror Movies": ("halloween", "09/15-10/31"),
        "Thanksgiving Movies": ("thanksgiving", "11/01-12/15"),
        "Christmas Movies": ("christmas", "11/01-01/10"),
        "Hallmark Christmas Movies": ("christmas_hallmark", "11/01-01/10"),
        "Lifetime Christmas Movies": ("christmas_lifetime", "11/01-01/10"),
        "Rankin/Bass Christmas Movies": ("christmas_rankin-bass", "11/01-01/10"),
        "Vintage Christmas Movies": ("christmas_vintage", "11/01-01/10"),
        "Horror Christmas Movies": ("christmas_horror", "11/01-01/10"),
        "New Year's Eve Movies": ("years", "12/26-01/10"),
    }
    if set(seasonal["collections"]) != set(expected):
        raise ValueError("Seasonal preview must contain the thirteen holiday movies.")

    #
    # Constrain each family to its intended native source and local artwork.
    # Exact key sets reject writers, external templates, and source overrides.
    #
    for name, definition in seasonal["collections"].items():
        poster, dates = expected[name]
        allowed = {"template", "schedule", "summary"}
        if (
            definition.get("template")
            != {
                "name": "seasonal",
                "poster_id": poster,
            }
            or definition.get("schedule") != f"range({dates})"
        ):
            raise ValueError("Unexpected seasonal artwork, schedule, or variables.")
        if (
            not isinstance(definition.get("summary"), str)
            or not definition["summary"].strip()
        ):
            raise ValueError("Seasonal collections need a viewer-facing summary.")
        if "Christmas" in name:
            allowed.add("tmdb_discover")
            query = definition.get("tmdb_discover", {})
            query_keys = {"with_keywords", "limit"}
            if (
                query.get("with_keywords") != "207317"
                or not isinstance(query.get("limit"), int)
                or isinstance(query.get("limit"), bool)
                or query["limit"] != 0
            ):
                raise ValueError("Christmas discovery must be uncapped and themed.")
            if name.startswith(("Hallmark", "Lifetime", "Rankin/Bass")):
                query_keys.add("with_companies")
                companies = query.get("with_companies")
                if not isinstance(companies, str) or not re.fullmatch(
                    r"[1-9]\d*(?:\|[1-9]\d*)*", companies
                ):
                    raise ValueError("Christmas studios require explicit company IDs.")
            if name == "Vintage Christmas Movies":
                query_keys.add("primary_release_date.lte")
                if query.get("primary_release_date.lte") != "12/31/1979":
                    raise ValueError("Vintage Christmas ends with the 1979 releases.")
            if name == "Horror Christmas Movies":
                query_keys.add("with_genres")
                if query.get("with_genres") != "27":
                    raise ValueError("Horror Christmas requires the Horror genre.")
            if set(query) != query_keys:
                raise ValueError("Unexpected seasonal discovery override.")
            for key in query_keys & {"with_keywords", "with_companies", "with_genres"}:
                comment = query.ca.items.get(key)
                if not comment or not comment[2] or not comment[2].value.strip("# \n"):
                    raise ValueError(
                        "Every seasonal TMDb query needs named ID comments."
                    )
        else:
            allowed.add("tmdb_keyword")
            ids = definition.get("tmdb_keyword")
            if (
                not isinstance(ids, list)
                or not ids
                or any(type(value) is not int or value <= 0 for value in ids)
                or len(ids) != len(set(ids))
            ):
                raise ValueError("Seasonal keywords must be unique positive integers.")
        if name == "Christmas Movies":
            allowed.add("filters")
            filters = definition.get("filters", {})
            if (
                set(filters) != {"title.not"}
                or not isinstance(filters["title.not"], list)
                or any(not isinstance(title, str) for title in filters["title.not"])
            ):
                raise ValueError("Christmas exclusions must remain title filters.")
        searches = {
            "Valentine's Day Movies": [
                {"all": {"genre": "Romance, Comedy"}},
                {"all": {"genre": "Romance, Drama"}},
            ],
            "Halloween and Horror Movies": {"any": {"genre": "Horror"}},
        }
        if name in searches:
            allowed.add("plex_search")
            if definition.get("plex_search") != searches[name]:
                raise ValueError("Unexpected seasonal Plex search.")
        if set(definition) != allowed:
            raise ValueError("Unexpected seasonal source or writer behavior.")
    check_id_comments(seasonal["collections"], "tmdb_keyword")
    return list(seasonal["collections"])


def seasonal_preview(seasonal) -> dict:
    """Copy validated sources for a preview with no Radarr connection or deletion.

    Args:
        seasonal: Round-trip holiday YAML with production download flags disabled.

    Returns:
        A separate source copy with unchanged builders, artwork, and schedules.

    Raises:
        ValueError: If production source violates the seasonal safety contract.
    """
    seasonal_names(seasonal)
    result = copy.deepcopy(seasonal)
    template = result["templates"]["seasonal"]

    #
    # Kometa requires a Radarr connection even for false Radarr attributes.
    # Remove only the five validated false flags from the disconnected fixture.
    #
    for key in (
        "radarr_add_missing",
        "radarr_add_existing",
        "radarr_search",
        "radarr_upgrade_existing",
        "radarr_monitor_existing",
    ):
        del template[key]
    template["delete_not_scheduled"] = False
    return result


def tv_seasonal_names(seasonal) -> list[str]:
    """Validate episode-only holiday rules and their no-download template.

    Args:
        seasonal: Parsed TV holiday source with local title and summary filters.

    Returns:
        The three TV holiday collection names permitted in the preview.

    Raises:
        ValueError: If sources, episode scope, patterns, or side effects are unsafe.
    """
    expected_template = {
        "file_poster": "/config/assets/posters/seasonal/<<poster_id>>.jpg",
        "sort_title": "!00_<<collection_name>>",
        "sync_mode": "sync",
        "builder_level": "episode",
        "plex_all": True,
        "filters": [
            {"title.regex": "<<holiday_pattern>>"},
            {"summary.regex": "<<holiday_pattern>>"},
        ],
        "visible_library": True,
        "visible_home": True,
        "visible_shared": True,
        "delete_not_scheduled": True,
    }
    if set(seasonal) != {"templates", "collections"} or seasonal["templates"] != {
        "seasonal": expected_template
    }:
        raise ValueError("TV holidays require the safe episode-only template.")
    expected = {
        "Halloween Episodes": ("halloween", "09/15-10/31"),
        "Thanksgiving Episodes": ("thanksgiving", "11/01-12/15"),
        "Christmas Episodes": ("christmas", "11/20-12/28"),
    }
    if set(seasonal["collections"]) != set(expected):
        raise ValueError("TV holidays must contain exactly three episode collections.")

    #
    # Keep patterns editable while rejecting extra builders, writers, and variables.
    # Test representative matches separately so regex syntax alone is not the gate.
    #
    for name, definition in seasonal["collections"].items():
        poster, dates = expected[name]
        if set(definition) != {"template", "schedule", "summary"}:
            raise ValueError("Unexpected TV holiday source or writer behavior.")
        template = definition["template"]
        if (
            set(template) != {"name", "poster_id", "holiday_pattern"}
            or template["name"] != "seasonal"
            or template["poster_id"] != poster
            or definition["schedule"] != f"range({dates})"
        ):
            raise ValueError("Unexpected TV holiday artwork, schedule, or variables.")
        if (
            not isinstance(definition["summary"], str)
            or not definition["summary"].strip()
        ):
            raise ValueError("TV holidays need viewer-facing summaries.")
        pattern = template["holiday_pattern"]
        if not isinstance(pattern, str) or not pattern.strip() or "<<" in pattern:
            raise ValueError("TV holidays require explicit nonempty regex patterns.")
        try:
            compiled = re.compile(pattern)
        except re.error as error:
            raise ValueError("TV holiday regex pattern is invalid.") from error
        if compiled.search(""):
            raise ValueError("TV holiday patterns must not match empty metadata.")
    return list(seasonal["collections"])


def tv_seasonal_preview(seasonal) -> dict:
    """Copy validated TV holidays with scheduled deletion disabled for fixtures.

    Args:
        seasonal: Episode-only holiday source without download-client attributes.

    Returns:
        A separate copy with unchanged episode rules, posters, and schedules.

    Raises:
        ValueError: If source validation fails before rendering the fixture copy.
    """
    tv_seasonal_names(seasonal)
    result = copy.deepcopy(seasonal)
    template = result["templates"]["seasonal"]

    #
    # Episode collections do not support Sonarr attributes, even when false.
    # Keep the same local builders and change only scheduled deletion for tests.
    #
    template["delete_not_scheduled"] = False
    return result


def load_preview(source: Path) -> tuple[list[str], dict]:
    """Load preview sources and validate their behavior and readable ID comments.

    Args:
        source: Root of the credential-free source snapshot mounted by Docker.

    Returns:
        Selected collection names and the validated fixture configuration.

    Raises:
        OSError: If a required mounted source file cannot be read.
        ValueError: If a source violates an isolation or documentation rule.
    """

    #
    # Round-trip parsing preserves the ID comments checked below.
    #
    yaml = YAML()
    path = source / "movies/franchises.yml"
    franchises = yaml.load(path.read_text())
    config = yaml.load((source / "tests/kometa/collections-config.yml").read_text())
    smoke = yaml.load((source / "tests/kometa/smoke-collections.yml").read_text())
    shows = yaml.load((source / "shows/animation-and-sitcoms.yml").read_text())
    genres = yaml.load((source / "movies/genres.yml").read_text())
    themes = yaml.load((source / "movies/top-rated-subgenres.yml").read_text())
    cities = yaml.load((source / "movies/cities.yml").read_text())
    universes = yaml.load((source / "movies/universes.yml").read_text())
    seasonal = yaml.load((source / "scheduled/holiday-movies.yml").read_text())
    tv_seasonal = yaml.load((source / "shows/holiday-episodes.yml").read_text())
    names = preview_names(franchises, config, smoke, shows)
    names.extend(rule_names(genres, themes))
    names.extend(location_universe_names(cities, universes))
    names.extend(seasonal_names(seasonal))
    names.extend(tv_seasonal_names(tv_seasonal))
    check_id_comments(franchises["collections"], "tmdb_collection")
    check_id_comments(shows["collections"], "tmdb_show")
    check_id_comments(genres["collections"], "tmdb_keyword")
    check_id_comments(cities["collections"], "tmdb_keyword")
    check_id_comments(universes["collections"], "tmdb_keyword")
    check_id_comments(universes["collections"], "tmdb_collection")
    for definition in themes["collections"].values():
        for template in definition["template"]:
            for key in ("keywords", "genres", "excluded_keywords"):
                if key not in template:
                    continue
                comment = template.ca.items.get(key)
                if not comment or not comment[2] or not comment[2].value.strip("# \n"):
                    raise ValueError("Every TMDb ID query needs a descriptive comment.")
    return names, config


def check_run_summary(log: str, names: list[str]) -> None:
    """Reject failed or missing collection results even when Kometa exits zero.

    Args:
        log: Fresh runtime log read privately after Kometa finishes.
        names: Every selected collection that must have a successful result.

    Raises:
        ValueError: If errors, unsuccessful states, or missing results are found.
    """
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


def main() -> None:
    """Validate mounted sources and run Plex previews only with explicit --run.

    Raises:
        ValueError: If isolation checks or the fresh run summary fail.
        subprocess.CalledProcessError: If the Kometa process exits unsuccessfully.
    """

    #
    # Keep the default invocation offline; Plex writes require the explicit flag.
    #
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--seasonal-only", action="store_true")
    scope.add_argument("--tv-seasonal-only", action="store_true")
    scope.add_argument("--subgenres-only", action="store_true")
    args = parser.parse_args()
    selected, preview = load_preview(Path("/workspace"))
    library_args = []
    if args.seasonal_only:
        selected = seasonal_names(
            YAML().load(Path("/workspace/scheduled/holiday-movies.yml").read_text())
        )
        library_args = ["--libraries", "test_movie_lib"]
    elif args.tv_seasonal_only:
        selected = tv_seasonal_names(
            YAML().load(Path("/workspace/shows/holiday-episodes.yml").read_text())
        )
        library_args = ["--libraries", "test_tv_lib"]
    elif args.subgenres_only:
        selected = list(
            YAML().load(Path("/workspace/movies/top-rated-subgenres.yml").read_text())[
                "collections"
            ]
        )
        library_args = ["--libraries", "test_movie_lib"]
    if args.run:
        #
        # Check the copied runtime as well as source before enabling Plex writes.
        # Check the fresh run summary because Kometa can report errors and exit zero.
        #
        if YAML(typ="safe").load(Path("/config/config.yml").read_text()) != preview:
            raise ValueError(
                "Runtime configuration does not match the checked preview."
            )

        #
        # Render only the guarded holiday copy into private runtime storage.
        # All membership and presentation inputs remain identical to the source.
        #
        yaml = YAML()
        seasonal = yaml.load(
            Path("/workspace/scheduled/holiday-movies.yml").read_text()
        )
        yaml.dump(seasonal_preview(seasonal), Path("/config/holiday-movies.yml"))
        tv_seasonal = yaml.load(
            Path("/workspace/shows/holiday-episodes.yml").read_text()
        )
        yaml.dump(
            tv_seasonal_preview(tv_seasonal), Path("/config/holiday-episodes.yml")
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
            ]
            + library_args,
            check=True,
        )
        if not log_path.exists() or log_path.stat().st_mtime_ns == previous:
            raise ValueError("Collection preview did not produce a fresh runtime log.")
        check_run_summary(log_path.read_text(), selected)
    print(
        f"Collection preview isolation and ID comments passed ({len(selected)} definitions)."
    )


if __name__ == "__main__":
    main()
