#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_collection_sources.py: Protect readable provider IDs and intentional source choices.
#

"""Check collection source contracts without contacting metadata providers."""

import unittest
from pathlib import Path

from ruamel.yaml import YAML


class CollectionSourceTests(unittest.TestCase):
    """Keep verified IDs documented and retired network matches out of builders."""

    def setUp(self) -> None:
        """Use the tracked YAML snapshot supplied by the offline validator."""
        self.root = Path("/workspace")
        self.yaml = YAML()

    def test_beverly_hills_uses_native_collection(self) -> None:
        """Enable the four-film franchise in release order with its existing poster."""
        source = self.yaml.load((self.root / "movies/franchises.yml").read_text())
        collection = source["collections"]["Beverly Hills Cop Collection"]
        self.assertEqual(collection["tmdb_collection"], [85861])
        self.assertEqual(
            collection["template"],
            {"name": "franchise", "poster_id": "Beverly Hills Cop"},
        )
        self.assertNotIn("plex_search", collection)
        self.assertEqual(
            source["templates"]["franchise"]["collection_order"], "release"
        )

    def test_networks_use_documented_live_ids(self) -> None:
        """Keep explicit ID lists, descriptive comments, and approved mismatch removals."""
        source = self.yaml.load((self.root / "shows/networks.yml").read_text())
        removed = {
            2193,
            2693,
            3917,
            5479,
            5484,
            5485,
            5666,
            5687,
            5750,
            5764,
            5836,
            7072,
            2919,
            505,
            1074,
            4383,
        }
        for name, definition in source["collections"].items():
            with self.subTest(collection=name):
                ids = definition["template"]["network"]
                self.assertIsInstance(ids, list)
                self.assertTrue(ids)
                self.assertEqual(len(ids), len(set(ids)))
                self.assertFalse(set(ids) & removed)
                for index, value in enumerate(ids):
                    self.assertIs(type(value), int)
                    self.assertTrue(ids.ca.items[index][0].value.strip("# \n"))
        self.assertEqual(
            source["collections"]["Disney+"]["template"]["network"], [2739]
        )
        self.assertEqual(
            source["collections"]["Max"]["template"]["network"], [6783, 3186]
        )

    def test_numeric_tmdb_builders_have_comments(self) -> None:
        """Require individual documented IDs in custom collection builder lists."""
        keys = {
            "tmdb_list",
            "tmdb_collection",
            "tmdb_show",
            "tmdb_movie",
            "tmdb_keyword",
        }

        def check(value: object) -> None:
            """Visit YAML maps and sequences without interpreting template placeholders."""
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in keys and isinstance(child, (int, list)):
                        self.assertIsInstance(child, list)
                        for index, item in enumerate(child):
                            if isinstance(item, int):
                                self.assertTrue(
                                    child.ca.items.get(index),
                                    f"Missing comment for {key} ID {item}",
                                )
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        for folder in ("movies", "shows", "scheduled", "playlists"):
            for path in (self.root / folder).glob("*.yml"):
                with self.subTest(file=path.name):
                    check(self.yaml.load(path.read_text()))

    def test_critics_choice_window_rolls_automatically(self) -> None:
        """Keep six years without confusing historical URL spellings with selection."""
        source = self.yaml.load(
            (self.root / "scheduled/critics-choice.yml").read_text()
        )
        dynamic = source["dynamic_collections"]["Critics Choice Awards"]
        self.assertEqual(
            dynamic["data"], {"starting": "current_year-5", "ending": "current_year"}
        )
        self.assertEqual(dynamic["template_variables"]["url"], {"default": "critic-s"})


if __name__ == "__main__":
    unittest.main()
