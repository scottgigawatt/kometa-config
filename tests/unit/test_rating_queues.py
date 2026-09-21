#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_rating_queues.py: Preserve rating positions through schema-compatible queue layouts.
#

"""Exercise Kometa's real queue parser without loading services or rendering artwork."""

import copy
import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ruamel.yaml import YAML


class RatingQueueTests(unittest.TestCase):
    """Keep named layouts equivalent to their original list-based positions."""

    def setUp(self) -> None:
        """Load the pinned parser and public source snapshot without credentials."""
        importlib.import_module("modules.builder")
        self.meta = importlib.import_module("modules.meta")
        self.root = Path("/workspace")

    def parse_queues(self, source: dict) -> tuple[dict, dict]:
        """Parse queues with real Kometa code while isolating file and template loading.

        Args:
            source: An in-memory overlay document containing the queue definitions.

        Returns:
            The parsed coordinates and queue-name mapping produced by Kometa.
        """
        with (
            patch.object(self.meta, "logger", Mock()),
            patch.object(self.meta.DataFile, "load_file", return_value=source),
            patch.object(self.meta.DataFile, "external_templates"),
        ):
            result = self.meta.OverlayFile(
                SimpleNamespace(requested_files=[]),
                SimpleNamespace(overlay_files=[]),
                "File",
                "ratings.yml",
                {},
                None,
                0,
            )
        return result.queues, result.queue_names

    #
    # Compare the two source layouts with their former list representation through
    # the pinned runtime, not a local copy of the queue-selection logic.
    #
    def test_named_layouts_preserve_positions(self) -> None:
        """Keep queue coordinates, ordering, and names unchanged in both rating files."""
        for filename in ("overlays/ratings.yml", "overlays/test/ratings.yml"):
            with self.subTest(file=filename):
                source = YAML(typ="safe").load((self.root / filename).read_text())
                previous = copy.deepcopy(source)
                previous["queues"] = {
                    name: layout["default"] for name, layout in source["queues"].items()
                }
                current = self.parse_queues(source)
                self.assertEqual(current, self.parse_queues(previous))
                self.assertEqual(len(current[0]), 2)
                self.assertTrue(all(len(queue) == 2 for queue in current[0].values()))

    def test_invalid_coordinates_still_fail(self) -> None:
        """Reject a malformed queue position instead of hiding it behind the mapping."""
        source = YAML(typ="safe").load(
            (self.root / "overlays/test/ratings.yml").read_text()
        )
        source["queues"]["rating_queue_logo"]["default"][0]["horizontal_align"] = (
            "sideways"
        )
        with self.assertRaises(self.meta.Failed):
            self.parse_queues(source)


if __name__ == "__main__":
    unittest.main()
