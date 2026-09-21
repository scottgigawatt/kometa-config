#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_location_universe_preview.py: Guard native sources and retained charts.
#
# Purpose: Protect native city and universe builders and production chart wiring.
# Usage: Run through make validate inside the pinned Kometa image.
#

"""Exercise collection safety contracts without connecting to external services."""

import copy
import importlib.util
import unittest
from pathlib import Path

from ruamel.yaml import YAML

#
# Load the exact container-mounted helper without invoking its CLI entrypoint.
# A missing loader indicates a broken test mount, not a collection failure.
#
spec = importlib.util.spec_from_file_location(
    "preview", "/scripts/collection-preview.py"
)
if spec is None or spec.loader is None:
    raise ImportError("The container must mount /scripts/collection-preview.py.")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class LocationUniverseTests(unittest.TestCase):
    """Keep native city and universe sources isolated from production services."""

    def setUp(self) -> None:
        """Load independent source copies for mutation and wiring checks."""
        yaml = YAML()
        self.cities = yaml.load(Path("/workspace/movies/cities.yml").read_text())
        self.universes = yaml.load(Path("/workspace/movies/universes.yml").read_text())
        self.config = yaml.load(Path("/workspace/config.yml").read_text())

    #
    # Validate native builders before permitting any fixture-library writes.
    #
    def test_native_sources_selected(self) -> None:
        """Select the six city collections and five native movie universes."""
        names = preview.location_universe_names(self.cities, self.universes)
        self.assertEqual(len(names), 11)
        self.assertIn("Washington D.C. Collection", names)
        self.assertIn("Star Trek Universe", names)

    def test_writers_and_external_sources_rejected(self) -> None:
        """Reject external lists, standalone movies, and download writers."""
        for index in range(2):
            for key in ("trakt_list", "imdb_list", "radarr_search", "tmdb_movie"):
                with self.subTest(source=index, key=key):
                    sources = copy.deepcopy([self.cities, self.universes])
                    next(iter(sources[index]["collections"].values()))[key] = True
                    with self.assertRaises(ValueError):
                        preview.location_universe_names(*sources)

    def test_template_writers_and_overrides_rejected(self) -> None:
        """Prevent source templates or their variables from enabling downloads."""
        for index in range(2):
            for target in ("templates", "collections"):
                with self.subTest(source=index, target=target):
                    sources = copy.deepcopy([self.cities, self.universes])
                    definition = next(iter(sources[index][target].values()))
                    if target == "collections":
                        definition = definition["template"]
                    definition["radarr_add_missing"] = True
                    with self.assertRaises(ValueError):
                        preview.location_universe_names(*sources)

    def test_invalid_and_duplicate_ids_rejected(self) -> None:
        """Require unique positive integers for both native TMDb builders."""
        for source, name, builder in (
            (0, "Chicago Collection", "tmdb_keyword"),
            (1, "DC Universe", "tmdb_keyword"),
            (1, "Star Trek Universe", "tmdb_collection"),
        ):
            for ids in ([True], [0], [-1], [], ["151"], [151, 151]):
                with self.subTest(name=name, ids=ids):
                    sources = copy.deepcopy([self.cities, self.universes])
                    sources[source]["collections"][name][builder] = ids
                    with self.assertRaises(ValueError):
                        preview.location_universe_names(*sources)

    def test_id_comments_required(self) -> None:
        """Require readable names beside keyword and collection IDs."""
        for source, builder in (
            (self.cities, "tmdb_keyword"),
            (self.universes, "tmdb_keyword"),
            (self.universes, "tmdb_collection"),
        ):
            with self.subTest(builder=builder):
                changed = copy.deepcopy(source["collections"])
                next(
                    d[builder] for d in changed.values() if builder in d
                ).ca.items.clear()
                with self.assertRaises(ValueError):
                    preview.check_id_comments(changed, builder)

    #
    # Protect production wiring and the explicitly retained chart behavior.
    #
    def test_universe_defaults_cannot_recreate_local_collections(self) -> None:
        """Keep excluded Defaults from recreating locally owned universes."""
        chart = next(
            entry
            for entry in self.config["libraries"]["Movies"]["collection_files"]
            if entry.get("default") == "universe"
        )["template_variables"]
        self.assertEqual(
            set(chart["exclude"]), {"marvel", "mcu", "dcu", "trek", "avp", "xmen"}
        )
        self.assertFalse(any(key.startswith("trakt_list") for key in chart))
        self.assertEqual(chart["append_data"], {"star": "Star Wars Saga"})
        self.assertFalse(chart.get("sync", False))

        #
        # Pinned Defaults must not delete excluded dynamic collections by default.
        # Local names must not also appear in another human-authored movie file.
        #
        yaml = YAML(typ="safe")
        defaults = yaml.load(Path("/defaults/both/universe.yml").read_text())
        self.assertFalse(
            defaults["dynamic_collections"]["Universe Collections"].get("sync", False)
        )
        local_names = set(self.universes["collections"])
        for path in Path("/workspace/movies").glob("*.yml"):
            if path.name != "universes.yml":
                self.assertFalse(
                    local_names
                    & set(yaml.load(path.read_text()).get("collections", {}))
                )

    def test_trakt_chart_settings_preserved(self) -> None:
        """Preserve the approved movie and TV Trakt chart settings."""
        for library in ("Movies", "TV Shows"):
            with self.subTest(library=library):
                entries = [
                    item
                    for item in self.config["libraries"][library]["collection_files"]
                    if item.get("default") == "trakt"
                ]
                expected = {
                    "use_collected": False,
                    "use_recommended": False,
                    "use_watched": False,
                    "order_popular": 4,
                    "order_trending": 4,
                }
                if library == "Movies":
                    expected["schedule"] = "weekly(monday)"
                self.assertEqual(
                    entries, [{"default": "trakt", "template_variables": expected}]
                )

    def test_tracearr_behavior_preserved(self) -> None:
        """Preserve Tracearr behavior while using media-specific summaries."""

        #
        # Use the pinned Defaults' zero activity threshold without a redundant override.
        #
        defaults = YAML().load(Path("/defaults/chart/tracearr.yml").read_text())
        self.assertEqual(
            defaults["templates"]["tracearr"]["default"]["list_minimum"], 0
        )
        for library in ("Movies", "TV Shows"):
            with self.subTest(library=library):
                entries = [
                    item
                    for item in self.config["libraries"][library]["collection_files"]
                    if item.get("default") == "tracearr"
                ]
                expected = {
                    "collection_section": "020_1",
                    "list_days": 30,
                    "list_size": 25,
                    "name_popular": "Plex Popular",
                    "name_watched": "Plex Watched",
                    "use_trending": False,
                    "use_rewatched": False,
                    "use_completed": False,
                    "use_binged": False,
                    "use_transcoded": False,
                }
                for entry in entries:
                    for key in ("summary_popular", "summary_watched"):
                        summary = entry["template_variables"].pop(key)
                        self.assertIsInstance(summary, str)
                        self.assertTrue(summary.strip())
                self.assertEqual(
                    entries, [{"default": "tracearr", "template_variables": expected}]
                )


#
# Support direct execution inside the same isolated validation container.
#
if __name__ == "__main__":
    unittest.main()
