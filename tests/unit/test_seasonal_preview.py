#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_seasonal_preview.py: Guard holiday membership and download-free previews.
#
# Purpose: Preserve holiday presentation and reject external writers or lists.
# Usage: Run through make validate inside the pinned Kometa image.
#

"""Check seasonal sources and preview boundaries without external services."""

import copy
import importlib.util
import unittest
from pathlib import Path

from ruamel.yaml import YAML

#
# Load the container-mounted guard without invoking its live preview entrypoint.
#
spec = importlib.util.spec_from_file_location(
    "preview", "/scripts/collection-preview.py"
)
if spec is None or spec.loader is None:
    raise ImportError("The container must mount /scripts/collection-preview.py.")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class SeasonalPreviewTests(unittest.TestCase):
    """Keep holiday sources native and their test runs isolated from downloads."""

    def setUp(self) -> None:
        """Load fresh round-trip YAML so ID comment checks remain meaningful."""
        yaml = YAML()
        self.source = yaml.load(Path("/workspace/scheduled/seasonal.yml").read_text())
        self.config = yaml.load(Path("/workspace/config.yml").read_text())

    #
    # Lock the approved seasonal boundaries without retaining remote user lists.
    #
    def test_all_holidays_selected(self) -> None:
        """Select all thirteen holidays, including the newly populated Irish set."""
        names = preview.seasonal_names(self.source)
        self.assertEqual(len(names), 13)
        self.assertIn("St. Patrick's Day Movies", names)

    def test_irish_and_holiday_keywords(self) -> None:
        """Include Irish settings and culture alongside St. Patrick's Day."""
        ids = self.source["collections"]["St. Patrick's Day Movies"]["tmdb_keyword"]
        self.assertEqual(
            set(ids),
            {14985, 7005, 4729, 299594, 232483, 232529, 301981, 301982, 209352},
        )

    def test_christmas_company_queries(self) -> None:
        """Intersect Christmas tagging with the reviewed production company IDs."""
        expected = {
            "Hallmark Christmas Movies": "4056|6435|53015|9027",
            "Lifetime Christmas Movies": "3431|21935|6709",
            "Rankin/Bass Christmas Movies": "688|8813",
        }
        for name, companies in expected.items():
            with self.subTest(name=name):
                query = self.source["collections"][name]["tmdb_discover"]
                self.assertEqual(query["with_keywords"], "207317")
                self.assertEqual(query["with_companies"], companies)
                self.assertEqual(query["limit"], 0)

    def test_vintage_date_cannot_drift(self) -> None:
        """Keep vintage films through 1979 rather than using a moving age window."""
        query = self.source["collections"]["Vintage Christmas Movies"]["tmdb_discover"]
        self.assertEqual(query["primary_release_date.lte"], "12/31/1979")
        query["primary_release_date.lte"] = "12/31/1999"
        with self.assertRaises(ValueError):
            preview.seasonal_names(self.source)

    def test_christmas_exclusions_preserved(self) -> None:
        """Preserve the nine explicit exclusions from the broad Christmas set."""
        self.assertEqual(
            self.source["collections"]["Christmas Movies"]["filters"]["title.not"],
            [
                "Lethal Weapon",
                "The Ice Harvest",
                "Life with Mikey",
                "Two Night Stand",
                "Brazil",
                "Spencer",
                "Iron Man 3",
                "Planes, Trains & Automobiles",
                "Kiss Kiss Bang Bang",
            ],
        )

    def test_defaults_do_not_duplicate_custom_holidays(self) -> None:
        """Keep the eight custom holiday groups excluded from Kometa Defaults."""
        entry = next(
            item
            for item in self.config["libraries"]["Movies"]["collection_files"]
            if item.get("default") == "seasonal"
        )
        self.assertEqual(
            set(entry["template_variables"]["exclude"]),
            {
                "christmas",
                "easter",
                "halloween",
                "mother",
                "patrick",
                "thanksgiving",
                "valentine",
                "years",
            },
        )

    #
    # Reject every source of download behavior, not just the missing-item flag.
    #
    def test_template_downloads_rejected(self) -> None:
        """Require all Radarr creation, search, and existing-item flags to stay off."""
        for key in (
            "radarr_add_missing",
            "radarr_add_existing",
            "radarr_search",
            "radarr_upgrade_existing",
            "radarr_monitor_existing",
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.source)
                changed["templates"]["seasonal"][key] = True
                with self.assertRaises(ValueError):
                    preview.seasonal_names(changed)

    def test_collection_writers_and_external_lists_rejected(self) -> None:
        """Reject collection-level overrides even when the shared template is safe."""
        for key in (
            "radarr_add_missing",
            "radarr_add_existing",
            "radarr_search",
            "trakt_list",
            "letterboxd_list",
            "imdb_list",
            "sync_to_trakt_list",
            "item_label",
            "delete_not_scheduled",
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.source)
                changed["collections"]["Christmas Movies"][key] = True
                with self.assertRaises(ValueError):
                    preview.seasonal_names(changed)

    def test_external_templates_rejected(self) -> None:
        """Reject remote templates before they can inject additional behavior."""
        self.source["external_templates"] = [{"default": "templates"}]
        with self.assertRaises(ValueError):
            preview.seasonal_names(self.source)

    def test_template_variable_overrides_rejected(self) -> None:
        """Prevent collection variables from bypassing preview deletion controls."""
        self.source["collections"]["Christmas Movies"]["template"][
            "delete_not_scheduled"
        ] = True
        with self.assertRaises(ValueError):
            preview.seasonal_names(self.source)

    def test_fixture_projection_required(self) -> None:
        """Require the guarded copy instead of loading seasonal source directly."""
        yaml = YAML()
        config = yaml.load(
            Path("/workspace/tests/kometa/collections-config.yml").read_text()
        )
        seasonal = next(
            entry
            for entry in config["libraries"]["test_movie_lib"]["collection_files"]
            if entry["file"] == "/config/seasonal.yml"
        )
        seasonal["file"] = "/workspace/scheduled/seasonal.yml"
        with self.assertRaises(ValueError):
            preview.preview_names(
                yaml.load(Path("/workspace/movies/franchise.yml").read_text()),
                config,
                yaml.load(Path("/workspace/tests/kometa/collections.yml").read_text()),
                yaml.load(Path("/workspace/shows/shuffle.yml").read_text()),
            )

    def test_projection_changes_only_disabled_integration_and_deletion(self) -> None:
        """Preserve builders and presentation while removing fixture side effects."""
        original = copy.deepcopy(self.source)
        expected = copy.deepcopy(self.source)
        template = expected["templates"]["seasonal"]
        for key in (
            "radarr_add_missing",
            "radarr_add_existing",
            "radarr_search",
            "radarr_upgrade_existing",
            "radarr_monitor_existing",
        ):
            self.assertIs(template.pop(key), False)
        template["delete_not_scheduled"] = False
        self.assertEqual(preview.seasonal_preview(self.source), expected)
        self.assertEqual(self.source, original)

    def test_projection_does_not_hide_enabled_downloads(self) -> None:
        """Reject unsafe source instead of silently sanitizing an enabled writer."""
        self.source["templates"]["seasonal"]["radarr_search"] = True
        with self.assertRaises(ValueError):
            preview.seasonal_preview(self.source)

    #
    # Keep query IDs readable and prevent silent truncation or unrelated sources.
    #
    def test_invalid_keyword_ids_rejected(self) -> None:
        """Reject empty, duplicate, boolean, string, or nonpositive keyword IDs."""
        for ids in ([], [True], [0], [-1], ["613"], [613, 613]):
            with self.subTest(ids=ids):
                changed = copy.deepcopy(self.source)
                changed["collections"]["New Year's Eve Movies"]["tmdb_keyword"] = ids
                with self.assertRaises(ValueError):
                    preview.seasonal_names(changed)

    def test_missing_keyword_comment_rejected(self) -> None:
        """Require readable names beside each explicit seasonal keyword ID."""
        ids = self.source["collections"]["Easter Movies"]["tmdb_keyword"]
        ids.ca.items.clear()
        with self.assertRaisesRegex(ValueError, "comment"):
            preview.seasonal_names(self.source)

    def test_missing_discover_comment_rejected(self) -> None:
        """Require named IDs beside discovery keywords and company combinations."""
        query = self.source["collections"]["Hallmark Christmas Movies"]["tmdb_discover"]
        query.ca.items.clear()
        with self.assertRaisesRegex(ValueError, "comment"):
            preview.seasonal_names(self.source)

    def test_discovery_overrides_rejected(self) -> None:
        """Reject result caps and additional discovery filters in the preview."""
        for key, value in (("limit", 100), ("limit", False), ("with_cast", "1")):
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(self.source)
                changed["collections"]["Christmas Movies"]["tmdb_discover"][key] = value
                with self.assertRaises(ValueError):
                    preview.seasonal_names(changed)


#
# Support direct execution inside the isolated validation container.
#
if __name__ == "__main__":
    unittest.main()
