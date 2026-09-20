#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_collection_preview.py: Offline regression tests for fixture isolation.
#
# Purpose: Reject unsafe builders, services, library targets, and run results.
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


class CollectionPreviewTests(unittest.TestCase):
    """Reject unsafe preview inputs before any Plex connection is attempted."""

    def setUp(self) -> None:
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
        self.genres = yaml.load(Path("/workspace/movies/genre.yml").read_text())
        self.themes = yaml.load(
            Path("/workspace/movies/subgenre-rules.yml").read_text()
        )

    #
    # Check rule-based membership and reject hidden source or template behavior.
    #
    def test_genre_and_theme_selection(self) -> None:
        """Select all seven genre rules and six supported theme searches."""
        names = preview.rule_names(self.genres, self.themes)
        self.assertEqual(len(names), 13)
        self.assertIn("LGBTQ+ Movies", names)
        self.assertIn("Top Rated in Mindfuck", names)

    def test_provider_error_cannot_hide_behind_success_summary(self) -> None:
        """Reject provider errors even when the summary reports success."""
        log = "[ERROR] TMDb lookup failed\n| Example | 1 | 0 | 0 | 0:00:01 | Created |"
        with self.assertRaises(ValueError):
            preview.check_run_summary(log, ["Example"])

    def test_rule_source_writers_rejected(self) -> None:
        """Reject source-level downloads, list writes, and curated additions."""
        for source in (self.genres, self.themes):
            for key in (
                "radarr_add_missing",
                "sync_to_trakt_list",
                "trakt_list",
                "tmdb_movie",
            ):
                with self.subTest(source=source is self.genres, key=key):
                    changed = copy.deepcopy(source)
                    next(iter(changed["collections"].values()))[key] = True
                    with self.assertRaises(ValueError):
                        preview.rule_names(
                            changed if source is self.genres else self.genres,
                            changed if source is self.themes else self.themes,
                        )

    def test_rule_template_writers_rejected(self) -> None:
        """Reject writer behavior inherited through a theme template."""
        for key in ("radarr_search", "sync_to_trakt_list", "item_label"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.themes)
                changed["templates"]["ranked_theme"][key] = True
                with self.assertRaises(ValueError):
                    preview.rule_names(self.genres, changed)

    def test_keyword_ids_rejected(self) -> None:
        """Reject empty, duplicate, boolean, and nonpositive keyword IDs."""
        for ids in ([True], [0], [], [470, 470], ["470"]):
            with self.subTest(ids=ids):
                self.genres["collections"]["Spy Movies"]["tmdb_keyword"] = ids
                with self.assertRaises(ValueError):
                    preview.rule_names(self.genres, self.themes)

    def test_genre_search_cannot_escape(self) -> None:
        """Keep native genre searches limited to their expected genre tag."""
        self.genres["collections"]["Horror Movies"]["plex_search"] = {
            "all": {"year": 2025}
        }
        with self.assertRaises(ValueError):
            preview.rule_names(self.genres, self.themes)

    def test_theme_keywords_rejected(self) -> None:
        """Require explicit positive keyword IDs joined with OR separators."""
        for keywords in ("490,4379", "<<arbitrary>>", "0", True):
            with self.subTest(keywords=keywords):
                self.themes["collections"]["Top Rated in Philosophical"]["template"][1][
                    "keywords"
                ] = keywords
                with self.assertRaises(ValueError):
                    preview.rule_names(self.genres, self.themes)

    def test_theme_external_poster_rejected(self) -> None:
        """Keep theme posters in the repository-owned artwork directory."""
        self.themes["collections"]["Top Rated in Mindfuck"]["file_poster"] = (
            "https://example.com/poster.png"
        )
        with self.assertRaises(ValueError):
            preview.rule_names(self.genres, self.themes)

    def test_imdb_curated_list_rejected(self) -> None:
        """Reject curated IMDb lists added to a keyword-based search."""
        self.themes["collections"]["Top Rated in Mindfuck"]["imdb_search"][
            "list.any"
        ] = "ls12345"
        with self.assertRaises(ValueError):
            preview.rule_names(self.genres, self.themes)

    def test_genre_and_subgenre_sources_have_no_trakt(self) -> None:
        """Keep movie genre and theme sources independent of Trakt lists."""
        for name in ("genre.yml", "subgenre-rules.yml", "subgenre-top.yml"):
            self.assertNotIn(
                "trakt", Path("/workspace/movies", name).read_text().lower()
            )

    def test_theme_names_are_not_duplicated(self) -> None:
        """Prevent rule-based themes from duplicating remaining definitions."""
        remaining = YAML(typ="safe").load(
            Path("/workspace/movies/subgenre-top.yml").read_text()
        )
        self.assertFalse(
            set(remaining["collections"]) & set(self.themes["collections"])
        )

    def check(self) -> list[str]:
        """Evaluate the same guard used by the live preview entrypoint."""
        return preview.preview_names(
            self.franchises, self.config, self.smoke, self.shows
        )

    #
    # Keep preview execution restricted to the two named fixture libraries.
    #
    def test_native_selection(self) -> None:
        """Select all guarded sources while excluding unrelated franchises."""
        selected, _ = preview.load_preview(Path("/workspace"))
        self.assertEqual(len(selected), 42)
        self.assertIn("The Purge Collection", selected)
        self.assertIn("Adult Animation", selected)
        self.assertNotIn("After Collection", selected)

    def test_production_library_rejected(self) -> None:
        """Reject production library names before Plex can be contacted."""
        self.config["libraries"]["Movies"] = self.config["libraries"].pop(
            "test_movie_lib"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_library_alias_rejected(self) -> None:
        """Prevent fixture names from aliasing a production library."""
        self.config["libraries"]["test_movie_lib"]["library_name"] = "Movies"
        with self.assertRaises(ValueError):
            self.check()

    def test_extra_service_rejected(self) -> None:
        """Reject unapproved services and external writers in the preview."""
        for service in ("trakt", "radarr", "sonarr", "playlist_files", "webhooks"):
            with self.subTest(service=service):
                config = copy.deepcopy(self.config)
                config[service] = {}
                with self.assertRaises(ValueError):
                    preview.preview_names(
                        self.franchises, config, self.smoke, self.shows
                    )

    def test_extra_library_behavior_rejected(self) -> None:
        """Reject operations and overlays added to the fixture libraries."""
        for key in ("operations", "overlay_files", "settings"):
            with self.subTest(key=key):
                config = copy.deepcopy(self.config)
                config["libraries"]["test_movie_lib"][key] = {}
                with self.assertRaises(ValueError):
                    preview.preview_names(
                        self.franchises, config, self.smoke, self.shows
                    )

    def test_deletion_rejected(self) -> None:
        """Keep below-minimum collection deletion disabled during previews."""
        self.config["settings"]["delete_below_minimum"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_maintenance_rejected(self) -> None:
        """Prevent test runs from triggering server-wide Plex maintenance."""
        self.config["plex"]["empty_trash"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_plaintext_connection_rejected(self) -> None:
        """Require secret substitutions instead of literal Plex addresses."""
        self.config["plex"]["url"] = "http://localhost:32400"
        with self.assertRaises(ValueError):
            self.check()

    def test_plaintext_tmdb_key_rejected(self) -> None:
        """Require a secret substitution instead of a literal API key."""

        #
        # This deliberately fake value exercises rejection, not authentication.
        #
        self.config["tmdb"]["apikey"] = "example"  # pragma: allowlist secret
        with self.assertRaises(ValueError):
            self.check()

    def test_external_templates_rejected(self) -> None:
        """Prevent external templates from bypassing the source allowlist."""
        self.franchises["external_templates"] = [{"default": "templates"}]
        with self.assertRaises(ValueError):
            self.check()

    def test_only_owner_favorites_active(self) -> None:
        """Retain only the owner's active favorites source."""
        yaml = YAML(typ="safe")
        favorites = yaml.load(Path("/workspace/movies/favorites.yml").read_text())
        self.assertEqual(list(favorites["collections"]), ["Edward's Favorite Movies"])
        self.assertFalse(Path("/workspace/shows/favorites.yml").exists())

    def test_writer_in_template_rejected(self) -> None:
        """Reject downloads inherited from the franchise template."""
        self.franchises["templates"]["franchise"]["radarr_add_missing"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_writer_in_definition_rejected(self) -> None:
        """Reject external list synchronization in a franchise definition."""
        self.franchises["collections"]["The Purge Collection"]["sync_to_trakt_list"] = (
            "example"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_custom_order_rejected(self) -> None:
        """Keep franchise ordering controlled by the release-order template."""
        self.franchises["collections"]["The Purge Collection"]["collection_order"] = (
            "custom"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_boolean_id_rejected(self) -> None:
        """Reject booleans despite Python treating them as integers."""
        self.franchises["collections"]["The Purge Collection"]["tmdb_collection"] = [
            True
        ]
        with self.assertRaises(ValueError):
            self.check()

    def test_template_override_rejected(self) -> None:
        """Prevent per-collection variables from enabling downloads."""
        self.franchises["collections"]["The Purge Collection"]["template"][
            "radarr_add_missing"
        ] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_smoke_writer_rejected(self) -> None:
        """Apply the same no-download boundary to smoke collections."""
        next(iter(self.smoke["collections"].values()))["radarr_add_missing"] = True
        with self.assertRaises(ValueError):
            self.check()

    #
    # Protect whole-series TV membership and its repository-owned ID lists.
    #
    def test_tv_episode_expansion_rejected(self) -> None:
        """Keep curated TV membership at the show level."""
        self.shows["templates"]["shuffle"]["builder_level"] = "episode"
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_template_writer_rejected(self) -> None:
        """Prevent TV templates from enabling Sonarr downloads."""
        self.shows["templates"]["shuffle"]["sonarr_add_missing"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_definition_writer_rejected(self) -> None:
        """Prevent TV definitions from writing to an external list."""
        self.shows["collections"]["Adult Animation"]["sync_to_trakt_list"] = "example"
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_external_source_rejected(self) -> None:
        """Reject user-list builders injected through the TV template."""
        self.shows["templates"]["shuffle"]["trakt_list"] = (
            "https://trakt.tv/users/example/lists/<<list_slug>>"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_template_override_rejected(self) -> None:
        """Reject unapproved variables in individual TV collections."""
        self.shows["collections"]["Adult Animation"]["template"]["list_slug"] = (
            "classic-sitcoms"
        )
        with self.assertRaises(ValueError):
            self.check()

    def test_tv_invalid_ids_rejected(self) -> None:
        """Reject invalid or repeated IDs in repository-owned show lists."""
        for ids in ([True], [0], [-1], ["60625"], [], [60625, 60625]):
            with self.subTest(ids=ids):
                self.shows["collections"]["Adult Animation"]["tmdb_show"] = ids
                with self.assertRaises(ValueError):
                    self.check()

    def test_tv_membership_counts(self) -> None:
        """Preserve the reviewed membership count of each curated TV list."""
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

    def test_will_and_grace_combined_series(self) -> None:
        """Use the combined series ID for original and revival seasons."""
        ids = self.shows["collections"]["Classic Sitcoms"]["tmdb_show"]
        self.assertIn(4454, ids)
        self.assertNotIn(74321, ids)

    def test_tv_id_comment_required(self) -> None:
        """Require a readable title comment beside every explicit show ID."""
        yaml = YAML()
        shows = yaml.load(Path("/workspace/shows/shuffle.yml").read_text())
        shows["collections"]["Adult Animation"]["tmdb_show"].ca.items.clear()
        with self.assertRaises(ValueError):
            preview.check_id_comments(shows["collections"], "tmdb_show")

    #
    # Treat the run summary as evidence only when every result is successful.
    #
    def test_successful_run_summary(self) -> None:
        """Accept documented successful and below-minimum summary states."""
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

    def test_failed_run_summary(self) -> None:
        """Reject provider failures and skipped scheduled collection runs."""
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

    def test_incomplete_run_summary(self) -> None:
        """Require a result row for every selected collection."""
        with self.assertRaises(ValueError):
            preview.check_run_summary("No summary rows", ["Adult Animation"])

    def test_tv_movie_builder_rejected(self) -> None:
        """Prevent movie builders from entering show-only collections."""
        self.shows["collections"]["Adult Animation"]["tmdb_movie"] = [1]
        with self.assertRaises(ValueError):
            self.check()

    #
    # Check production wiring without loading credentials or calling services.
    #
    def test_tv_sources_only_wired_to_tv(self) -> None:
        """Keep show sources in the TV library with Sonarr writes disabled."""
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

    def test_only_chronological_playlist_retained(self) -> None:
        """Retain the single mixed-media chronological playlist."""
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

    def test_radarr_override_only_for_weekly_chart(self) -> None:
        """Limit automatic Radarr additions and searches to the weekly chart."""
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


#
# Support direct execution inside the same isolated validation container.
#
if __name__ == "__main__":
    unittest.main()
