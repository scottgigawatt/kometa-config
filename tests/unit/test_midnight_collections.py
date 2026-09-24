#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_midnight_collections.py: Protect local discovery membership and preview isolation.
#

"""Exercise Midnight Cinema safety boundaries with the pinned Kometa renderer."""

import contextlib
import copy
import importlib
import importlib.util
import io
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from modules import util
from modules.tmdb import TMDb
from ruamel.yaml import YAML

#
# Import the mounted guard without invoking its Plex-mutating command line.
#
spec = importlib.util.spec_from_file_location(
    "midnight_preview", "/scripts/collection-preview.py"
)
if spec is None or spec.loader is None:
    raise ImportError("The container must mount /scripts/collection-preview.py.")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class MidnightCollectionTests(unittest.TestCase):
    """Keep curated discovery independent of external lists and production writes."""

    def setUp(self) -> None:
        """Preserve round-trip comments and isolate each source mutation."""
        self.root = Path("/workspace")
        self.yaml = YAML()
        self.sources = {
            filename: self.yaml.load((self.root / filename).read_text())
            for filename in (
                "movies/midnight-curated.yml",
                "movies/midnight-discovery.yml",
                "shows/midnight-cinema.yml",
            )
        }
        self.curated = self.sources["movies/midnight-curated.yml"]
        self.discovery = self.sources["movies/midnight-discovery.yml"]
        self.television = self.sources["shows/midnight-cinema.yml"]
        self.production = self.yaml.load((self.root / "config.yml").read_text())
        importlib.import_module("modules.builder")
        self.meta = importlib.import_module("modules.meta")

    def render(self, source: dict, name: str, media_type: str) -> dict:
        """Expand a definition with Kometa's renderer rather than string substitution.

        Args:
            source: Local collection file including its templates.
            name: Collection whose effective attributes are required.
            media_type: Plex library media type supplied to the renderer.

        Returns:
            Expanded template attributes with collection overrides applied.
        """
        definition = source["collections"][name]
        renderer = self.meta.DataFile.__new__(self.meta.DataFile)
        renderer.templates = {
            key: (value, {}) for key, value in source["templates"].items()
        }
        renderer.library = SimpleNamespace(type=media_type, name="Fixture")
        renderer.data_type = "Collection"
        renderer.temp_vars = {}
        with patch.object(self.meta, "logger", Mock()):
            result = renderer.apply_template(
                None, name, definition, copy.deepcopy(definition["template"]), {}
            )
        result.update(
            {key: value for key, value in definition.items() if key != "template"}
        )
        return result

    def test_all_sources_pass_and_allow_catalog_growth(self) -> None:
        """Validate current sources without freezing their titles or catalog size."""
        names = []
        for source in self.sources.values():
            names.extend(preview.midnight_names(source))
        self.assertEqual(preview.load_midnight(self.root), names)
        self.assertEqual(len(names), len(set(names)))

    def test_external_source_keys_are_rejected(self) -> None:
        """Reject remote includes before they can supply hidden collection behavior."""
        for key in ("external_templates", "dynamic_collections", "metadata"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.curated)
                changed[key] = {"url": "https://example.invalid/source.yml"}
                with self.assertRaises(ValueError):
                    preview.midnight_names(changed)

    def test_external_builders_and_writers_are_rejected(self) -> None:
        """Reject side effects and transient lists in definitions and inherited templates."""
        for key in (
            "letterboxd_list",
            "trakt_list",
            "imdb_list",
            "mdblist_list",
            "radarr_add_missing",
            "radarr_search",
            "sonarr_add_missing",
            "sync_to_trakt_list",
            "item_label",
            "changes_webhooks",
            "url_poster",
        ):
            for inherited in (False, True):
                with self.subTest(key=key, inherited=inherited):
                    changed = copy.deepcopy(self.curated)
                    group = changed["templates" if inherited else "collections"]
                    next(iter(group.values()))[key] = True
                    with self.assertRaises(ValueError):
                        preview.midnight_names(changed)

    def test_unknown_local_template_is_rejected(self) -> None:
        """Do not silently accept unresolved or externally supplied template names."""
        definition = next(iter(self.curated["collections"].values()))
        definition["template"]["name"] = "remote-template"
        with self.assertRaises(ValueError):
            preview.midnight_names(self.curated)

    def test_shared_home_overrides_are_rejected(self) -> None:
        """Fixture collections must stay off home screens even through overrides."""
        for key in ("visible_home", "visible_shared"):
            for inherited in (False, True):
                with self.subTest(key=key, inherited=inherited):
                    changed = copy.deepcopy(self.curated)
                    group = changed["templates" if inherited else "collections"]
                    next(iter(group.values()))[key] = True
                    with self.assertRaises(ValueError):
                        preview.midnight_names(changed)

    def test_invalid_and_duplicate_movie_or_show_ids_are_rejected(self) -> None:
        """Reject IDs that can silently select a wrong title or duplicate a builder."""
        for original, builder in (
            (self.curated, "tmdb_movie"),
            (self.television, "tmdb_show"),
        ):
            for bad in ([True], [0], [-1], ["123"], [], [123, 123]):
                with self.subTest(builder=builder, ids=bad):
                    changed = copy.deepcopy(original)
                    definition = next(
                        v for v in changed["collections"].values() if builder in v
                    )
                    definition[builder] = bad
                    with self.assertRaises(ValueError):
                        preview.midnight_names(changed)

    def test_id_comments_are_required(self) -> None:
        """Keep static membership reviewable when a movie or show is added."""
        for original, builder in (
            (self.curated, "tmdb_movie"),
            (self.television, "tmdb_show"),
        ):
            with self.subTest(builder=builder):
                changed = copy.deepcopy(original)
                definition = next(
                    v for v in changed["collections"].values() if builder in v
                )
                definition[builder].ca.items.clear()
                with self.assertRaises(ValueError):
                    preview.midnight_names(changed)

    def test_story_arcs_reject_untyped_remote_and_invalid_episode_references(
        self,
    ) -> None:
        """Allow only explicit positive episode references in local story arcs."""
        for references in (
            ["https://example.invalid/episodes.txt"],
            ["71470"],
            ["tmdb_movie:15"],
            ["tvdb_episode:0_2_16"],
            ["tvdb_episode:71470_-1_16"],
            ["tvdb_episode:71470_2_0"],
            ["tvdb_episode:71470_2_16", "tvdb_episode:71470_2_16"],
        ):
            with self.subTest(references=references):
                changed = copy.deepcopy(self.television)
                definition = next(
                    v for v in changed["collections"].values() if "text" in v
                )
                definition["text"] = references
                with self.assertRaises(ValueError):
                    preview.midnight_names(changed)

    def test_story_arc_cannot_run_at_show_level(self) -> None:
        """Episode references must not become whole-show collection membership."""
        definition = next(
            v for v in self.television["collections"].values() if "text" in v
        )
        definition["builder_level"] = "show"
        with self.assertRaises(ValueError):
            preview.midnight_names(self.television)

    def test_episode_minimum_is_rejected_directly_and_through_templates(self) -> None:
        """Reject minimum_items on episode collections before Kometa rejects the run."""
        episode_names = [
            name
            for name, definition in self.television["collections"].items()
            if definition.get("builder_level") == "episode"
        ]
        self.assertTrue(episode_names)
        for name in episode_names:
            for inherited in (False, True):
                with self.subTest(collection=name, inherited=inherited):
                    changed = copy.deepcopy(self.television)
                    definition = changed["collections"][name]
                    target = (
                        changed["templates"][definition["template"]["name"]]
                        if inherited
                        else definition
                    )
                    target["minimum_items"] = 3
                    with self.assertRaises(ValueError):
                        preview.midnight_names(changed)

    def test_empty_search_tolerance_stays_scoped_to_episode_highlights(self) -> None:
        """Permit expected empty per-show searches without broadening failure tolerance."""
        for name in self.television["collections"]:
            for value in (True, False, "true", 1):
                if name == "TV's Greatest Episodes" and value is True:
                    continue
                with self.subTest(collection=name, value=value):
                    changed = copy.deepcopy(self.television)
                    changed["collections"][name]["ignore_blank_results"] = value
                    with self.assertRaises(ValueError):
                        preview.midnight_names(changed)
        changed = copy.deepcopy(self.television)
        changed["templates"]["midnight"]["ignore_blank_results"] = True
        with self.assertRaises(ValueError):
            preview.midnight_names(changed)

    def test_effective_poster_and_sort_overrides_are_rejected(self) -> None:
        """Check final collection presentation rather than trusting only templates."""
        for key, value in (
            ("file_poster", "https://example.invalid/poster.jpg"),
            ("file_poster", "/config/assets/posters/midnight-cinema/../other.jpg"),
            ("sort_title", "!019_Escaped"),
        ):
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(self.curated)
                next(iter(changed["collections"].values()))[key] = value
                with self.assertRaises(ValueError):
                    preview.midnight_names(changed)

    def test_poster_template_variable_cannot_escape(self) -> None:
        """Reject path traversal hidden inside an otherwise local poster template."""
        for value in ("../escape", "/tmp/escape", "<<external>>"):
            with self.subTest(value=value):
                changed = copy.deepcopy(self.curated)
                next(iter(changed["collections"].values()))["template"]["poster"] = (
                    value
                )
                with self.assertRaises(ValueError):
                    preview.midnight_names(changed)

    def test_production_folder_loading_covers_correct_media(self) -> None:
        """Autoload movie and TV definitions exactly once in their intended libraries."""
        for library, folder in (("Movies", "movies"), ("TV Shows", "shows")):
            with self.subTest(library=library):
                files = self.production["libraries"][library]["collection_files"]
                self.assertEqual(
                    sum(item.get("folder") == f"config/{folder}/" for item in files), 1
                )
                self.assertFalse(
                    any("midnight" in item.get("file", "") for item in files)
                )

    def test_rendered_block_sorts_after_tracearr_before_charts(self) -> None:
        """Keep every rendered title and poster stable within its media-specific block."""
        for library, prefix, media_type in (
            ("Movies", "movies/", "Movie"),
            ("TV Shows", "shows/", "Show"),
        ):
            with self.subTest(library=library):
                tracearr = next(
                    item
                    for item in self.production["libraries"][library][
                        "collection_files"
                    ]
                    if item.get("default") == "tracearr"
                )
                self.assertEqual(
                    tracearr["template_variables"]["collection_section"], "020_1"
                )
                titles = []
                posters = []
                for filename, source in self.sources.items():
                    if not filename.startswith(prefix):
                        continue
                    for name in source["collections"]:
                        rendered = self.render(source, name, media_type)
                        title = rendered["sort_title"]
                        self.assertRegex(title, r"^!020_2_\d{2}_")
                        self.assertGreater(title, "!020_1_zzzz")
                        self.assertLess(title, "!03")
                        self.assertNotIn("<<", rendered["file_poster"])
                        self.assertTrue(
                            rendered["file_poster"].startswith(
                                "/config/assets/posters/midnight-cinema/"
                            )
                        )
                        self.assertIs(rendered["visible_home"], False)
                        self.assertIs(rendered["visible_shared"], False)
                        if rendered.get("builder_level") == "episode":
                            self.assertNotIn("minimum_items", rendered)
                        else:
                            self.assertEqual(rendered["minimum_items"], 3)
                        titles.append(title)
                        posters.append(rendered["file_poster"])
                self.assertEqual(titles, sorted(titles))
                self.assertEqual(len(posters), len(set(posters)))

    def test_hidden_gems_native_search_and_sampling_contract(self) -> None:
        """Search owned unwatched older movies before applying the final discovery cap."""
        definition = self.discovery["collections"]["Hidden Gems"]
        self.assertEqual(
            definition["plex_search"]["all"], {"unplayed": True, "release.not": 730}
        )
        self.assertEqual(definition["plex_search"]["sort_by"], "random")
        self.assertGreater(definition["plex_search"]["limit"], definition["limit"])
        self.assertEqual(definition["limit"], 25)
        self.assertEqual(
            definition["filters"],
            {
                "tmdb_vote_average.gte": 7,
                "tmdb_vote_count.gte": 100,
                "tmdb_vote_count.lte": 2500,
            },
        )

    def test_hidden_gems_provider_rating_and_vote_boundaries(self) -> None:
        """Accept exact rating and vote bounds, excluding sparse or mainstream outliers."""
        provider = object.__new__(TMDb)
        filters = self.discovery["collections"]["Hidden Gems"]["filters"]
        for rating, votes, expected in (
            (7, 100, True),
            (7, 2500, True),
            (6.9, 100, False),
            (7, 99, False),
            (7, 2501, False),
        ):
            with self.subTest(rating=rating, votes=votes):
                movie = SimpleNamespace(vote_average=rating, vote_count=votes)
                checks = [
                    (key.rsplit(".", 1)[0], "." + key.rsplit(".", 1)[1], key, value)
                    for key, value in filters.items()
                ]
                actual = all(
                    provider.item_filter(movie, key, modifier, final, value, True, None)
                    for key, modifier, final, value in checks
                )
                self.assertEqual(actual, expected)

    def test_hidden_gems_age_excludes_recent_and_undated_movies(self) -> None:
        """Treat the rolling age threshold as exclusive and reject missing release dates."""
        days = self.discovery["collections"]["Hidden Gems"]["plex_search"]["all"][
            "release.not"
        ]
        now = datetime(2026, 9, 23, tzinfo=UTC)
        for age, excluded in (
            (days - 1, True),
            (days, True),
            (days + 1, False),
            (None, True),
        ):
            with self.subTest(age=age):
                date = now - timedelta(days=age) if age is not None else None
                self.assertEqual(
                    util.is_date_filter(date, ".not", days, "release.not", now),
                    excluded,
                )

    def test_alternate_editions_use_exact_owned_edition_metadata(self) -> None:
        """Avoid matching a movie title or every loosely named special edition."""
        definition = self.discovery["collections"][
            "Director's Cuts & Extended Editions"
        ]
        search = definition["plex_search"]
        self.assertEqual(set(search), {"any"})
        self.assertEqual(set(search["any"]), {"edition.is"})
        editions = search["any"]["edition.is"]
        self.assertIn("Director's Cut", editions)
        self.assertIn("Extended Edition", editions)
        self.assertNotIn("Special Edition", editions)
        self.assertNotIn("Theatrical", editions)

    def test_midnight_cli_runs_only_named_fixture_collections(self) -> None:
        """Exercise the live CLI path with a fake process and disposable runtime files."""
        names = preview.load_midnight(self.root)
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            runtime.joinpath("config.yml").write_text(
                (self.root / "tests/kometa/collections-config.yml").read_text()
            )

            def mapped_path(value: str) -> Path:
                """Redirect runtime writes while retaining real public source reads."""
                return (
                    runtime / value[8:] if value.startswith("/config/") else Path(value)
                )

            def completed_run(*args, **kwargs) -> None:
                """Create a fresh successful log without connecting to any Plex server."""
                runtime.joinpath("logs").mkdir()
                runtime.joinpath("logs/meta.log").write_text(
                    "\n".join(f"| {name} | 1 | 1 | 0 | 0 | Created |" for name in names)
                )

            with (
                patch(
                    "sys.argv", ["collection-preview.py", "--run", "--midnight-only"]
                ),
                patch.object(preview, "Path", side_effect=mapped_path),
                patch.object(
                    preview.subprocess, "run", side_effect=completed_run
                ) as run,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                preview.main()
            command = run.call_args.args[0]
            self.assertEqual(
                command[command.index("--run-collections") + 1], "|".join(names)
            )
            self.assertIn("--collections-only", command)
            self.assertIn("--no-missing", command)
            self.assertIn("--read-only-config", command)
            self.assertNotIn("--run-files", command)
            self.assertNotIn("--libraries", command)
            self.assertEqual(run.call_count, 1)

    def test_midnight_cli_rejects_competing_scopes_before_loading(self) -> None:
        """Do not let combined switches accidentally widen a scoped fixture run."""
        for flag in ("--seasonal-only", "--tv-seasonal-only", "--subgenres-only"):
            with (
                self.subTest(flag=flag),
                patch("sys.argv", ["collection-preview.py", "--midnight-only", flag]),
                patch.object(preview, "load_preview") as load,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                preview.main()
            self.assertEqual(error.exception.code, 2)
            load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
