#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_config_schema.py: Check supported editor fields and reject malformed overrides.
#

"""Exercise the generated upstream schema without credentials or service access."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "editor_schema", ROOT / "scripts/editor-schema.py"
)
if spec is None or spec.loader is None:
    raise ImportError("The repository editor-schema helper is required.")
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


class ConfigSchemaTests(unittest.TestCase):
    """Keep narrow compatibility fixes from becoming global schema exemptions."""

    def setUp(self) -> None:
        """Load only generated schema data and the public root configuration."""
        self.schema = json.loads(
            (ROOT / ".vscode/.schemas/config-schema.json").read_text()
        )
        self.config = YAML(typ="safe").load((ROOT / "config.yml").read_text())

    def variables(self, default: str, section: str = "collection_files") -> dict:
        """Return one movie Defaults call's variables for isolated mutation."""
        return next(
            item["template_variables"]
            for item in self.config["libraries"]["Movies"][section]
            if item.get("default") == default
        )

    def assert_invalid(self) -> None:
        """Require a real validation failure without exposing configuration contents."""
        self.assertTrue(editor.validation_errors(self.schema, self.config))

    def test_supported_source_passes(self) -> None:
        """Accept the actual supported overrides without rewriting runtime values."""
        self.assertFalse(editor.validation_errors(self.schema, self.config))

    def test_emoji_requires_text(self) -> None:
        """Reject a non-text emoji value instead of accepting arbitrary variables."""
        self.variables("seasonal")["emoji"] = 123
        self.assert_invalid()

    def test_veteran_list_requires_imdb_list(self) -> None:
        """Reject an unrelated URL in the narrowly supported seasonal list override."""
        self.variables("seasonal")["imdb_list_veteran"] = "https://example.invalid/"
        self.assert_invalid()

    def test_universe_requires_named_mapping(self) -> None:
        """Reject malformed universe additions without loosening other Defaults."""
        self.variables("universe")["append_data"] = ["Star Wars Saga"]
        self.assert_invalid()
        self.variables("universe")["append_data"] = {"star": "Star Wars Saga"}
        self.variables("studio")["append_data"] = {"star": "Star Wars Saga"}
        self.assert_invalid()

    def test_offsets_require_integers(self) -> None:
        """Reject malformed final positions while allowing the existing zero offsets."""
        for key in ("final_horizontal_offset", "final_vertical_offset"):
            with self.subTest(key=key):
                self.variables("resolution", "overlay_files")[key] = "sideways"
                self.assert_invalid()
                self.variables("resolution", "overlay_files")[key] = 0

    def test_unknown_variables_still_fail(self) -> None:
        """Reject misspelled overrides in every corrected template family."""

        #
        # Intentional misspellings exercise rejection instead of expanding the dictionary.
        # cspell:ignore emojii datta offest
        #
        for default, section, key in (
            ("seasonal", "collection_files", "emojii"),
            ("universe", "collection_files", "append_datta"),
            ("resolution", "overlay_files", "final_horizontal_offest"),
        ):
            with self.subTest(default=default):
                variables = self.variables(default, section)
                variables[key] = 0
                self.assert_invalid()
                del variables[key]

    def test_secret_urls_require_complete_placeholders(self) -> None:
        """Allow Kometa's URL substitution syntax, not arbitrary invalid addresses."""
        self.config["plex"]["url"] = "<<plexurl>>"
        self.assertFalse(editor.validation_errors(self.schema, self.config))
        self.config["plex"]["url"] = "not-a-url"
        self.assert_invalid()

    def test_adapter_does_not_mutate_input(self) -> None:
        """Keep the caller's upstream schema unchanged when constructing fixes."""
        original = copy.deepcopy(self.schema)
        editor.build_schema(self.schema)
        self.assertEqual(self.schema, original)

    #
    # Rating queues use named layouts accepted by both the editor schema and runtime.
    # Do not silence the editor's queue type check to accommodate the older list form.
    #
    def test_rating_queue_mappings_pass_upstream_schema(self) -> None:
        """Accept both real rating layouts and reject bare lists in the editor schema."""
        schema = json.loads((ROOT / ".vscode/.schemas/overlay-schema.json").read_text())
        for filename in ("overlays/ratings.yml", "overlays/test/ratings.yml"):
            with self.subTest(file=filename):
                source = YAML(typ="safe").load((ROOT / filename).read_text())
                self.assertFalse(editor.validation_errors(schema, source))
                source["queues"]["rating_queue_logo"] = source["queues"][
                    "rating_queue_logo"
                ]["default"]
                self.assertTrue(editor.validation_errors(schema, source))


if __name__ == "__main__":
    unittest.main()
