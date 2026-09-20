#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_collection_presentation.py: Guard viewer-facing prose and shared template behavior.
#

"""Exercise comment alignment and template expansion without network or Plex access."""

import copy
import importlib
import importlib.util
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML

#
# Load the formatter without running its CLI or touching private runtime files.
#
spec = importlib.util.spec_from_file_location(
    "yaml_comments", "/scripts/yaml-comments.py"
)
if spec is None or spec.loader is None:
    raise ImportError("The container must mount /scripts/yaml-comments.py.")
comments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comments)


class CollectionPresentationTests(unittest.TestCase):
    """Keep formatting and prose separate from membership, artwork, and scheduling."""

    def setUp(self) -> None:
        """Read only the tracked source snapshot and use Kometa's actual renderer."""
        self.root = Path("/workspace")
        self.yaml = YAML(typ="safe")
        importlib.import_module("modules.builder")
        self.meta = importlib.import_module("modules.meta")

    def render(self, source: dict, name: str, definition: dict) -> dict:
        """Expand local templates using the pinned runtime.

        Args:
            source: Parsed YAML with local templates.
            name: Collection title supplied to Kometa.
            definition: Collection attributes and template calls.

        Returns:
            Effective collection attributes with explicit values taking precedence.
        """
        renderer = self.meta.DataFile.__new__(self.meta.DataFile)
        renderer.templates = {
            key: (value, {}) for key, value in source["templates"].items()
        }
        renderer.library = SimpleNamespace(type="Movie", name="Fixture")
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

    #
    # Formatting must distinguish actual comments from string and block-scalar content.
    #
    def test_comment_alignment_preserves_values(self) -> None:
        """Pad short entries and leave two spaces after the longest adjacent entry."""
        source = "ids:\n  - 1  # First\n  - 12345    # Second\n\n  - 9   # Separate\n"
        expected = (
            "ids:\n  - 1      # First\n  - 12345  # Second\n\n  - 9  # Separate\n"
        )
        self.assertEqual(comments.align_comments(source), expected)
        self.assertEqual(self.yaml.load(source), self.yaml.load(expected))
        self.assertEqual(comments.align_comments(expected), expected)

    def test_hashes_and_standalone_comments_untouched(self) -> None:
        """Keep quoted hashes, literal blocks, and framed standalone comments intact."""
        source = 'color: "#0000"  # Transparent\nsummary: |\n  Text  # not a comment\n#\n# Section\n#\nvalue: 1  # Separate\n'
        self.assertEqual(comments.align_comments(source), source)

        #
        # Comment tokens can begin at a preceding scalar's end rather than at a hash.
        #
        source = "value: 1\n\n#\n# Next section\n#\nitems:\n  - value\n\n# Another section\nother: true\n"
        self.assertEqual(comments.align_comments(source), source)

    def test_all_yaml_inline_comments_aligned(self) -> None:
        """Enforce the same group alignment rule throughout tracked YAML."""
        for path in sorted(self.root.rglob("*.yml")) + sorted(
            self.root.rglob("*.yaml")
        ):
            with self.subTest(path=path.relative_to(self.root)):
                source = path.read_text()
                self.assertEqual(source, comments.align_comments(source))

    def test_summaries_are_viewer_facing(self) -> None:
        """Require concise prose without provider, sorting, or assembly commentary."""
        forbidden = re.compile(
            r"\b(?:this collection|our collection|a collection of|in (?:this|your|the) (?:plex )?library|"
            r"tmdb|imdb|metadata|keyword matching|vote thresholds?|sorted by|using .+ collection)\b",
            re.IGNORECASE,
        )
        summaries = []
        for folder in ("movies", "shows", "scheduled", "playlists"):
            for path in (self.root / folder).glob("*.yml"):
                source = self.yaml.load(path.read_text())
                templates = source.get("templates", {})
                for name, definition in source.get(
                    "collections", source.get("playlists", {})
                ).items():
                    if definition.get("build_collection") is False:
                        continue
                    calls = definition.get("template", [])
                    calls = [calls] if isinstance(calls, dict) else calls
                    inherited = next(
                        (
                            templates[call["name"]]["summary"]
                            for call in calls
                            if "summary" in templates.get(call["name"], {})
                        ),
                        None,
                    )
                    summary = definition.get("summary", inherited)
                    with self.subTest(file=path.name, collection=name):
                        self.assertIsInstance(summary, str)
                        self.assertGreater(len(summary.strip()), 10)
                    summaries.append(summary)
                summaries.extend(
                    t["summary"] for t in templates.values() if "summary" in t
                )

        #
        # Main-config overrides are viewer-facing too, including dynamic year summaries.
        #
        def collect(value: object) -> None:
            """Collect summary overrides without treating source comments as prose."""
            if isinstance(value, dict):
                for key, child in value.items():
                    if str(key).startswith("summary") and isinstance(child, str):
                        summaries.append(child)
                    else:
                        collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(self.yaml.load((self.root / "config.yml").read_text()))
        self.assertGreater(len(summaries), 200)
        for summary in summaries:
            with self.subTest(summary=summary):
                self.assertLessEqual(len(summary), 300)
                self.assertNotRegex(summary, forbidden)

    #
    # Compare effective behavior, not merely whether the YAML still parses.
    #
    def test_shared_people_template_preserves_each_role(self) -> None:
        """Retain role filters, metadata, artwork, ordering, and Saturday schedules."""
        source = self.yaml.load(
            (self.root / "movies/actors-directors-writers.yml").read_text()
        )
        self.assertNotIn("external_templates", source)
        for group, role in (
            ("Top Actors", "actor"),
            ("Top Directors", "director"),
            ("Top Writers", "writer"),
        ):
            dynamic = source["dynamic_collections"][group]
            call = {
                key: value["default"]
                for key, value in dynamic["template_variables"].items()
            }
            call.update(
                name=dynamic["template"][0], value=[31], key=31, key_name="Tom Hanks"
            )
            rendered = self.render(source, "Tom Hanks Collection", {"template": call})
            summary = rendered.pop("summary")
            with self.subTest(role=role):
                self.assertIn(f"{call['credit']} Tom Hanks", summary)
                self.assertNotIn("<<", summary)
                self.assertEqual(
                    rendered,
                    {
                        "tmdb_person": [31],
                        "file_poster": "/config/assets/posters/people/31.png",
                        "sort_title": "Tom Hanks",
                        "schedule": "weekly(saturday)",
                        "smart_filter": {
                            "sort_by": "release.desc",
                            "all": {role: "tmdb"},
                        },
                    },
                )

    def test_genre_schedule_override_preserved(self) -> None:
        """Keep the shared Tuesday schedule and Horror's explicit seasonal exception."""
        source = self.yaml.load((self.root / "movies/genres.yml").read_text())
        for name, definition in source["collections"].items():
            with self.subTest(collection=name):
                rendered = self.render(source, name, definition)
                expected = (
                    "range(11/01-09/14)"
                    if name == "Horror Movies"
                    else "weekly(tuesday)"
                )
                self.assertEqual(rendered["schedule"], expected)

    def test_theme_rating_defaults_shared(self) -> None:
        """Keep both provider defaults identical while preserving explicit overrides."""
        source = self.yaml.load(
            (self.root / "movies/top-rated-subgenres.yml").read_text()
        )
        templates = source["templates"]
        self.assertEqual(
            templates["tmdb_theme"]["default"], templates["imdb_theme"]["default"]
        )
        self.assertEqual(
            templates["tmdb_theme"]["default"],
            {"minimum_rating": 5, "minimum_votes": 1000},
        )
        for name, definition in source["collections"].items():
            rendered = self.render(source, name, definition)
            variables = definition["template"][1]
            builder, rating, votes = (
                ("tmdb_discover", "vote_average.gte", "vote_count.gte")
                if variables["name"] == "tmdb_theme"
                else ("imdb_search", "rating.gte", "votes.gte")
            )
            with self.subTest(collection=name):
                self.assertEqual(
                    rendered[builder][rating], variables.get("minimum_rating", 5)
                )
                self.assertEqual(
                    rendered[builder][votes], variables.get("minimum_votes", 1000)
                )


if __name__ == "__main__":
    unittest.main()
