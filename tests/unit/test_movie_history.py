#
# Copyright 2025-2026 Scott Gigawatt
#
# SPDX-License-Identifier: Apache-2.0
#
# test_movie_history.py: Protect native movie history dates and local-item matching.
#

"""Exercise the authored history definition with the unchanged pinned runtime."""

import copy
import importlib
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML


class MovieHistoryTests(unittest.TestCase):
    """Keep monthly history independent of generated GUIDs and current releases."""

    def setUp(self) -> None:
        """Load public source and native parsers without any service connections."""
        self.root = Path("/workspace")
        self.source = YAML().load((self.root / "movies/movie-history.yml").read_text())
        self.builder = importlib.import_module("modules.builder")
        self.plex = importlib.import_module("modules.plex")
        self.meta = importlib.import_module("modules.meta")

    def effective_definition(self, now: datetime) -> dict:
        """Render the real template at a controlled calendar boundary.

        Args:
            now: Run date used by Kometa's built-in template variables.

        Returns:
            The collection definition after native template expansion.
        """
        renderer = self.meta.DataFile.__new__(self.meta.DataFile)
        renderer.templates = {
            name: (definition, {})
            for name, definition in self.source["templates"].items()
        }
        renderer.library = SimpleNamespace(type="Movie", name="Fixture movies")
        renderer.data_type = "Collection"
        renderer.temp_vars = {}
        name = "This Month in Movie History"
        definition = self.source["collections"][name]
        with (
            patch.object(self.meta, "datetime", Mock(now=Mock(return_value=now))),
            patch.object(self.meta, "logger", Mock()),
        ):
            effective = renderer.apply_template(
                None, name, definition, copy.deepcopy(definition["template"]), {}
            )
        effective.update(
            {key: value for key, value in definition.items() if key != "template"}
        )
        return effective

    def matches(self, now: datetime, released: datetime | None) -> bool:
        """Evaluate real Kometa filters against a local-only Plex movie.

        Args:
            now: Run date controlling the current month and year boundary.
            released: Plex release date, or missing metadata.

        Returns:
            Whether the native history filters retain the movie.
        """
        effective = self.effective_definition(now)
        library = self.plex.Plex.__new__(self.plex.Plex)
        library.reload = Mock(side_effect=lambda item, **kwargs: item)
        library.cached_item_attr = Mock(
            side_effect=lambda item, key: vars(item).get(key)
        )
        renderer = self.builder.CollectionBuilder.__new__(
            self.builder.CollectionBuilder
        )
        renderer.Type = "Collection"
        renderer.library = library
        renderer.builder_level = "movie"
        renderer.filters = []
        renderer._filters("filters", copy.deepcopy(effective["filters"]))
        self.assertEqual(len(renderer.filters), 1)

        #
        # The release date controls history, even when the separate year field differs.
        #
        movie = self.plex.Movie.__new__(self.plex.Movie)
        movie.ratingKey = 123
        movie.guid = "local://123"
        movie.year = now.year
        movie.originallyAvailableAt = released
        return library.check_filters(movie, renderer.filters[0], now)

    def test_previous_years_match_only_the_current_month(self) -> None:
        """Include both month edges and exclude current, future, or absent dates."""
        now = datetime(2026, 11, 16)
        cases = (
            (datetime(2018, 11, 1), True),
            (datetime(2018, 11, 30), True),
            (datetime(2018, 10, 31), False),
            (datetime(2018, 12, 1), False),
            (datetime(2026, 11, 1), False),
            (datetime(2027, 11, 1), False),
            (None, False),
        )
        for released, expected in cases:
            with self.subTest(released=released):
                self.assertEqual(self.matches(now, released), expected)

    def test_year_rollover_and_leap_day_use_the_run_calendar(self) -> None:
        """Keep January, December, and leap-day releases within the correct month."""
        cases = (
            (datetime(2027, 1, 1), datetime(2026, 1, 31), True),
            (datetime(2027, 1, 1), datetime(2027, 1, 1), False),
            (datetime(2026, 12, 31), datetime(2025, 12, 1), True),
            (datetime(2026, 12, 31), datetime(2026, 12, 1), False),
            (datetime(2027, 2, 1), datetime(2024, 2, 29), True),
        )
        for now, released, expected in cases:
            with self.subTest(now=now, released=released):
                self.assertEqual(self.matches(now, released), expected)

    def test_local_only_movie_uses_its_item_key_without_text_parsing(self) -> None:
        """Reproduce the rejected GUID and prove the native builder accepts its item."""
        textfile = importlib.import_module("modules.textfile")
        util = importlib.import_module("modules.util")
        with self.assertRaisesRegex(util.Failed, "Line not supported"):
            textfile.TextFile(Mock()).get_text_ids(["local://123"], is_movie=True)

        movie = self.plex.Movie.__new__(self.plex.Movie)
        movie.ratingKey = 123
        movie.guid = "local://123"
        library = self.plex.Plex.__new__(self.plex.Plex)
        library.get_all = Mock(return_value=[movie])
        with patch.object(self.plex, "logger", Mock()):
            self.assertEqual(
                library.get_rating_keys("plex_all", "movie"), [(123, "ratingKey")]
            )
        self.assertTrue(self.matches(datetime(2026, 11, 16), datetime(2018, 11, 1)))

    def test_definition_preserves_presentation_without_external_writers(self) -> None:
        """Keep one native selection with the existing name, artwork, and sort position."""
        effective = self.effective_definition(datetime(2026, 11, 16))
        self.assertEqual(
            set(effective),
            {
                "plex_all",
                "filters",
                "collection_order",
                "sync_mode",
                "minimum_items",
                "sort_title",
                "file_poster",
                "summary",
            },
        )
        self.assertIs(effective["plex_all"], True)
        self.assertEqual(effective["sync_mode"], "sync")
        self.assertEqual(effective["minimum_items"], 1)
        self.assertEqual(effective["collection_order"], "alpha")
        self.assertEqual(effective["sort_title"], "!020_0_1_Plex In-History")
        self.assertEqual(
            effective["file_poster"],
            "/config/assets/posters/chart/This Month in Movie History.png",
        )
