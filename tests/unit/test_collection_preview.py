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

import contextlib
import copy
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.themes = yaml.load(Path("/workspace/movies/subgenre-top.yml").read_text())

    #
    # Check rule-based membership and reject hidden source or template behavior.
    #
    def test_genre_and_theme_selection(self) -> None:
        """Select all seven genre rules and 101 supported theme searches."""
        names = preview.rule_names(self.genres, self.themes)
        self.assertEqual(len(names), 108)
        self.assertIn("LGBTQ+ Movies", names)
        self.assertIn("Top Rated in Mindfuck", names)

    def test_sunday_theme_keywords(self) -> None:
        """Keep each Sunday theme tied to its named native TMDb keywords."""
        expected = {
            "Vampires": "3133",
            "Video Game": "41645",
            "Werewolves": "12564",
            "Whodunit?": "12570",
            "Wizardry & Witchcraft": "616|177912",
            "World War": "2504|1956",
            "Zombies": "12377",
        }
        for theme, keywords in expected.items():
            with self.subTest(theme=theme):
                definition = self.themes["collections"][f"Top Rated in {theme}"]
                self.assertEqual(definition["template"][1]["keywords"], keywords)
                self.assertEqual(definition["schedule"], "weekly(sunday)")

    def test_whodunit_thresholds_preserved(self) -> None:
        """Reject changed or missing Whodunit rating and vote thresholds."""
        for key, value in (("minimum_rating", 5), ("minimum_votes", 1000)):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.themes)
                variables = changed["collections"]["Top Rated in Whodunit?"][
                    "template"
                ][1]
                variables[key] = value
                with self.assertRaises(ValueError):
                    preview.rule_names(self.genres, changed)
                del variables[key]
                with self.assertRaises(ValueError):
                    preview.rule_names(self.genres, changed)

    def test_other_theme_threshold_override_rejected(self) -> None:
        """Keep ordinary themes on the shared rating and vote floors."""
        self.themes["collections"]["Top Rated in Zombies"]["template"][1][
            "minimum_votes"
        ] = 100
        with self.assertRaises(ValueError):
            preview.rule_names(self.genres, self.themes)

    def test_theme_letterboxd_builder_rejected(self) -> None:
        """Reject reintroduced list dependencies in native theme definitions."""
        for key in ("letterboxd_list", "imdb_list", "trakt_list"):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.themes)
                changed["collections"]["Top Rated in Zombies"][key] = "list"
                with self.assertRaises(ValueError):
                    preview.rule_names(self.genres, changed)

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
        self.themes["templates"]["imdb_theme"]["imdb_search"]["list.any"] = "ls12345"
        with self.assertRaises(ValueError):
            preview.rule_names(self.genres, self.themes)

    def test_genre_and_subgenre_sources_have_no_trakt(self) -> None:
        """Keep movie genre and theme sources independent of Trakt lists."""
        for name in ("genre.yml", "subgenre-top.yml"):
            self.assertNotIn(
                "trakt", Path("/workspace/movies", name).read_text().lower()
            )

    def test_theme_personal_lists_are_absent(self) -> None:
        """Keep the complete theme source free of personal-list dependencies."""
        text = Path("/workspace/movies/subgenre-top.yml").read_text().lower()
        for marker in ("letterboxd", "trakt", "imdb_list", "mdblist"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)

    #
    # Exercise the scoped CLI without credentials, network access, or Plex writes.
    #
    def test_subgenre_command_targets_only_movie_themes(self) -> None:
        """Restrict the live command to all 101 themes in the movie fixture."""
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            runtime.joinpath("config.yml").write_text(
                Path("/workspace/tests/kometa/collections-config.yml").read_text()
            )

            def mapped_path(value: str) -> Path:
                """Redirect private runtime writes into disposable scratch space."""
                return (
                    runtime / value[8:] if value.startswith("/config/") else Path(value)
                )

            def completed_run(*args, **kwargs) -> None:
                """Supply a successful summary without starting a real process."""
                runtime.joinpath("logs").mkdir()
                runtime.joinpath("logs/meta.log").write_text(
                    "\n".join(
                        f"| {name} | 1 | 1 | 0 | 0 | Created |"
                        for name in self.themes["collections"]
                    )
                )

            with (
                patch(
                    "sys.argv", ["collection-preview.py", "--run", "--subgenres-only"]
                ),
                patch.object(preview, "Path", side_effect=mapped_path),
                patch.object(
                    preview.subprocess, "run", side_effect=completed_run
                ) as run,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                preview.main()
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ["--libraries", "test_movie_lib"])
            self.assertEqual(
                command[command.index("--run-collections") + 1],
                "|".join(self.themes["collections"]),
            )
            self.assertIn("--collections-only", command)
            self.assertIn("--ignore-schedules", command)

    def test_conflicting_subgenre_scopes_rejected(self) -> None:
        """Reject combined scopes before loading any preview sources."""
        for flag in ("--seasonal-only", "--tv-seasonal-only"):
            with (
                self.subTest(flag=flag),
                patch("sys.argv", ["collection-preview.py", "--subgenres-only", flag]),
                patch.object(preview, "load_preview") as load,
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                preview.main()
            self.assertEqual(error.exception.code, 2)
            load.assert_not_called()

    #
    # Freeze public identity and presentation independently of provider membership.
    # These expectations catch accidental removals and flattened rating thresholds.
    #
    def test_all_theme_contracts_preserved(self) -> None:
        """Preserve all names, poster mappings, schedules, and rating floors."""
        expected = {
            "Absurdism": ("absurdism", "weekly(monday)", 5, 1000),
            "Aliens": ("aliens", "weekly(monday)", 5, 1000),
            "Alternate History": ("alternate-history", "weekly(monday)", 5, 1000),
            "Anti-Hero": ("anti-hero", "weekly(monday)", 5, 1000),
            "Apocalypse": ("apocalypse", "weekly(monday)", 5, 1000),
            "Artificial Intelligence": (
                "artificial-intelligence",
                "weekly(monday)",
                5,
                1000,
            ),
            "Assassins": ("assassins", "weekly(monday)", 5, 1000),
            "Betrayal": ("betrayal", "weekly(monday)", 5, 1000),
            "Bigfoot": ("bigfoot", "weekly(monday)", 5, 500),
            "Boxing": ("boxing", "weekly(monday)", 2, 100),
            "Bugs": ("bugs", "weekly(monday)", 2, 100),
            "Cannibals": ("cannibals", "weekly(monday)", 2, 100),
            "Caper": ("caper", "weekly(monday)", 5, 100),
            "Chick-flick": ("chick-flick", "weekly(monday)", 5, 100),
            "Comics": ("comics", "weekly(tuesday)", 5, 1000),
            "Coming of Age": ("coming-of-age", "weekly(tuesday)", 5, 1000),
            "Con-Artists": ("con-artists", "weekly(tuesday)", 2, 1000),
            "Cop": ("cop", "weekly(tuesday)", 2, 1000),
            "Costume Drama": ("costume-drama", "weekly(tuesday)", 5, 1000),
            "Courtroom": ("courtroom", "weekly(tuesday)", 5, 1000),
            "Cyberpunk": ("cyberpunk", "weekly(tuesday)", 5, 1000),
            "Dark Comedy": ("dark-comedy", "weekly(monday)", 5, 1000),
            "Dark Fantasy": ("dark-fantasy", "weekly(tuesday)", 5, 1000),
            "Detective": ("detective", "weekly(tuesday)", 5, 1000),
            "Disaster": ("disaster", "weekly(tuesday)", 5, 1000),
            "Dragons": ("dragons", "weekly(tuesday)", 3, 1000),
            "Dystopian": ("dystopian", "weekly(tuesday)", 5, 1000),
            "Epics": ("epics", "weekly(tuesday)", 5, 1000),
            "Espionage": ("espionage", "weekly(tuesday)", 5, 1000),
            "Experimental": ("experimental", "weekly(wednesday)", 3, 1000),
            "Fairytales": ("fairytales", "weekly(wednesday)", 5, 1000),
            "Found Footage": ("found-footage", "weekly(wednesday)", 2, 1000),
            "Fugitives": ("fugitives", "weekly(wednesday)", 5, 1000),
            "Gangster": ("gangster", "weekly(wednesday)", 5, 1000),
            "Ghosts": ("ghosts", "weekly(wednesday)", 5, 1000),
            "Gothic": ("gothic", "weekly(wednesday)", 2, 100),
            "Heartbreak": ("heartbreak", "weekly(wednesday)", 1, 10),
            "Heists": ("heists", "weekly(wednesday)", 5, 1000),
            "Historical Event": ("historical-event", "weekly(wednesday)", 5, 1000),
            "Hostage": ("hostage", "weekly(wednesday)", 5, 1000),
            "Hustle": ("hustle", "weekly(wednesday)", 5, 1000),
            "Martial-Arts": ("martial-arts", "weekly(wednesday)", 5, 1000),
            "Medical": ("medical", "weekly(wednesday)", 2, 100),
            "Medieval": ("medieval", "weekly(wednesday)", 5, 1000),
            "Melodrama": ("melodrama", "weekly(thursday)", 5, 1000),
            "Military": ("military", "weekly(thursday)", 2, 1000),
            "Mindfuck": ("mindfuck", "weekly(thursday)", 5, 1000),
            "Mockumentary": ("mockumentary", "weekly(thursday)", 2, 1000),
            "Monsters": ("monsters", "weekly(thursday)", 5, 1000),
            "Mythology": ("mythology", "weekly(thursday)", 5, 1000),
            "Naval": ("naval", "weekly(thursday)", 2, 1000),
            "Ninjas": ("ninjas", "weekly(thursday)", 5, 1000),
            "Novel": ("novel", "weekly(thursday)", 5, 1000),
            "Occult": ("occult", "weekly(thursday)", 5, 1000),
            "Outerspace": ("outerspace", "weekly(thursday)", 5, 1000),
            "Outlaw": ("outlaw", "weekly(thursday)", 2, 100),
            "Pandemic": ("pandemic", "weekly(thursday)", 2, 1000),
            "Paranormal": ("paranormal", "weekly(thursday)", 5, 1000),
            "Period Drama": ("period-drama", "weekly(friday)", 5, 1000),
            "Philosophical": ("philosophical", "weekly(friday)", 5, 1000),
            "Political": ("political", "weekly(friday)", 5, 1000),
            "Post-Apocalyptic": ("post-apocalyptic", "weekly(friday)", 5, 1000),
            "Prehistoric": ("prehistoric", "weekly(friday)", 2, 1000),
            "Prison": ("prison", "weekly(friday)", 2, 100),
            "Psychedelic": ("psychedelic", "weekly(friday)", 2, 1000),
            "Psychological": ("psychological", "weekly(friday)", 2, 1000),
            "Religion": ("religion", "weekly(friday)", 2, 100),
            "Remake": ("remake", "weekly(friday)", 5, 100),
            "Revenge": ("revenge", "weekly(friday)", 3, 1000),
            "Robots": ("robots", "weekly(friday)", 3, 1000),
            "Romantic Comedy": ("romantic-comedy", "weekly(friday)", 5, 1000),
            "Romantic Drama": ("romantic-drama", "weekly(friday)", 5, 1000),
            "Samurai": ("samurai", "weekly(friday)", 2, 100),
            "Satire": ("satire", "weekly(friday)", 5, 1000),
            "Serial Killers": ("serial-killers", "weekly(saturday)", 5, 1000),
            "Slasher": ("slasher", "weekly(saturday)", 5, 1000),
            "Space Opera": ("space-opera", "weekly(saturday)", 2, 1000),
            "Spaghetti Western": ("spaghetti-western", "weekly(saturday)", 1, 10),
            "Splatter": ("splatter", "weekly(saturday)", 2, 1000),
            "Steampunk": ("steampunk", "weekly(saturday)", 5, 1000),
            "Stoner": ("stoner", "weekly(saturday)", 1, 1000),
            "Stop-Motion": ("stop-motion", "weekly(saturday)", 5, 100),
            "Superhero": ("superhero", "weekly(saturday)", 5, 1000),
            "Supernatural": ("supernatural", "weekly(saturday)", 5, 1000),
            "Surrealism": ("surrealism", "weekly(saturday)", 5, 1000),
            "Survival": ("survival", "weekly(saturday)", 5, 1000),
            "Swashbuckler": ("swashbuckler", "weekly(saturday)", 2, 100),
            "Sword & Sandal": ("sword-sandal", "weekly(saturday)", 3, 1000),
            "Sword & Sorcery": ("sword-sorcery", "weekly(saturday)", 3, 1000),
            "Time Travel": ("time-travel", "weekly(sunday)", 5, 1000),
            "Treasure Hunt": ("treasure-hunt", "weekly(sunday)", 2, 100),
            "True Story": ("true-story", "weekly(sunday)", 5, 1000),
            "Urban Fantasy": ("urban-fantasy", "weekly(sunday)", 5, 1000),
            "Utopian": ("utopian", "weekly(sunday)", 5, 1000),
            "Vampires": ("vampires", "weekly(sunday)", 5, 1000),
            "Video Game": ("video-game", "weekly(sunday)", 5, 1000),
            "Werewolves": ("werewolves", "weekly(sunday)", 5, 1000),
            "Whodunit?": ("whodunit", "weekly(sunday)", 2, 100),
            "Wizardry & Witchcraft": ("wizardry-witchcraft", "weekly(sunday)", 5, 1000),
            "World War": ("world-war", "weekly(sunday)", 5, 1000),
            "Zombies": ("zombies", "weekly(sunday)", 5, 1000),
        }
        self.assertEqual(
            set(self.themes["collections"]),
            {f"Top Rated in {theme}" for theme in expected},
        )
        for theme, (poster, schedule, rating, votes) in expected.items():
            with self.subTest(theme=theme):
                definition = self.themes["collections"][f"Top Rated in {theme}"]
                variables = definition["template"][1]
                self.assertEqual(
                    definition["file_poster"],
                    f"/config/assets/posters/subgenre_top/subgenre_top_{poster}.png",
                )
                self.assertEqual(definition["schedule"], schedule)
                self.assertEqual(variables.get("minimum_rating", 5), rating)
                self.assertEqual(variables.get("minimum_votes", 1000), votes)

    def test_theme_templates_reject_list_builders(self) -> None:
        """Reject external lists and writers inherited by any shared template."""
        for template in self.themes["templates"]:
            for key in (
                "letterboxd_list",
                "imdb_list",
                "trakt_list",
                "mdblist_list",
                "radarr_search",
            ):
                with self.subTest(template=template, key=key):
                    changed = copy.deepcopy(self.themes)
                    changed["templates"][template][key] = "unexpected"
                    with self.assertRaises(ValueError):
                        preview.rule_names(self.genres, changed)

    def test_native_query_boundaries(self) -> None:
        """Keep synonyms as alternatives and romantic genres as intersections."""
        expected = {
            "Aliens": {"keywords": "9951|14909"},
            "Anti-Hero": {"keywords": "2095"},
            "Coming of Age": {"keywords": "10683"},
            "Robots": {"keywords": "14544|10891"},
            "Romantic Comedy": {"genres": "10749,35"},
            "Romantic Drama": {"genres": "10749,18"},
            "Utopian": {"keywords": "3469", "excluded_keywords": "4565"},
        }
        for theme, query in expected.items():
            variables = self.themes["collections"][f"Top Rated in {theme}"]["template"][
                1
            ]
            for key, value in query.items():
                with self.subTest(theme=theme, key=key):
                    self.assertEqual(variables[key], value)

    def test_unbounded_theme_search_rejected(self) -> None:
        """Reject a TMDb theme with no keyword or genre restriction."""
        del self.themes["collections"]["Top Rated in Zombies"]["template"][1][
            "keywords"
        ]
        with self.assertRaises(ValueError):
            preview.rule_names(self.genres, self.themes)

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
        self.assertEqual(len(selected), 153)
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
