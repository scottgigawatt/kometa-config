#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_tv_seasonal_preview.py: Check episode holiday matching and fixture safety.
#
# Purpose: Exercise title-or-summary rules without external lists or downloads.
# Usage: Run through make validate inside the pinned Kometa image.
#

"""Protect episode-level membership, presentation, and disconnected previews."""

import contextlib
import copy
import importlib.util
import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ruamel.yaml import YAML

#
# Load the mounted guard without running its live Plex entrypoint.
#
spec = importlib.util.spec_from_file_location(
    "preview", "/scripts/collection-preview.py"
)
if spec is None or spec.loader is None:
    raise ImportError("The container must mount /scripts/collection-preview.py.")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class TVSeasonalPreviewTests(unittest.TestCase):
    """Require precise episode rules and preserve the fixture-only boundary."""

    def setUp(self) -> None:
        """Load a fresh copy of the actual production source for every test."""
        self.source = YAML().load(Path("/workspace/shows/seasonal.yml").read_text())

    def matches(self, holiday: str, title: str = "", summary: str = "") -> bool:
        """Evaluate source patterns using Kometa's title-or-summary filter shape.

        Args:
            holiday: Collection holiday name without the Episodes suffix.
            title: Episode title, never the parent show title.
            summary: Episode description, never the parent show description.

        Returns:
            Whether either episode metadata field matches the source pattern.
        """
        template = self.source["templates"]["seasonal"]
        pattern = self.source["collections"][f"{holiday} Episodes"]["template"][
            "holiday_pattern"
        ]
        values = {"title.regex": title, "summary.regex": summary}
        return any(
            all(re.search(pattern, values[key]) for key in group)
            for group in template["filters"]
        )

    #
    # Check both OR branches and useful vocabulary without broad seasonal guesses.
    #
    def test_three_episode_collections(self) -> None:
        """Select only the three existing holiday episode collections."""
        self.assertEqual(
            preview.tv_seasonal_names(self.source),
            ["Halloween Episodes", "Thanksgiving Episodes", "Christmas Episodes"],
        )

    def test_title_only_matches(self) -> None:
        """Accept explicit holidays even when the episode summary is empty."""
        for holiday in ("Halloween", "Thanksgiving", "Christmas"):
            with self.subTest(holiday=holiday):
                self.assertTrue(self.matches(holiday, title=f"A {holiday} Story"))

    def test_summary_only_matches(self) -> None:
        """Accept holiday descriptions even when the episode title is unrelated."""
        for holiday in ("Halloween", "Thanksgiving", "Christmas"):
            with self.subTest(holiday=holiday):
                self.assertTrue(
                    self.matches(
                        holiday, "The Reunion", f"Plans for {holiday} go awry."
                    )
                )

    def test_halloween_traditions(self) -> None:
        """Recognize specific Halloween traditions with common separators."""
        for title in (
            "HALLOWEEN!",
            "Treehouse of Horror II",
            "Trick-or-Treat",
            "Trick or Treating",
            "All Hallows Eve",
        ):
            with self.subTest(title=title):
                self.assertTrue(self.matches("Halloween", title=title))

    def test_christmas_variants(self) -> None:
        """Recognize Christmas abbreviations and unambiguous seasonal phrases."""
        for title in (
            "CHRISTMAS EVE",
            "Xmas",
            "X-Mas",
            "X mas",
            "Yuletide",
            "Santa Claus",
        ):
            with self.subTest(title=title):
                self.assertTrue(self.matches("Christmas", title=title))

    def test_generic_seasonal_words_do_not_match(self) -> None:
        """Exclude weather, food, locations, and festivities without a named holiday."""

        #
        # Deliberate near-matches exercise word boundaries, not accepted spellings.
        # cspell:ignore Christmasberry Halloweenish Thanksgivingish xmaxs
        #
        for holiday in ("Halloween", "Thanksgiving", "Christmas"):
            for text in (
                "A winter holiday party with gifts and snow.",
                "A ghost wears a costume to a haunted house.",
                "A turkey dinner with the family.",
                "A visit to Santa Barbara and Santa Fe.",
                "Noel joins the party.",
                "A Christmasberry tree and a Halloweenish costume.",
                "Thanksgivingish decorations and a xmaxs typo.",
            ):
                with self.subTest(holiday=holiday, text=text):
                    self.assertFalse(self.matches(holiday, text, text))

    def test_empty_metadata_does_not_match(self) -> None:
        """Reject missing episode descriptions without a fallback to show metadata."""
        for holiday in ("Halloween", "Thanksgiving", "Christmas"):
            with self.subTest(holiday=holiday):
                self.assertFalse(self.matches(holiday))

    #
    # Constrain membership and source behavior before any fixture copy is rendered.
    #
    def test_show_level_expansion_rejected(self) -> None:
        """Prevent selecting a parent show and expanding every episode."""
        for level in ("show", "season"):
            with self.subTest(level=level):
                changed = copy.deepcopy(self.source)
                changed["templates"]["seasonal"]["builder_level"] = level
                with self.assertRaises(ValueError):
                    preview.tv_seasonal_names(changed)

    def test_parent_metadata_and_combined_filters_rejected(self) -> None:
        """Require independent episode-title and episode-summary filter sets."""
        for filters in (
            [{"show_title.regex": "<<holiday_pattern>>"}],
            [
                {
                    "title.regex": "<<holiday_pattern>>",
                    "summary.regex": "<<holiday_pattern>>",
                }
            ],
            [],
        ):
            with self.subTest(filters=filters):
                changed = copy.deepcopy(self.source)
                changed["templates"]["seasonal"]["filters"] = filters
                with self.assertRaises(ValueError):
                    preview.tv_seasonal_names(changed)

    def test_download_flags_rejected(self) -> None:
        """Reject Sonarr attributes, which are unsupported on episode collections."""
        for key in (
            "sonarr_add_missing",
            "sonarr_add_existing",
            "sonarr_search",
            "sonarr_upgrade_existing",
            "sonarr_monitor_existing",
        ):
            for enabled in (True, False):
                with self.subTest(key=key, enabled=enabled):
                    changed = copy.deepcopy(self.source)
                    changed["templates"]["seasonal"][key] = enabled
                    with self.assertRaises(ValueError):
                        preview.tv_seasonal_preview(changed)

    def test_collection_overrides_rejected(self) -> None:
        """Reject additional builders, external lists, and item or download writes."""
        for key in (
            "trakt_list",
            "tmdb_show",
            "plex_search",
            "item_label",
            "sonarr_add_existing",
            "radarr_search",
            "delete_not_scheduled",
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.source)
                changed["collections"]["Christmas Episodes"][key] = True
                with self.assertRaises(ValueError):
                    preview.tv_seasonal_names(changed)

    def test_external_templates_rejected(self) -> None:
        """Reject remote templates that could introduce unchecked behavior."""
        self.source["external_templates"] = [{"default": "templates"}]
        with self.assertRaises(ValueError):
            preview.tv_seasonal_names(self.source)

    def test_invalid_patterns_rejected(self) -> None:
        """Reject invalid, empty-matching, unresolved, and non-string patterns."""
        for pattern in ("", " ", "[", ".*", "<<other_pattern>>", True, None):
            with self.subTest(pattern=pattern):
                changed = copy.deepcopy(self.source)
                changed["collections"]["Christmas Episodes"]["template"][
                    "holiday_pattern"
                ] = pattern
                with self.assertRaises(ValueError):
                    preview.tv_seasonal_names(changed)

    def test_presentation_and_schedule_changes_rejected(self) -> None:
        """Protect the existing poster mappings, schedules, and visible presentation."""
        for key, value in (("schedule", "daily"), ("summary", "")):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.source)
                changed["collections"]["Christmas Episodes"][key] = value
                with self.assertRaises(ValueError):
                    preview.tv_seasonal_names(changed)
        self.source["collections"]["Christmas Episodes"]["template"]["poster_id"] = (
            "other"
        )
        with self.assertRaises(ValueError):
            preview.tv_seasonal_names(self.source)

    def test_projection_changes_only_deletion(self) -> None:
        """Preserve all source membership and presentation without mutating source."""
        original = copy.deepcopy(self.source)
        expected = copy.deepcopy(self.source)
        template = expected["templates"]["seasonal"]
        template["delete_not_scheduled"] = False
        self.assertEqual(preview.tv_seasonal_preview(self.source), expected)
        self.assertEqual(self.source, original)

    #
    # Exercise CLI selection with disposable runtime files and a mocked Kometa run.
    # No network, credentials, or actual Plex writes are available to these tests.
    #
    def test_tv_only_command_targets_the_tv_fixture(self) -> None:
        """Restrict the live command to the three TV collections and TV fixture."""
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            runtime.joinpath("config.yml").write_text(
                Path("/workspace/tests/kometa/collections-config.yml").read_text()
            )

            def mapped_path(value: str) -> Path:
                """Map runtime writes into the disposable test directory."""
                return (
                    runtime / value[8:] if value.startswith("/config/") else Path(value)
                )

            def completed_run(*args, **kwargs) -> None:
                """Produce a successful private summary without invoking Kometa."""
                runtime.joinpath("logs").mkdir()
                runtime.joinpath("logs/meta.log").write_text(
                    "\n".join(
                        f"| {name} | 1 | 1 | 0 | 0 | Created |"
                        for name in self.source["collections"]
                    )
                )

            with (
                patch(
                    "sys.argv", ["collection-preview.py", "--run", "--tv-seasonal-only"]
                ),
                patch.object(preview, "Path", side_effect=mapped_path),
                patch.object(
                    preview.subprocess, "run", side_effect=completed_run
                ) as run,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                preview.main()
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ["--libraries", "test_tv_lib"])
            self.assertEqual(
                command[command.index("--run-collections") + 1],
                "|".join(self.source["collections"]),
            )
            self.assertIn("--no-missing", command)
            self.assertIn("--ignore-schedules", command)
            self.assertEqual(
                YAML().load(runtime.joinpath("tv-seasonal.yml").read_text()),
                preview.tv_seasonal_preview(self.source),
            )

    def test_conflicting_scopes_rejected(self) -> None:
        """Reject simultaneous movie-only and episode-only requests before loading."""
        with (
            patch(
                "sys.argv",
                ["collection-preview.py", "--seasonal-only", "--tv-seasonal-only"],
            ),
            patch.object(preview, "load_preview") as load,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as error,
        ):
            preview.main()
        self.assertEqual(error.exception.code, 2)
        load.assert_not_called()


#
# Support direct execution inside the isolated validation container.
#
if __name__ == "__main__":
    unittest.main()
