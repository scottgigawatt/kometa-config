#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_collection_sources.py: Protect readable provider IDs and intentional source choices.
#

"""Check collection source contracts without contacting metadata providers."""

import importlib
import unittest
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import urlsplit

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
        """Use six available ceremonies without requesting unpublished future years."""
        source = self.yaml.load(
            (self.root / "scheduled/critics-choice.yml").read_text()
        )
        dynamic = source["dynamic_collections"]["Critics Choice Awards"]
        self.assertEqual(dynamic["type"], "imdb_awards")
        self.assertEqual(
            dynamic["data"],
            {"event_id": "ev0000133", "starting": "latest-5", "ending": "latest"},
        )
        self.assertIn("choice_award_year", dynamic["template"])
        self.assertNotIn("trakt", dynamic["template"])
        self.assertNotIn("url", dynamic["template_variables"])
        self.assertEqual(
            source["templates"]["choice_award_year"],
            {
                "imdb_award": {
                    "event_id": "ev0000133",
                    "event_year": "<<key>>",
                    "winning": True,
                }
            },
        )

    def test_critics_choice_best_picture_uses_award_records(self) -> None:
        """Select only Best Picture winners across every available ceremony."""
        source = self.yaml.load(
            (self.root / "scheduled/critics-choice.yml").read_text()
        )
        collection = source["collections"]["Critics Choice Best Picture Winners"]
        self.assertEqual(
            collection["imdb_award"],
            {
                "event_id": "ev0000133",
                "event_year": "all",
                "category_filter": "best picture",
                "winning": True,
            },
        )

    def test_golden_globe_categories_cover_historical_film_names(self) -> None:
        """Include old film category names without television or foreign-film awards."""
        source = self.yaml.load((self.root / "scheduled/golden-globes.yml").read_text())
        expected = {
            "Golden Globes Best Picture Winners": {
                "best picture",
                "best motion picture - drama",
                "best motion picture - comedy",
                "best motion picture - musical",
                "best motion picture - comedy or musical",
                "best motion picture - musical or comedy",
                "best motion picture, musical or comedy",
                "best animated feature film",
                "best animated film",
                "best motion picture - animated",
            },
            "Golden Globes Best Director Winners": {
                "best director",
                "best director - motion picture",
            },
        }
        for name, categories in expected.items():
            with self.subTest(collection=name):
                award = source["collections"][name]["imdb_award"]
                self.assertEqual(award["event_id"], "ev0000292")
                self.assertEqual(award["event_year"], "all")
                self.assertIs(award["winning"], True)
                self.assertEqual(set(award["category_filter"]), categories)
                self.assertEqual(len(award["category_filter"]), len(categories))

    def test_custom_collections_do_not_depend_on_personal_lists(self) -> None:
        """Allow only the owner's favorites, excluding deferred upstream Defaults."""

        #
        # Inspect nested templates too; yearly URLs need not appear on collections.
        # Playlists and upstream Defaults have separate source policies.
        #
        def check(value: object, path: Path) -> None:
            """Reject third-party list URLs and builders at any nesting depth."""
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"trakt_list", "letterboxd_list"}:
                        self.assertEqual(path.name, "edwards-favorites.yml")
                        self.assertEqual(
                            child,
                            [
                                (
                                    "https://trakt.tv/users/scottgigawatt/"
                                    "lists/plex-favorite-movies"
                                )
                            ],
                        )
                    check(child, path)
            elif isinstance(value, list):
                for child in value:
                    check(child, path)
            elif isinstance(value, str) and value.startswith(("https://", "http://")):
                url = urlsplit(value)
                personal_trakt = url.hostname in {
                    "trakt.tv",
                    "www.trakt.tv",
                    "app.trakt.tv",
                } and url.path.startswith("/users/")
                letterboxd = url.hostname in {"letterboxd.com", "www.letterboxd.com"}
                if personal_trakt or letterboxd:
                    self.assertEqual(path.name, "edwards-favorites.yml")
                    self.assertEqual(
                        value,
                        "https://trakt.tv/users/scottgigawatt/lists/plex-favorite-movies",
                    )

        for folder in ("movies", "shows", "scheduled"):
            for path in (self.root / folder).glob("*.yml"):
                with self.subTest(file=path.name):
                    check(self.yaml.load(path.read_text()), path)

        #
        # TMDb lists are also user-maintained; do not reintroduce them for awards.
        #
        for filename in ("critics-choice.yml", "golden-globes.yml"):
            self.assertNotIn(
                "tmdb_list:", (self.root / "scheduled" / filename).read_text()
            )

    def test_native_award_selector_excludes_nominees_and_unrelated_categories(
        self,
    ) -> None:
        """Exercise Kometa's selector with winners, nominees, and unrelated awards."""
        #
        # Kometa modules exist in the pinned container, not the editor environment.
        #
        imdb = importlib.import_module("modules.imdb")

        for filename in ("critics-choice.yml", "golden-globes.yml"):
            source = self.yaml.load((self.root / "scheduled" / filename).read_text())
            for name, collection in source["collections"].items():
                with self.subTest(collection=name):
                    award = dict(collection["imdb_award"])
                    categories = award["category_filter"]
                    if isinstance(categories, str):
                        categories = [categories]
                    award["category_filter"] = categories
                    award["award_filter"] = []

                    #
                    # Each historical category must retain its winner, not nominees.
                    # A television category must not enter the all-time film awards.
                    #
                    expected = [f"tt{index:07}" for index in range(len(categories))]
                    records = {
                        category: {"winner": [winner], "nominee": ["tt9000000"]}
                        for category, winner in zip(categories, expected, strict=True)
                    }
                    records["best television series - drama"] = {
                        "winner": ["tt9000001"],
                        "nominee": ["tt9000002"],
                    }
                    client = imdb.IMDb.__new__(imdb.IMDb)
                    client._git_events_validation = {
                        award["event_id"]: {"years": ["2026"]}
                    }
                    client.get_event_data = Mock(return_value={"award": records})
                    self.assertEqual(client._award(award), expected)


if __name__ == "__main__":
    unittest.main()
