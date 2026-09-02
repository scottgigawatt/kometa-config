#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# Makefile: Provide one documented interface for repository validation and the
#           isolated Plex test-library workflow.
#

KOMETA_IMAGE ?= kometateam/kometa:v2.4.8@sha256:c58f6d4af511613f218b6dafbfc84078af4e5a6089790c1fdba58fd7c5dad70a
TEST_ENV ?= .secrets/test.env

export KOMETA_IMAGE
export TEST_ENV

.DEFAULT_GOAL := help

.PHONY: check check-generated format help lint lint-ci test-library validate

#
# help: List the supported repository commands.
#
# Dependencies: None.
#
help:
	@awk 'BEGIN {FS = ":.*# "} /^[a-zA-Z0-9_-]+:.*# / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

#
# check: Run every local validation gate used by the pull-request workflow.
#
# Dependencies: validate, check-generated, lint.
#
check: validate check-generated lint  # Run all repository checks.

#
# validate: Validate repository YAML with Kometa's pinned schema validator.
#
# Dependencies: Docker.
#
validate:  # Validate Kometa YAML without connecting to Plex or external APIs.
	@scripts/validate-kometa.sh

#
# check-generated: Reject PATTRMM-owned generated YAML from Git history.
#
# Dependencies: Git.
#
check-generated:  # Confirm generated runtime inputs remain untracked.
	@scripts/check-generated-files.sh

#
# lint: Run all pre-commit hooks against the complete local checkout.
#
# Dependencies: pre-commit.
#
lint:  # Lint formatting, Markdown, YAML, shell, workflows, and secrets.
	@pre-commit run --all-files

#
# lint-ci: Run pre-commit against files present in the sparse CI checkout.
#
# Dependencies: pre-commit.
#
lint-ci:  # Lint the text-only continuous-integration checkout.
	@scripts/run-pre-commit-ci.sh

#
# format: Apply only safe whitespace and final-newline formatting hooks.
#
# Dependencies: pre-commit.
#
format:  # Apply safe repository whitespace fixes.
	@pre-commit run trailing-whitespace --all-files || true
	@pre-commit run end-of-file-fixer --all-files || true
	@pre-commit run mixed-line-ending --all-files || true

#
# test-library: Run the isolated Kometa configuration against Plex test media.
#
# Dependencies: Docker, TEST_ENV, and the two documented Plex test libraries.
#
test-library:  # Render smoke collections and default overlays in test libraries.
	@scripts/run-test-library.sh
