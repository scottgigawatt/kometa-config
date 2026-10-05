#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_run_warnings.py: Verify scoped warning workarounds against pinned Kometa.
#

"""Exercise configuration overrides without contacting Plex or external providers."""

import copy
import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML


class RunWarningTests(unittest.TestCase):
    """Keep source exclusions and notification overrides local to their definitions."""

    def setUp(self) -> None:
        """Load public configuration and the actual pinned runtime modules."""
        self.yaml = YAML(typ="safe")
        self.config = self.yaml.load(Path("/workspace/config.yml").read_text())
        self.builder = importlib.import_module("modules.builder")
        self.meta = importlib.import_module("modules.meta")
        self.variables = next(
            entry["template_variables"]
            for entry in self.config["libraries"]["Movies"]["collection_files"]
            if entry.get("default") == "letterboxd"
        )

    def test_defaults_expand_chart_overrides(self) -> None:
        """Apply the actual Defaults template to verify exclusions and Top 500 visibility."""
        shared = self.yaml.load(Path("/defaults/templates.yml").read_text())
        chart = self.yaml.load(Path("/defaults/chart/letterboxd.yml").read_text())
        data = self.meta.DataFile.__new__(self.meta.DataFile)
        data.templates = {
            name: (definition, {}) for name, definition in shared["templates"].items()
        }
        data.temp_vars = self.variables
        data.data_type = "Collection"
        data.library = SimpleNamespace(type="Movie", name="Fixture movies")
        collection = chart["collections"]["Letterboxd Top 500"]
        with patch.object(self.meta, "logger", Mock()):
            result = data.apply_template(
                None,
                "Letterboxd Top 500",
                {},
                [{"name": "shared"}],
                copy.deepcopy(collection["variables"]),
            )
        self.assertEqual(result["ignore_ids"], [712168, 753972, 1016041, 1567451])
        for key in ("visible_library", "visible_home", "visible_shared"):
            self.assertIs(result[key], True)
        self.assertNotIn("ignore_ids", self.config["settings"])
        self.assertNotIn("ignore_ids", self.config["libraries"]["TV Shows"]["settings"])

    def test_unresolved_movies_do_not_enter_missing_lookup(self) -> None:
        """Skip only reviewed movie IDs while retaining an unrelated missing movie."""
        builder = self.builder.CollectionBuilder.__new__(self.builder.CollectionBuilder)
        builder.ignore_ids = self.variables["ignore_ids"]
        builder.parts_collection = False
        builder.libraries = [SimpleNamespace(movie_map={})]
        builder.missing_movies = []
        builder._log_episode_count = Mock()
        ids = [(value, "tmdb") for value in builder.ignore_ids] + [(11, "tmdb")]
        with patch.object(self.builder, "logger", Mock()) as logger:
            builder.filter_and_save_items(ids)
        self.assertEqual(builder.missing_movies, [11])
        logger.error.assert_not_called()

    def test_star_wars_defaults_skip_unresolved_missing_movie(self) -> None:
        """Render pinned Defaults and skip the bad record without dropping a valid movie."""
        shared = self.yaml.load(Path("/defaults/templates.yml").read_text())
        playlists = self.yaml.load(Path("/defaults/playlist.yml").read_text())
        universe = next(
            entry["template_variables"]
            for entry in self.config["libraries"]["Movies"]["collection_files"]
            if entry.get("default") == "universe"
        )
        playlist = next(
            entry["template_variables"]
            for entry in self.config["playlist_files"]
            if entry.get("default") == "playlist"
        )

        #
        # Exercise each actual Defaults template before testing missing-item selection.
        # The exclusion belongs to these files, never the global or library settings.
        #
        cases = (
            ("Collection", universe, shared, "shared", {"key": "star"}),
            ("Playlist", playlist, playlists, "playlist", {"key": "starwars"}),
        )
        for kind, variables, source, template, definition_variables in cases:
            with self.subTest(definition=kind):
                data = self.meta.DataFile.__new__(self.meta.DataFile)
                data.templates = {
                    name: (definition, {})
                    for name, definition in source["templates"].items()
                }
                data.temp_vars = variables
                data.data_type = kind
                data.library = SimpleNamespace(type="Movie", name="Fixture movies")
                with patch.object(self.meta, "logger", Mock()):
                    result = data.apply_template(
                        None,
                        "Star Wars",
                        {},
                        [{"name": template}],
                        definition_variables,
                    )
                self.assertEqual(result["ignore_ids"], [1756073])
                builder = self.builder.CollectionBuilder.__new__(
                    self.builder.CollectionBuilder
                )
                builder.ignore_ids = result["ignore_ids"]
                builder.parts_collection = False
                builder.libraries = [SimpleNamespace(movie_map={})]
                builder.missing_movies = []
                builder._log_episode_count = Mock()
                with patch.object(self.builder, "logger", Mock()):
                    builder.filter_and_save_items([(1756073, "tmdb"), (11, "tmdb")])
                self.assertEqual(builder.missing_movies, [11])
        self.assertNotIn("ignore_ids", self.config["settings"])
        for library in self.config["libraries"].values():
            self.assertNotIn("ignore_ids", library.get("settings", {}))

    def test_ranked_themes_override_inherited_change_hooks(self) -> None:
        """An empty hook list blocks theme notifications even with inherited hooks."""
        source = self.yaml.load(
            Path("/workspace/movies/top-rated-subgenres.yml").read_text()
        )
        template = source["templates"]["ranked_theme"]
        builder = self.builder.CollectionBuilder.__new__(self.builder.CollectionBuilder)
        builder.details = {"changes_webhooks": ["https://example.invalid/webhook"]}
        builder._details(
            "changes_webhooks", template["changes_webhooks"], "changes_webhooks", {}
        )
        builder.obj = object()
        builder.deleted = False
        builder.created = True
        builder.library = Mock()
        builder.send_notifications()
        builder.library.Webhooks.collection_hooks.assert_not_called()
        self.assertEqual(template["limit"], 250)
        self.assertEqual(template["sync_mode"], "sync")

    def test_optional_settings_remain_explicit_nulls(self) -> None:
        """Keep optional keys present so private copies can preserve default behavior."""
        for key in (
            "default_collection_order",
            "auto_sort_hubs",
            "playlist_exclude_users",
            "custom_repo",
        ):
            self.assertIn(key, self.config["settings"])
            self.assertIsNone(self.config["settings"][key])
        self.assertIn("verify_ssl", self.config["plex"])
        self.assertIsNone(self.config["plex"]["verify_ssl"])
        self.assertIs(self.config["settings"]["verify_ssl"], True)
