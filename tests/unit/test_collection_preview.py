#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_collection_preview.py: Offline regression tests for fixture isolation.
#

import copy
import importlib.util
import unittest
from pathlib import Path

from ruamel.yaml import YAML

spec = importlib.util.spec_from_file_location(
    "preview", "/scripts/collection-preview.py"
)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class CollectionPreviewTests(unittest.TestCase):
    """Reject unsafe preview inputs before any Plex connection is attempted."""

    def setUp(self):
        """Load fresh source data so each mutation test remains independent."""
        yaml = YAML(typ="safe")
        self.franchises = yaml.load(Path("/workspace/movies/franchise.yml").read_text())
        self.config = yaml.load(
            Path("/workspace/tests/kometa/collections-config.yml").read_text()
        )
        self.smoke = yaml.load(
            Path("/workspace/tests/kometa/collections.yml").read_text()
        )
        self.shows = yaml.load(Path("/workspace/shows/shuffle.yml").read_text())

    def check(self):
        """Evaluate the same guard used by the live preview entrypoint."""
        return preview.preview_names(
            self.franchises, self.config, self.smoke, self.shows
        )

    def test_native_selection(self):
        selected, _ = preview.load_preview(Path("/workspace"))
        self.assertEqual(len(selected), 18)
        self.assertIn("The Purge Collection", selected)
        self.assertIn("Adult Animation", selected)
        self.assertNotIn("After Collection", selected)

    def test_production_library_rejected(self):
        self.config["libraries"]["Movies"] = self.config["libraries"].pop(
            "test_movie_lib"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_library_alias_rejected(self):
        self.config["libraries"]["test_movie_lib"]["library_name"] = "Movies"
        with self.assertRaises(ValueError):
            self.check()

    def test_extra_service_rejected(self):
        for service in ("trakt", "radarr", "sonarr", "playlist_files", "webhooks"):
            with self.subTest(service=service):
                config = copy.deepcopy(self.config)
                config[service] = {}
                with self.assertRaises(ValueError):
                    preview.preview_names(
                        self.franchises, config, self.smoke, self.shows
                    )

    def test_extra_library_behavior_rejected(self):
        for key in ("operations", "overlay_files", "settings"):
            with self.subTest(key=key):
                config = copy.deepcopy(self.config)
                config["libraries"]["test_movie_lib"][key] = {}
                with self.assertRaises(ValueError):
                    preview.preview_names(
                        self.franchises, config, self.smoke, self.shows
                    )

    def test_deletion_rejected(self):
        self.config["settings"]["delete_below_minimum"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_maintenance_rejected(self):
        self.config["plex"]["empty_trash"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_plaintext_connection_rejected(self):
        self.config["plex"]["url"] = "http://localhost:32400"
        with self.assertRaises(ValueError):
            self.check()

    def test_plaintext_tmdb_key_rejected(self):
        #
        # This deliberately fake value exercises rejection, not authentication.
        #
        self.config["tmdb"]["apikey"] = "example"  # pragma: allowlist secret
        with self.assertRaises(ValueError):
            self.check()

    def test_external_templates_rejected(self):
        self.franchises["external_templates"] = [{"default": "templates"}]
        with self.assertRaises(ValueError):
            self.check()

    def test_only_owner_favorites_active(self):
        yaml = YAML(typ="safe")
        favorites = yaml.load(Path("/workspace/movies/favorites.yml").read_text())
        self.assertEqual(list(favorites["collections"]), ["Edward's Favorite Movies"])
        self.assertFalse(Path("/workspace/shows/favorites.yml").exists())

    def test_writer_in_template_rejected(self):
        self.franchises["templates"]["franchise"]["radarr_add_missing"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_writer_in_definition_rejected(self):
        self.franchises["collections"]["The Purge Collection"]["sync_to_trakt_list"] = (
            "example"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_custom_order_rejected(self):
        self.franchises["collections"]["The Purge Collection"]["collection_order"] = (
            "custom"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_boolean_id_rejected(self):
        self.franchises["collections"]["The Purge Collection"]["tmdb_collection"] = [
            True
        ]
        with self.assertRaises(ValueError):
            self.check()

    def test_template_override_rejected(self):
        self.franchises["collections"]["The Purge Collection"]["template"][
            "radarr_add_missing"
        ] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_smoke_writer_rejected(self):
        next(iter(self.smoke["collections"].values()))["radarr_add_missing"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_episode_expansion_rejected(self):
        self.shows["templates"]["shuffle"]["builder_level"] = "episode"
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_template_writer_rejected(self):
        self.shows["templates"]["shuffle"]["sonarr_add_missing"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_definition_writer_rejected(self):
        self.shows["collections"]["Adult Animation"]["sync_to_trakt_list"] = "example"
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_external_source_rejected(self):
        self.shows["templates"]["shuffle"]["trakt_list"] = (
            "https://trakt.tv/users/example/lists/<<list_slug>>"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_template_override_rejected(self):
        self.shows["collections"]["Adult Animation"]["template"]["list_slug"] = (
            "classic-sitcoms"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_invalid_ids_rejected(self):
        for ids in ([True], [0], [-1], ["60625"], [], [60625, 60625]):
            with self.subTest(ids=ids):
                self.shows["collections"]["Adult Animation"]["tmdb_show"] = ids
                with self.assertRaises(ValueError):
                    self.check()

    def test_tv_membership_counts(self):
        self.assertEqual(
            {
                name: len(definition["tmdb_show"])
                for name, definition in self.shows["collections"].items()
            },
            {
                "Adult Animation": 9,
                "Saturday Morning Cartoons": 21,
                "Classic Sitcoms": 9,
                "Modern Sitcoms": 10,
            },
        )

    def test_will_and_grace_combined_series(self):
        ids = self.shows["collections"]["Classic Sitcoms"]["tmdb_show"]
        self.assertIn(4454, ids)
        self.assertNotIn(74321, ids)

    def test_tv_id_comment_required(self):
        yaml = YAML()
        shows = yaml.load(Path("/workspace/shows/shuffle.yml").read_text())
        shows["collections"]["Adult Animation"]["tmdb_show"].ca.items.clear()
        with self.assertRaises(ValueError):
            preview.check_id_comments(shows["collections"], "tmdb_show")

    def test_successful_run_summary(self):
        for status in (
            "Created",
            "Unchanged",
            "Modified and Updated Image",
            "Created and Updated Metadata, Image",
            "Ignored",
            "Minimum 1 Not Met",
        ):
            with self.subTest(status=status):
                preview.check_run_summary(
                    f"| Adult Animation | 1 | 0 | 0 | 0:00:01 | {status} |",
                    ["Adult Animation"],
                )

    def test_failed_run_summary(self):
        for status in (
            "Service Error",
            "Kometa Failure",
            "Mapping/Conversion Error",
            "Unknown Error",
            "Not Scheduled",
        ):
            with self.subTest(status=status), self.assertRaises(ValueError):
                preview.check_run_summary(
                    f"| Adult Animation | 0 | 0 | 0 | 0:00:01 | {status} |",
                    ["Adult Animation"],
                )

    def test_incomplete_run_summary(self):
        with self.assertRaises(ValueError):
            preview.check_run_summary("No summary rows", ["Adult Animation"])

    def test_tv_movie_builder_rejected(self):
        self.shows["collections"]["Adult Animation"]["tmdb_movie"] = [1]
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_sources_only_wired_to_tv(self):
        yaml = YAML(typ="safe")
        config = yaml.load(Path("/workspace/config.yml").read_text())
        for setting in ("add_missing", "add_existing", "search"):
            self.assertIs(config["sonarr"][setting], False)
        self.assertIn(
            {"folder": "config/shows/"},
            config["libraries"]["TV Shows"]["collection_files"],
        )
        self.assertNotIn(
            {"folder": "config/shows/"},
            config["libraries"]["Movies"]["collection_files"],
        )

    def test_only_chronological_playlist_retained(self):
        yaml = YAML(typ="safe")
        source = yaml.load(Path("/workspace/playlists/playlists.yml").read_text())
        self.assertEqual(
            list(source["playlists"]), ["Battlestar Galactica (Timeline Order)"]
        )
        playlist = next(iter(source["playlists"].values()))
        self.assertEqual(playlist["libraries"], "Movies, TV Shows")
        self.assertEqual(
            playlist["trakt_list"],
            "https://trakt.tv/users/markmckee/lists/battlestar-galactica-chrono-order",
        )

    def test_radarr_override_only_for_weekly_chart(self):
        yaml = YAML(typ="safe")
        config = yaml.load(Path("/workspace/config.yml").read_text())
        chart = next(
            entry
            for entry in config["libraries"]["Movies"]["collection_files"]
            if entry.get("default") == "other_chart"
        )
        variables = chart["template_variables"]
        self.assertEqual(
            {
                key: value
                for key, value in variables.items()
                if key.startswith("radarr_")
            },
            {"radarr_add_missing_pirated": True, "radarr_search_pirated": True},
        )
        self.assertIs(config["radarr"]["add_missing"], False)
        self.assertIs(config["radarr"]["search"], False)

        #
        # Check the pinned Defaults contract, not just arbitrary variable names.
        #
        defaults = yaml.load(Path("/defaults/chart/other_chart.yml").read_text())
        pirated = defaults["collections"]["Top 10 Pirated Movies of the Week"]
        self.assertEqual(pirated["variables"]["key"], "pirated")
        self.assertIn({"name": "arr"}, pirated["template"])
        shared = yaml.load(Path("/defaults/templates.yml").read_text())
        arr = shared["templates"]["arr"]
        self.assertEqual(arr["radarr_add_missing"], "<<radarr_add_missing_<<key>>>>")
        self.assertEqual(arr["radarr_search"], "<<radarr_search_<<key>>>>")


if __name__ == "__main__":
    unittest.main()
