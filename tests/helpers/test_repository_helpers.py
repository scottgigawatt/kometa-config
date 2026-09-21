#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# test_repository_helpers.py: Check Make contracts and repository documentation.
#

"""Validate local automation and documentation without Docker or service access."""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]


class MakefileTests(unittest.TestCase):
    """Exercise real Make recipes using isolated command stubs."""

    def setUp(self) -> None:
        """Copy only the Makefile into a temporary directory with harmless helpers."""
        self.directory = tempfile.TemporaryDirectory(prefix="kometa-make-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copy2(ROOT / "Makefile", self.root / "Makefile")
        self.make = shutil.which("make")
        if not self.make:
            self.fail("GNU Make is required for helper tests.")
        self.stub = self.root / "stub.sh"
        self.stub.write_text(
            "#!/bin/sh\n"
            'printf "%s\\n" "$*" >> calls.txt\n'
            'printf "%s\\n" "$KOMETA_IMAGE|$TEST_ENV" > settings.txt\n'
            'case "$*" in\n'
            '  *trailing-whitespace*) exit "${STUB_FORMAT_STATUS:-0}" ;;\n'
            "esac\n"
            'exit "${STUB_STATUS:-0}"\n'
        )
        self.stub.chmod(0o700)
        self.env = {"PATH": os.defpath, "NO_COLOR": "1"}
        self.overrides = [
            f"{key}=./stub.sh {name}"
            for key, name in {
                "VALIDATE_CMD": "validate",
                "EDITOR_SCHEMA_CMD": "editor-schema",
                "EDITOR_SCHEMA_TEST_CMD": "editor-tests",
                "CHECK_GENERATED_CMD": "generated",
                "MAKE_HELPERS_TEST_CMD": "helpers",
                "PRE_COMMIT": "pre-commit",
                "LINT_CI_CMD": "lint-ci",
                "TEST_LIBRARY_CMD": "overlays",
                "TEST_COLLECTIONS_CMD": "collections",
            }.items()
        ]

    def run_make(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run Make against isolated stubs and capture output for assertions.

        Args:
            *args: Targets or variable overrides supplied to Make.

        Returns:
            The completed process, including its status and combined output.
        """
        return subprocess.run(
            [self.make, "--no-print-directory", *self.overrides, *args],
            cwd=self.root,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_default_is_help_only(self) -> None:
        """Show useful help without invoking helpers or emitting terminal escapes."""
        default = self.run_make()
        explicit = self.run_make("help")
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(default.stdout, explicit.stdout)
        self.assertNotIn("\x1b", default.stdout)
        self.assertFalse((self.root / "calls.txt").exists())
        for target in (
            "check",
            "validate",
            "test-library",
            "test-subgenres",
            "lint-ci",
        ):
            self.assertIn(target, default.stdout)

    def test_check_routes_all_local_gates(self) -> None:
        """Keep validation, generated-file policy, helper tests, and lint in check."""
        result = self.run_make("check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.root / "calls.txt").read_text().splitlines(),
            [
                "validate",
                "editor-schema",
                "editor-tests",
                "generated",
                "helpers",
                "pre-commit run --all-files",
            ],
        )

    def test_preview_scope_and_exports(self) -> None:
        """Preserve every preview flag and pass settings to helpers without printing them."""
        routes = {
            "test-library": "overlays",
            "test-collections": "collections",
            "test-subgenres": "collections --subgenres-only",
            "test-seasonal": "collections --seasonal-only",
            "test-tv-seasonal": "collections --tv-seasonal-only",
            "lint-ci": "lint-ci",
        }
        for target, expected in routes.items():
            with self.subTest(target=target):
                result = self.run_make(
                    target, "KOMETA_IMAGE=fixture-image", "TEST_ENV=fixture.env"
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    (self.root / "calls.txt").read_text().splitlines()[-1], expected
                )
                self.assertEqual(
                    (self.root / "settings.txt").read_text().strip(),
                    "fixture-image|fixture.env",
                )
                self.assertNotIn("fixture.env", result.stdout)

    def test_helper_failure_propagates(self) -> None:
        """Stop a failed local gate without running later checks or live previews."""
        self.env["STUB_STATUS"] = "7"
        result = self.run_make("check")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            (self.root / "calls.txt").read_text().splitlines(), ["validate"]
        )

    def test_format_runs_all_hooks_without_hiding_failure(self) -> None:
        """Continue safe formatting hooks but preserve an earlier failure status."""
        self.env["STUB_FORMAT_STATUS"] = "3"
        result = self.run_make("format")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            (self.root / "calls.txt").read_text().splitlines(),
            [
                f"pre-commit run {hook} --all-files"
                for hook in (
                    "trailing-whitespace",
                    "end-of-file-fixer",
                    "mixed-line-ending",
                )
            ],
        )


class DocumentationTests(unittest.TestCase):
    """Protect navigation and GitHub community-file discovery in sparse checkouts."""

    def setUp(self) -> None:
        """Use Git's tracked inventory without reading ignored runtime material."""
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.tracked = set(result.stdout.rstrip("\0").split("\0"))

    def test_community_files_live_in_docs(self) -> None:
        """Keep recognized community policies in docs rather than duplicate roots."""
        for name in (
            "CONTRIBUTING.md",
            "SECURITY.md",
            "SUPPORT.md",
            "CODE_OF_CONDUCT.md",
        ):
            with self.subTest(name=name):
                self.assertIn(f"docs/{name}", self.tracked)
                self.assertNotIn(name, self.tracked)
                self.assertNotIn(f".github/{name}", self.tracked)
        self.assertIn(".github/ISSUE_TEMPLATE/config.yml", self.tracked)
        for name in ("bug-report", "feature-request", "documentation-enhancement"):
            self.assertIn(f".github/ISSUE_TEMPLATE/{name}.md", self.tracked)

    def test_relative_markdown_links(self) -> None:
        """Resolve local Markdown destinations and headings without network requests."""
        for filename in sorted(self.tracked):
            source = ROOT / filename
            if source.suffix != ".md" or not source.is_file():
                continue
            text = re.sub(r"(?ms)^```.*?^```[^\n]*", "", source.read_text())
            for target in re.findall(
                r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", text
            ):
                link = urlsplit(target)
                if link.scheme or link.netloc:
                    continue
                destination = (
                    (source.parent / unquote(link.path)).resolve()
                    if link.path
                    else source
                )
                with self.subTest(source=filename, target=target):
                    relative = destination.relative_to(ROOT).as_posix()
                    exists = relative in self.tracked or any(
                        path.startswith(relative + "/") for path in self.tracked
                    )
                    self.assertTrue(
                        exists, f"Untracked or missing destination: {relative}"
                    )
                    if (
                        link.fragment
                        and destination.suffix == ".md"
                        and destination.is_file()
                    ):
                        headings = re.findall(
                            r"(?m)^#{1,6} (.+)$", destination.read_text()
                        )
                        anchors = {
                            re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
                            for heading in headings
                        }
                        self.assertIn(unquote(link.fragment), anchors)


if __name__ == "__main__":
    unittest.main()
