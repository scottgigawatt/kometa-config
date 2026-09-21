#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_trakt_removal.py: Protect owned membership and Trakt-free runtime inputs.
#

"""Check source independence and parse ordered IDs with the pinned runtime."""

import unittest
from pathlib import Path
from unittest.mock import Mock

from modules.textfile import TextFile
from ruamel.yaml import YAML


class TraktRemovalTests(unittest.TestCase):
    """Keep retired integrations out of authored configuration and key Defaults."""

    def setUp(self) -> None:
        """Read only the public YAML snapshot supplied by the validator."""
        self.root = Path("/workspace")
        self.yaml = YAML()

    def assert_no_trakt(self, value: object) -> None:
        """Reject connection keys, nested builders, rating sources, and list URLs.

        Args:
            value: A parsed YAML document or one of its nested values.

        Raises:
            AssertionError: If a key or string still references Trakt.
        """
        if isinstance(value, dict):
            for key, child in value.items():
                self.assert_no_trakt(key)
                self.assert_no_trakt(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_no_trakt(child)
        elif isinstance(value, str):
            self.assertNotIn("trakt", value.lower())

    #
    # Validate nested templates as well as directly declared collection builders.
    # Negative examples keep future edits from weakening this source boundary.
    #
    def test_authored_runtime_inputs(self) -> None:
        """Reject Trakt dependencies in production definitions and fixture YAML."""
        paths = [self.root / "config.yml"]
        for folder in (
            "movies",
            "shows",
            "scheduled",
            "playlists",
            "overlays",
            "tests/kometa",
        ):
            paths.extend((self.root / folder).rglob("*.yml"))
            paths.extend((self.root / folder).rglob("*.yaml"))
        for path in paths:
            with self.subTest(file=str(path.relative_to(self.root))):
                self.assert_no_trakt(self.yaml.load(path.read_text()))

    def test_nested_dependencies_rejected(self) -> None:
        """Catch removed features even when hidden in defaults or template variables."""
        for definition in (
            {"trakt": {}},
            {"default": "trakt"},
            {"operations": [{"mass_user_rating_update": "trakt_user"}]},
            {"templates": {"shared": {"sync_to_trakt_list": "example"}}},
            {"text_file": "https://trakt.tv/users/example/lists/movies"},
        ):
            with self.subTest(definition=definition), self.assertRaises(AssertionError):
                self.assert_no_trakt(definition)

    def test_pinned_universe_and_playlist_defaults(self) -> None:
        """Require the retained upstream universe and playlist sources to be Trakt-free."""
        for filename in ("both/universe.yml", "playlist.yml"):
            with self.subTest(file=filename):
                self.assert_no_trakt(
                    self.yaml.load((Path("/defaults") / filename).read_text())
                )

    def test_favorites_are_named_unique_movie_ids(self) -> None:
        """Preserve every snapshotted favorite and its explicit download behavior."""
        source = self.yaml.load(
            (self.root / "movies/edwards-favorites.yml").read_text()
        )
        ids = source["collections"]["Edward's Favorite Movies"]["tmdb_movie"]
        self.assertEqual(len(ids), 96)
        self.assertEqual(len(set(ids)), len(ids))
        for index, identifier in enumerate(ids):
            with self.subTest(identifier=identifier):
                self.assertIs(type(identifier), int)
                self.assertGreater(identifier, 0)
                self.assertTrue(ids.ca.items[index][0].value.strip(" #\n"))
        template = source["templates"]["favorites"]
        self.assertIs(template["radarr_add_missing"], True)
        self.assertIs(template["radarr_search"], True)

    def test_battlestar_sequence_parses_without_network_access(self) -> None:
        """Preserve the exact Plex snapshot order using portable episode and movie IDs."""
        source = self.yaml.load(
            (self.root / "playlists/battlestar-galactica-timeline.yml").read_text()
        )
        playlist = source["playlists"]["Battlestar Galactica (Timeline Order)"]

        #
        # Protect movie placement between seasons, not just the number of entries.
        # No specials or absent items are guessed from the show's total episode count.
        #
        expected = [(f"85040_1_{episode}", "tvdb_episode") for episode in range(1, 19)]
        for season, count in ((1, 13), (2, 20)):
            expected.extend(
                (f"73545_{season}_{episode}", "tvdb_episode")
                for episode in range(1, count + 1)
            )
        expected.extend([("tt0991178", "imdb"), ("tt1286130", "imdb")])
        for season in (3, 4):
            expected.extend(
                (f"73545_{season}_{episode}", "tvdb_episode")
                for episode in range(1, 21)
            )
        requests = Mock()
        actual = TextFile(requests).get_text_ids(list(playlist["text"]))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 93)
        self.assertEqual(len(set(actual)), len(actual))
        self.assertEqual(requests.mock_calls, [])
        self.assertEqual(playlist["sync_mode"], "sync")
        self.assertEqual(playlist["sync_to_users"], "all")


#
# Support direct execution with the same pinned runtime and public source mounts.
#
if __name__ == "__main__":
    unittest.main()
