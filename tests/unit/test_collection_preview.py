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

    def check(self):
        """Evaluate the same guard used by the live preview entrypoint."""
        return preview.preview_names(self.franchises, self.config, self.smoke)

    def test_native_selection(self):
        selected, _ = preview.load_preview(Path("/workspace"))
        self.assertEqual(len(selected), 14)
        self.assertIn("The Purge Collection", selected)
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
                    preview.preview_names(self.franchises, config, self.smoke)

    def test_extra_library_behavior_rejected(self):
        for key in ("operations", "overlay_files", "settings"):
            with self.subTest(key=key):
                config = copy.deepcopy(self.config)
                config["libraries"]["test_movie_lib"][key] = {}
                with self.assertRaises(ValueError):
                    preview.preview_names(self.franchises, config, self.smoke)

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


if __name__ == "__main__":
    unittest.main()
