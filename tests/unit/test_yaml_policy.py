#!/usr/bin/env python3

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_yaml_policy.py: Protect YAML comments, shuffle eligibility, and Arr monitoring.
#

"""Check repository YAML conventions and the movie shuffle's selection policy."""

import copy
import importlib
import re
import unittest
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from modules import util
from modules.tmdb import TMDb
from ruamel.yaml import YAML


class YamlPolicyTests(unittest.TestCase):
    """Keep source conventions and explicit movie eligibility under regression tests."""

    def setUp(self) -> None:
        """Load the tracked source snapshot mounted by the offline validator."""
        self.root = Path("/workspace")
        self.yaml = YAML(typ="safe")

    #
    # The validator snapshot excludes generated files, private environments, and logs.
    #
    def test_yaml_headers(self) -> None:
        """Require standard ownership, license, and filename headers on tracked YAML."""
        paths = sorted(self.root.rglob("*.yml")) + sorted(self.root.rglob("*.yaml"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.relative_to(self.root)):
                header = "\n".join(path.read_text().splitlines()[:10])
                self.assertIn("Copyright 2025-2026 Scott Gigawatt", header)
                self.assertIn("Licensed under the Apache License, Version 2.0.", header)
                self.assertIn(f"# {path.name}:", header)

    def test_subgenre_id_comments(self) -> None:
        """Keep readable ID comments with room for block alignment."""
        source = (self.root / "movies/top-rated-subgenres.yml").read_text()
        lines = [
            line
            for line in source.splitlines()
            if re.match(r"\s+(keywords|genres|excluded_keywords):", line)
        ]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line):
                self.assertRegex(line, r'^\s+\w+: "[0-9|,]+" {2,}# \S')

    def test_definition_filenames_use_kebab_case(self) -> None:
        """Keep authored collection, overlay, playlist, and fixture names consistent."""
        for folder in (
            "movies",
            "shows",
            "scheduled",
            "overlays",
            "playlists",
            "tests/kometa",
        ):
            for path in (self.root / folder).rglob("*.yml"):
                with self.subTest(path=path.relative_to(self.root)):
                    self.assertRegex(path.name, r"^[a-z0-9]+(?:-[a-z0-9]+)*\.yml$")

    def test_configuration_source_paths_exist(self) -> None:
        """Resolve local source wiring after renames without reading private runtime state."""

        #
        # Collection previews generate these two guarded copies from tracked source.
        # Every other local definition must exist in the read-only YAML snapshot.
        #
        generated = {
            "/config/holiday-movies.yml": "scheduled/holiday-movies.yml",
            "/config/holiday-episodes.yml": "shows/holiday-episodes.yml",
        }
        for name in (
            "config.yml",
            "tests/kometa/config.yml",
            "tests/kometa/collections-config.yml",
        ):
            config = self.yaml.load((self.root / name).read_text())
            scopes = [config, *config["libraries"].values()]
            for scope in scopes:
                for key in ("collection_files", "overlay_files", "playlist_files"):
                    for entry in scope.get(key, []):
                        for kind in ("file", "folder"):
                            if kind not in entry:
                                continue
                            original = entry[kind]
                            relative = generated.get(original, original)
                            for prefix in ("/workspace/", "/config/", "config/"):
                                if relative.startswith(prefix):
                                    relative = relative.removeprefix(prefix)
                                    break
                            target = self.root / relative
                            with self.subTest(config=name, kind=kind, path=original):
                                self.assertTrue(
                                    target.is_file()
                                    if kind == "file"
                                    else target.is_dir()
                                )

    def test_existing_arr_monitoring_disabled(self) -> None:
        """Leave existing movie and episode monitoring under Radarr and Sonarr control."""
        config = self.yaml.load((self.root / "config.yml").read_text())
        for service in ("radarr", "sonarr"):
            with self.subTest(service=service):
                self.assertIs(config[service]["monitor_existing"], False)

    #
    # Keep file loading separate from global settings and preserve scheduled operations.
    # These checks need no service connections or production library access.
    #
    def test_playlist_file_entries_and_sharing(self) -> None:
        """Keep sharing enabled globally without treating it as a playlist source."""
        config = self.yaml.load((self.root / "config.yml").read_text())
        self.assertEqual(config["settings"]["playlist_sync_to_users"], "all")
        self.assertEqual(
            config["playlist_files"],
            [
                {"file": "config/playlists/battlestar-galactica-timeline.yml"},
                {"default": "playlist"},
            ],
        )

    def test_unused_nightly_setting_absent(self) -> None:
        """Reject the obsolete update-check flag ignored by the pinned runtime."""
        config = self.yaml.load((self.root / "config.yml").read_text())
        self.assertNotIn("check_nightly", config["settings"])

    def test_operation_blocks_and_schedule(self) -> None:
        """Preserve operation sources and every allowed day/hour in list form."""
        config = self.yaml.load((self.root / "config.yml").read_text())
        for library in ("Movies", "TV Shows"):
            expected: dict[str, str | bool] = {
                "schedule": "all[weekly(monday|thursday|saturday), hourly(05-07)]",
                "mass_genre_update": "tmdb",
                "mass_audience_rating_update": "imdb",
                "mass_critic_rating_update": "mdb_tomatoes",
            }
            if library == "Movies":
                expected["assets_for_all"] = True
            operations = config["libraries"][library]["operations"]
            with self.subTest(library=library):
                self.assertEqual(operations, [expected])
                self.assertEqual(
                    util.parse("Config", "operations", operations, datatype="listdict"),
                    util.parse("Config", "operations", expected, datatype="listdict"),
                )

            #
            # Exercise Kometa's scheduler across a full week, including hour boundaries.
            #
            monday = datetime(2026, 9, 21, tzinfo=UTC)
            for day_offset in range(7):
                for hour in range(24):
                    day = monday + timedelta(days=day_offset, hours=hour)
                    with self.subTest(library=library, day=day.weekday(), hour=hour):
                        eligible = day.weekday() in (0, 3, 5) and 5 <= hour <= 7
                        try:
                            util.schedule_check(
                                "schedule", operations[0]["schedule"], day, hour
                            )
                            scheduled = True
                        except util.NotScheduled:
                            scheduled = False
                        self.assertEqual(scheduled, eligible)

    #
    # Scheduled movie files share the Movies library; TV titles have a separate scope.
    # Upstream dynamic names still require log review because they depend on library data.
    #
    def test_static_collection_names_unique(self) -> None:
        """Reject duplicate explicit names across files targeting the same library."""
        groups = {"Movies": ("movies", "scheduled"), "TV Shows": ("shows",)}
        for library, folders in groups.items():
            names = defaultdict(list)
            for folder in folders:
                for path in sorted((self.root / folder).rglob("*.yml")):
                    source = self.yaml.load(path.read_text())
                    for name, definition in source.get("collections", {}).items():
                        title = str(definition.get("name", name)).casefold()
                        names[title].append(str(path.relative_to(self.root)))
            duplicates = {
                name: paths for name, paths in names.items() if len(paths) > 1
            }
            with self.subTest(library=library):
                self.assertFalse(duplicates, duplicates)

    def test_explicit_actors_excluded_from_dynamic_generation(self) -> None:
        """Reserve named actor collections before the dynamic actor limit is filled."""
        source = self.yaml.load(
            (self.root / "movies/actors-directors-writers.yml").read_text()
        )
        actors = source["dynamic_collections"]["Top Actors"]
        self.assertEqual(actors["type"], "actor")
        self.assertEqual(actors["title_format"], "<<title>> Collection")
        self.assertEqual(actors["data"], {"depth": 5, "minimum": 10, "limit": 200})
        reserved = set()
        for title, definition in source["collections"].items():
            call = definition["template"]
            self.assertEqual(call["name"], "person")
            self.assertEqual(title, f"{call['actor']} Collection")
            reserved.add(call["actor"])
        self.assertEqual(set(actors["exclude"]), reserved)
        self.assertEqual(len(actors["exclude"]), len(reserved))

    def test_kometa_actor_collision_and_limit(self) -> None:
        """Reproduce the collision and prove exclusions leave room for another actor."""
        #
        # Match Kometa's startup order to resolve the builder/Plex import cycle.
        #
        importlib.import_module("modules.builder")
        meta = importlib.import_module("modules.meta")
        source = self.yaml.load(
            (self.root / "movies/actors-directors-writers.yml").read_text()
        )
        actor_names = [
            definition["template"]["actor"]
            for definition in source["collections"].values()
        ] + ["Ray Liotta"]
        movie = SimpleNamespace(
            title="Fixture movie",
            actors=[
                SimpleNamespace(id=index, tag=name)
                for index, name in enumerate(actor_names)
            ],
        )
        library = SimpleNamespace(
            type="Movie",
            collections=[],
            get_all=lambda: [movie] * 10,
            reload=lambda item: item,
        )
        config = SimpleNamespace(Cache=None, requested_files=[])

        #
        # Exercise the pinned loader with synthetic credits and a one-slot dynamic limit.
        # All people templates are local, so the loader requires no external files.
        #
        for exclude_reserved in (False, True):
            with self.subTest(exclude_reserved=exclude_reserved):
                fixture = copy.deepcopy(source)
                actors = fixture["dynamic_collections"]["Top Actors"]
                actors["data"]["limit"] = 1
                if not exclude_reserved:
                    actors.pop("exclude")
                fixture["dynamic_collections"] = {"Top Actors": actors}
                logger = Mock()
                with (
                    patch.object(meta, "logger", logger),
                    patch.object(util, "logger", logger),
                    patch.object(meta.DataFile, "load_file", return_value=fixture),
                ):
                    loaded = meta.MetadataFile(
                        config, library, "File", "fixture.yml", {}, None, "collection"
                    )
                logger.error.assert_not_called()
                self.assertEqual(
                    "Ray Liotta Collection" in loaded.collections, exclude_reserved
                )
                for name, definition in source["collections"].items():
                    self.assertEqual(loaded.collections[name], definition)
                if exclude_reserved:
                    logger.warning.assert_not_called()
                    self.assertNotIn("Ray Liotta Collection", source["collections"])
                    call = loaded.collections["Ray Liotta Collection"]["template"]
                    calls = call if isinstance(call, list) else [call]
                    self.assertEqual(calls[0]["name"], "person_dynamic")
                    self.assertEqual(calls[0]["key"], "Ray Liotta")
                else:
                    self.assertTrue(
                        any(
                            "Skipping duplicate collection" in str(call)
                            for call in logger.warning.call_args_list
                        )
                    )

    #
    # Pre-rolls change a server-wide preference, so validate them without Plex access.
    #
    def test_preroll_structure(self) -> None:
        """Keep every pre-roll inside collections with schema-compatible schedules."""
        source = self.yaml.load(
            (self.root / "movies/seasonal-pre-rolls.yml").read_text()
        )
        self.assertEqual(set(source), {"collections"})
        self.assertEqual(
            set(source["collections"]),
            {
                "Weekly",
                "New Year",
                "Black History Month",
                "Valentine's Day",
                "Easter",
                "Pride Month",
                "Halloween",
                "Christmas",
            },
        )
        for name, definition in source["collections"].items():
            with self.subTest(collection=name):
                self.assertIs(definition["build_collection"], False)
                self.assertIsInstance(definition["schedule"], str)
                self.assertTrue(definition["server_preroll"])

    def test_preroll_calendar(self) -> None:
        """Check the complete annual rotation using Kometa's actual scheduler."""
        source = self.yaml.load(
            (self.root / "movies/seasonal-pre-rolls.yml").read_text()
        )
        windows = {
            "Weekly": ((301, 321), (426, 531), (701, 915)),
            "New Year": ((101, 115), (1226, 1231)),
            "Black History Month": ((201, 209), (215, 228)),
            "Valentine's Day": ((210, 214),),
            "Easter": ((322, 425),),
            "Pride Month": ((601, 630),),
            "Halloween": ((916, 1031),),
            "Christmas": ((1101, 1225),),
        }
        day = datetime(2026, 1, 1, tzinfo=UTC)
        while day.year == 2026:
            date_number = day.month * 100 + day.day
            active = []
            for name, definition in source["collections"].items():
                with self.subTest(collection=name, date=day.date()):
                    expected = any(
                        start <= date_number <= end for start, end in windows[name]
                    )
                    try:
                        util.schedule_check("schedule", definition["schedule"], day, 5)
                        actual = True
                    except util.NotScheduled:
                        actual = False
                    self.assertEqual(actual, expected)
                    if actual:
                        active.append(name)
            self.assertLessEqual(len(active), 1, day.date())
            day += timedelta(days=1)

    def test_shuffle_source_policy(self) -> None:
        """Keep random sampling separate from the post-filter 25-movie cap."""
        source = self.yaml.load((self.root / "movies/weekly-shuffle.yml").read_text())
        definition = source["collections"]["Weekly Shuffle"]
        template = source["templates"]["random"]
        self.assertEqual(template["limit"], 25)
        self.assertEqual(template["schedule"], "weekly(monday)")
        self.assertEqual(template["sync_mode"], "sync")
        self.assertEqual(
            definition["plex_search"],
            {
                "all": {"title.not": ["`", "Christmas", "Xmas"]},
                "sort_by": "random",
                "limit": 250,
            },
        )
        self.assertEqual(
            definition["filters"],
            {
                "tmdb_vote_average.gte": 6,
                "tmdb_vote_count.gte": 250,
                "tmdb_keyword.not": "christmas",
            },
        )

    #
    # Exercise the pinned provider evaluator, not a second implementation of its rules.
    #
    def test_shuffle_filter_boundaries(self) -> None:
        """Exclude Christmas and low-rated movies while accepting exact floors."""
        provider = object.__new__(TMDb)
        for rating, votes, keywords, expected in (
            (6, 250, [], True),
            (5.9, 250, [], False),
            (6, 249, [], False),
            (8, 10000, ["christmas"], False),
            (8, 10000, ["halloween"], True),
        ):
            with self.subTest(rating=rating, votes=votes, keywords=keywords):
                movie = SimpleNamespace(
                    vote_average=rating, vote_count=votes, keywords=keywords
                )
                checks = (
                    ("tmdb_vote_average", ".gte", 6),
                    ("tmdb_vote_count", ".gte", 250),
                    ("tmdb_keyword", ".not", ["christmas"]),
                )
                actual = all(
                    provider.item_filter(
                        movie, key, modifier, key + modifier, value, True, None
                    )
                    for key, modifier, value in checks
                )
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
