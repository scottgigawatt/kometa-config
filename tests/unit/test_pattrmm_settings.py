#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_pattrmm_settings.py: Protect Neo's authored settings and Kometa input paths.
#

"""Check the production Neo contract without credentials or service access."""

import copy
import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML


class PattrmmSettingsTests(unittest.TestCase):
    """Keep generated collections isolated from authored source and custom overlays."""

    def setUp(self) -> None:
        """Read only the source snapshot mounted by the offline validator."""
        root = Path("/workspace")
        yaml = YAML(typ="safe")
        self.settings = yaml.load((root / "pattrmm/settings.yml").read_text())
        self.config = yaml.load((root / "config.yml").read_text())
        self.workflow = yaml.load(
            (root / ".github/workflows/validate-pr.yml").read_text()
        )

    def test_ci_includes_authored_settings(self) -> None:
        """Keep the Neo source available in GitHub's artwork-free checkout."""
        checkout = self.workflow["jobs"]["validate"]["steps"][0]
        self.assertIn("/pattrmm/", checkout["with"]["sparse-checkout"].splitlines())

    def test_settings_and_library_contract(self) -> None:
        """Require Neo's config selection and the exact production library names."""
        self.assertEqual(set(self.settings), {"libraries", "settings"})
        self.assertEqual(
            self.settings["settings"],
            {"kometa_config": "config.yml", "data_source": "tmdb"},
        )
        self.assertEqual(set(self.settings["libraries"]), {"Movies", "TV Shows"})
        expected = {
            "Movies": ["by_size", "in_history"],
            "TV Shows": ["in_history", "extended_status"],
        }
        for library, cores in self.settings["libraries"].items():
            with self.subTest(library=library):
                self.assertEqual(
                    [list(core) for core in cores], [[key] for key in expected[library]]
                )

    def test_generated_paths_and_collection_safety(self) -> None:
        """Match each output folder to Kometa and forbid download or overlay actions."""
        names = set()
        for library, folder in (("Movies", "movies"), ("TV Shows", "shows")):
            directory = f"generated/pattrmm/{folder}/"
            self.assertIn(
                {"folder": f"config/{directory}"},
                self.config["libraries"][library]["collection_files"],
            )
            for entry in self.settings["libraries"][library]:
                core, settings = next(iter(entry.items()))
                if core == "extended_status":
                    self.assertEqual(set(settings), {"returning_soon"})
                    settings = settings["returning_soon"]
                    self.assertEqual(settings["mode"], "collection")
                    self.assertEqual(settings["days_ahead"], 90)
                    self.assertEqual(settings["days_behind"], 14)
                elif core == "in_history":
                    self.assertEqual(settings["range"], "month")
                else:
                    self.assertEqual(settings["order_by"], "size.desc")
                    self.assertEqual(settings["limit"], 500)
                self.assertIs(settings["enabled"], True)
                self.assertEqual(settings["collection_dir"], directory)
                collection = settings["collection"]
                self.assertEqual(
                    set(collection),
                    {
                        "name",
                        "collection_order",
                        "sync_mode",
                        "minimum_items",
                        "sort_title",
                        "file_poster",
                        "summary",
                    },
                )
                self.assertEqual(collection["sync_mode"], "sync")
                self.assertEqual(collection["collection_order"], "custom")
                self.assertEqual(collection["minimum_items"], 1)
                self.assertTrue(collection["summary"])
                self.assertNotIn(collection["name"], names)
                names.add(collection["name"])
        self.assertEqual(len(names), 4)

    def test_collection_posters_and_sort_positions(self) -> None:
        """Keep Neo in the original chart section with explicit local artwork."""
        expected = {
            "Movies by Size": ("!020_0_2_Movies by Size", "Movies by Size.png"),
            "This Month in Movie History": (
                "!020_0_1_Plex In-History",
                "This Month in Movie History.png",
            ),
            "This Month in TV History": (
                "!020_1_Plex In-History",
                "This Month in TV History.png",
            ),
            "Returning Soon": ("!020_0_Plex Returning Soon", "Returning Soon.png"),
        }

        #
        # A missing exclamation mark sorts these charts below the prefixed sections.
        #
        for entries in self.settings["libraries"].values():
            for entry in entries:
                core, settings = next(iter(entry.items()))
                if core == "extended_status":
                    settings = settings["returning_soon"]

                collection = settings["collection"]
                title, poster = expected[collection["name"]]
                with self.subTest(collection=collection["name"]):
                    self.assertEqual(collection["sort_title"], title)
                    self.assertEqual(
                        collection["file_poster"],
                        f"/config/assets/posters/chart/{poster}",
                    )

    def test_custom_overlay_ownership(self) -> None:
        """Keep every generated Neo file out of the production overlay pipeline."""
        for library in self.config["libraries"].values():
            for entry in library.get("overlay_files", []):
                self.assertNotIn("generated/pattrmm", str(entry))

    def test_movie_chart_group_order(self) -> None:
        """Keep both Neo movie charts together between recent additions and Tracearr."""
        yaml = YAML(typ="safe")
        recent = yaml.load(Path("/workspace/movies/recently-added.yml").read_text())
        shared = yaml.load(Path("/defaults/templates.yml").read_text())
        tracearr = yaml.load(Path("/defaults/chart/tracearr.yml").read_text())
        importlib.import_module("modules.builder")
        meta = importlib.import_module("modules.meta")
        renderer = meta.DataFile.__new__(meta.DataFile)
        renderer.templates = {
            key: (value, {}) for key, value in shared["templates"].items()
        }
        renderer.library = SimpleNamespace(type="Movie", name="Fixture movies")
        renderer.data_type = "Collection"
        renderer.temp_vars = next(
            entry["template_variables"]
            for entry in self.config["libraries"]["Movies"]["collection_files"]
            if entry.get("default") == "tracearr"
        )
        titles = {
            name: definition["sort_title"]
            for name, definition in recent["collections"].items()
        }
        for entry in self.settings["libraries"]["Movies"]:
            collection = next(iter(entry.values()))["collection"]
            titles[collection["name"]] = collection["sort_title"]

        #
        # Expand the actual pinned Defaults so changes to its prefix contract fail.
        #
        for name in ("Tracearr Popular", "Tracearr Watched"):
            definition = tracearr["collections"][name]
            with patch.object(meta, "logger", Mock()):
                rendered = renderer.apply_template(
                    None,
                    name,
                    {},
                    [{"name": "shared"}],
                    copy.deepcopy(definition["variables"]),
                )
            titles[rendered["name"]] = rendered["sort_title"]
        self.assertEqual(
            sorted(titles, key=titles.get),
            [
                "New Movie Releases",
                "Old Movies Just Added",
                "This Month in Movie History",
                "Movies by Size",
                "Plex Popular",
                "Plex Watched",
            ],
        )
