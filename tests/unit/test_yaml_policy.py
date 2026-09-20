#!/usr/bin/env python3

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_yaml_policy.py: Protect YAML comments, shuffle eligibility, and Arr monitoring.
#

"""Check repository YAML conventions and the movie shuffle's selection policy."""

import re
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

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

    def test_subgenre_inline_spacing(self) -> None:
        """Separate subgenre ID comments by exactly two spaces without alignment."""
        source = (self.root / "movies/subgenre-top.yml").read_text()
        lines = [
            line
            for line in source.splitlines()
            if re.match(r"\s+(keywords|genres|excluded_keywords):", line)
        ]
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line):
                self.assertRegex(line, r'^\s+\w+: "[0-9|,]+"  # \S')

    def test_existing_arr_monitoring_disabled(self) -> None:
        """Leave existing movie and episode monitoring under Radarr and Sonarr control."""
        config = self.yaml.load((self.root / "config.yml").read_text())
        for service in ("radarr", "sonarr"):
            with self.subTest(service=service):
                self.assertIs(config[service]["monitor_existing"], False)

    #
    # Pre-rolls change a server-wide preference, so validate them without Plex access.
    #
    def test_preroll_structure(self) -> None:
        """Keep every pre-roll inside collections with schema-compatible schedules."""
        source = self.yaml.load((self.root / "movies/pre-roll.yml").read_text())
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
        source = self.yaml.load((self.root / "movies/pre-roll.yml").read_text())
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
        source = self.yaml.load((self.root / "movies/shuffle.yml").read_text())
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
