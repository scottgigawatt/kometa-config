#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_midnight_tv.py: Protect episode rating scopes and ordered, local story references.
#

"""Exercise TV discovery definitions with Kometa's pinned native parsers."""

import ast
import copy
import importlib
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML


class MidnightTVTests(unittest.TestCase):
    """Keep per-show episode selections and multi-part story order intentional."""

    def setUp(self) -> None:
        """Load the public TV definitions without touching Plex or credentials."""
        self.source = YAML().load(
            Path("/workspace/shows/midnight-cinema.yml").read_text()
        )
        self.collections = self.source["collections"]
        self.builder = importlib.import_module("modules.builder")
        self.plex = importlib.import_module("modules.plex")
        self.textfile = importlib.import_module("modules.textfile")

    def test_effective_episode_attributes_are_allowed_by_pinned_runtime(self) -> None:
        """Catch unsupported show settings introduced through a shared template."""
        meta = importlib.import_module("modules.meta")
        renderer = meta.DataFile.__new__(meta.DataFile)
        renderer.templates = {
            name: (definition, {})
            for name, definition in self.source["templates"].items()
        }
        renderer.library = SimpleNamespace(type="Show", name="Fixture")
        renderer.data_type = "Collection"
        renderer.temp_vars = {}
        allowed = set(
            self.builder.parts_collection_valid + self.builder.ignored_details
        )

        #
        # Use the actual template renderer and level allowlist, which the YAML schema misses.
        # A show-only minimum in the shared template previously failed all episode collections.
        #
        self.assertNotIn("minimum_items", allowed)
        for name, definition in self.collections.items():
            if definition["builder_level"] != "episode":
                continue
            with self.subTest(collection=name), patch.object(meta, "logger", Mock()):
                effective = renderer.apply_template(
                    None, name, definition, copy.deepcopy(definition["template"]), {}
                )
                effective.update(
                    {
                        key: value
                        for key, value in definition.items()
                        if key != "template"
                    }
                )
                self.assertEqual(set(effective) - allowed, set())
        self.assertEqual(self.collections["Weekend Miniseries"]["minimum_items"], 3)

    def test_episode_ratings_do_not_become_parent_show_ratings(self) -> None:
        """Require genuinely rated episodes and cap each show's representation."""
        definition = self.collections["TV's Greatest Episodes"]
        library = self.plex.Plex.__new__(self.plex.Plex)
        library.is_show = True
        library.is_movie = False
        library.is_music = False
        renderer = self.builder.CollectionBuilder.__new__(
            self.builder.CollectionBuilder
        )
        renderer.Type = "Collection"
        renderer.builder_level = "episode"
        renderer.library = library

        self.assertEqual(definition["builder_level"], "episode")
        searches = definition["plex_search"]
        self.assertTrue(searches)
        titles = [
            str(search["all"].get("title.is", search["all"].get("any")))
            for search in searches
        ]
        self.assertEqual(len(titles), len(set(titles)))
        for search in searches:
            with self.subTest(search=search):
                self.assertEqual(search["limit"], 5)
                self.assertEqual(search["sort_by"], "critic_rating.desc")
                self.assertEqual(search["all"]["episode_critic_rating.gte"], 8.5)
                self.assertNotIn("critic_rating.gte", search["all"])
                item_type, _, query = renderer.build_filter("plex_search", dict(search))
                self.assertEqual(item_type, 4)
                self.assertIn("type=4&limit=5&sort=rating%3Adesc", query)
                self.assertIn("episode.rating", query)
                self.assertNotIn("show.rating", query)
                if "any" in search["all"]:
                    self.assertIn("or=1&show.title", query)

        self.assertEqual(
            library.get_search_key("episode_critic_rating", libtype="episode"),
            "episode.rating",
        )
        self.assertEqual(
            library.get_search_key("title", libtype="episode"), "show.title"
        )

    def test_empty_show_search_does_not_abort_other_episode_matches(self) -> None:
        """Execute the pinned run loop to preserve partial matches and real error failures."""
        definition = self.collections["TV's Greatest Episodes"]
        self.assertIs(definition["ignore_blank_results"], True)
        self.assertNotIn("ignore_blank_results", self.source["templates"]["midnight"])

        #
        # Importing kometa.py would start its CLI. Execute only its actual builder loop instead.
        # This protects handling of empty searches without copying the upstream exception logic.
        #
        tree = ast.parse(Path("/kometa.py").read_text())
        loops = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Attribute)
            and node.iter.attr == "builders"
            and any(isinstance(child, ast.ExceptHandler) for child in ast.walk(node))
        ]
        loop = next(
            node
            for node in loops
            if any(
                isinstance(child, ast.Attribute)
                and child.attr == "ignore_blank_results"
                for child in ast.walk(node)
            )
        )
        code = compile(
            ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])),
            "/kometa.py:collection-builder-loop",
            "exec",
        )
        util = importlib.import_module("modules.util")
        exceptions = {
            name: getattr(util, name)
            for name in (
                "BuilderValidationError",
                "OverlayError",
                "MappingConvertError",
                "ServiceError",
                "Failed",
            )
        }
        builder = Mock()
        builder.builders = [
            ("plex_search", "absent show"),
            ("plex_search", "present show"),
        ]
        builder.ignore_blank_results = definition["ignore_blank_results"]
        builder.obj = None
        builder.gather_ids.side_effect = [
            util.Failed("Plex Error: No Items found in Plex"),
            [(42, "ratingKey")],
        ]
        logger = Mock()
        exec(code, {"builder": builder, "logger": logger, **exceptions})  # noqa: S102 - Execute only immutable pinned runtime code.
        builder.filter_and_save_items.assert_called_once_with([(42, "ratingKey")])
        logger.warning.assert_called_once()

        #
        # Service and definition errors still abort; the setting is scoped to this collection.
        #
        for error_type in (
            util.ServiceError,
            util.BuilderValidationError,
            util.MappingConvertError,
        ):
            with self.subTest(error=error_type.__name__):
                builder.gather_ids.side_effect = error_type("Meaningful failure")
                with self.assertRaises(error_type):
                    exec(code, {"builder": builder, "logger": logger, **exceptions})  # noqa: S102 - Execute only immutable pinned runtime code.

    def test_arc_references_parse_in_story_order_without_requests(self) -> None:
        """Preserve both parts of each story and the recovery episode after assimilation."""
        expected = {
            "TV Story Arcs: Star Trek — The Borg": (
                71470,
                [(2, 16), (3, 26), (4, 1), (4, 2), (5, 23), (6, 26), (7, 1)],
            ),
            "TV Story Arcs: The X-Files — Black Oil Begins": (
                77398,
                [(3, 15), (3, 16), (4, 8), (4, 9)],
            ),
        }
        requests = Mock()
        parser = self.textfile.TextFile(requests)
        for name, (show_id, episodes) in expected.items():
            with self.subTest(collection=name):
                definition = self.collections[name]
                actual = parser.get_text_ids(list(definition["text"]), is_movie=False)
                self.assertEqual(
                    actual,
                    [
                        (f"{show_id}_{season}_{episode}", "tvdb_episode")
                        for season, episode in episodes
                    ],
                )
                self.assertEqual(definition["builder_level"], "episode")
                self.assertEqual(definition["collection_order"], "custom")
                self.assertFalse(any(key.startswith("sonarr_") for key in definition))
        self.assertEqual(requests.mock_calls, [])

    def test_miniseries_have_reviewable_complete_runtime_evidence(self) -> None:
        """Keep the ten-hour curation boundary explicit without an episode-runtime shortcut."""
        definition = self.collections["Weekend Miniseries"]
        ids = definition["tmdb_show"]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(4613, ids)
        for index, identifier in enumerate(ids):
            with self.subTest(tmdb_id=identifier):
                comment = ids.ca.items[index][0].value
                evidence = re.search(r"; (\d+) episodes, (\d+) minutes", comment)
                self.assertIsNotNone(evidence)
                if evidence:
                    episodes, minutes = map(int, evidence.groups())
                    self.assertGreaterEqual(episodes, 3)
                    self.assertGreater(minutes, episodes)
                    self.assertLessEqual(minutes, 600)
                self.assertIs(type(identifier), int)
        self.assertEqual(definition["builder_level"], "show")
        self.assertNotIn("plex_search", definition)
        self.assertEqual(
            definition["filters"], {"tmdb_type": "miniseries", "tmdb_status": "ended"}
        )


if __name__ == "__main__":
    unittest.main()
