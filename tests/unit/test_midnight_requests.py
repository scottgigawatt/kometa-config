#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_midnight_requests.py: Verify scoped Arr requests and complete parent-series coverage.
#

"""Exercise request policies through pinned Kometa parsers and mocked Arr transports."""

import importlib
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML


class MidnightRequestTests(unittest.TestCase):
    """Request new selections while preserving episode safety and Arr quality settings."""

    def setUp(self) -> None:
        """Read public definitions and load the pinned runtime without connecting services."""
        self.builder = importlib.import_module("modules.builder")
        self.sonarr = importlib.import_module("modules.sonarr")
        self.root = Path("/workspace")
        yaml = YAML()
        self.tv = yaml.load((self.root / "shows/midnight-cinema.yml").read_text())
        self.requests = yaml.load(
            (self.root / "shows/midnight-series-requests.yml").read_text()
        )
        self.movies = yaml.load((self.root / "movies/midnight-curated.yml").read_text())
        self.helper = self.requests["collections"]["Midnight Cinema Series Requests"]
        self.expected_sonarr = {
            "add_missing": True,
            "add_existing": True,
            "monitor": "all",
            "monitor_existing": True,
            "search": True,
            "ignore_cache": True,
            "upgrade_existing": False,
            "cutoff_search": False,
        }

    def test_request_values_parse_with_the_pinned_arr_handlers(self) -> None:
        """Use Kometa's parsers to verify new requests retain the configured quality defaults."""
        for definition in (
            self.helper,
            self.tv["collections"]["Weekend Miniseries"],
        ):
            parser = self.builder.CollectionBuilder.__new__(
                self.builder.CollectionBuilder
            )
            parser.Type = "Collection"
            parser.sonarr_details = {}
            for key, value in definition.items():
                if key.startswith("sonarr_"):
                    parser._sonarr(key, value)
            self.assertEqual(parser.sonarr_details, self.expected_sonarr)

        parser.radarr_details = {}
        for template in self.movies["templates"].values():
            for key, value in template.items():
                if key.startswith("radarr_"):
                    parser._radarr(key, value)
        self.assertEqual(
            parser.radarr_details,
            {
                "add_missing": True,
                "add_existing": False,
                "search": True,
                "monitor": True,
                "monitor_existing": True,
                "ignore_cache": True,
                "upgrade_existing": False,
            },
        )

    def test_parent_requests_cover_all_episode_candidates_and_arcs(self) -> None:
        """Missing episodes must not prevent their parent series from entering Sonarr."""
        self.assertEqual(self.helper["builder_level"], "show")
        self.assertIs(self.helper["build_collection"], False)
        self.assertEqual(self.helper["sync_mode"], "append")
        self.assertNotIn("file_poster", self.helper)
        self.assertNotIn("plex_search", self.helper)
        ids = self.helper["tvdb_show"]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        names = set()
        for index, identifier in enumerate(ids):
            self.assertIs(type(identifier), int)
            self.assertGreater(identifier, 0)
            comment = ids.ca.items[index][0].value.strip("# \n")
            match = re.fullmatch(r"(.+) \((\d{4})\)", comment)
            self.assertIsNotNone(match)
            if match:
                names.add(match.group(1))
        candidates = set()
        for query in self.tv["collections"]["TV's Greatest Episodes"]["plex_search"]:
            conditions = query["all"]
            title = conditions.get("title.is")
            candidates.add(title if title else conditions["any"]["title.is"][0])
        self.assertEqual(names, candidates)
        arc_parents = {
            int(entry.split(":")[1].split("_")[0])
            for definition in self.tv["collections"].values()
            for entry in definition.get("text", [])
        }
        self.assertTrue(arc_parents)
        self.assertLessEqual(arc_parents, set(ids))

    def test_episode_collections_never_inherit_sonarr_writers(self) -> None:
        """Sonarr requests must remain whole-show operations supported by Kometa."""
        for name, definition in self.tv["collections"].items():
            if definition["builder_level"] != "episode":
                continue
            with self.subTest(collection=name):
                template = self.tv["templates"][definition["template"]["name"]]
                effective = {**template, **definition}
                self.assertFalse(any(key.startswith("sonarr_") for key in effective))
        self.assertTrue(
            {f"sonarr_{key}" for key in self.expected_sonarr}.isdisjoint(
                self.builder.parts_collection_valid
            )
        )

    def test_sonarr_adds_search_new_series_and_remonitor_cached_existing_series(
        self,
    ) -> None:
        """Test the actual adapter's new-search behavior and existing-series search limitation."""
        existing_id, new_id = self.helper["tvdb_show"][:2]
        existing = SimpleNamespace(
            tvdbId=existing_id, title="Existing", path="/series/existing"
        )
        new = SimpleNamespace(tvdbId=new_id, title="New", folder="new")
        adapter = self.sonarr.Sonarr.__new__(self.sonarr.Sonarr)
        adapter.api = Mock()
        adapter.api._raw.v3 = True
        adapter.api.all_series.return_value = [existing]
        adapter.api.get_series.return_value = new
        adapter.api.add_multiple_series.return_value = ([new], [], [], [])
        adapter.cache = Mock()
        adapter.library = SimpleNamespace(original_mapping_name="Fixture")
        adapter.root_folder_path = "/series"
        adapter.quality_profile = "Existing quality profile"
        adapter.language_profile = "Existing language profile"
        adapter.series_type = "standard"
        adapter.season_folder = True
        adapter.tag = []
        adapter.profiles = []

        #
        # Existing IDs must bypass Kometa's addition cache so monitoring reaches Sonarr.
        # The adapter passes search only to new additions, not to existing-series edits.
        #
        with patch.object(self.sonarr, "logger", Mock()):
            added = adapter.add_tvdb([existing_id, new_id], **self.expected_sonarr)
        self.assertEqual(added, [new])
        adapter.cache.query_sonarr_adds.assert_not_called()
        args, kwargs = adapter.api.add_multiple_series.call_args
        self.assertEqual(args[0], [new])
        self.assertEqual(
            args[1:6],
            (
                "/series",
                "Existing quality profile",
                "Existing language profile",
                "all",
                True,
            ),
        )
        self.assertIs(args[6], True)
        self.assertIs(args[7], False)
        self.assertEqual(kwargs, {"per_request": 100})
        adapter.api.edit_multiple_series.assert_called_once_with(
            [existing_id], monitor="all"
        )
        self.assertEqual(
            [call[0] for call in adapter.api.mock_calls],
            ["all_series", "get_series", "add_multiple_series", "edit_multiple_series"],
        )


if __name__ == "__main__":
    unittest.main()
