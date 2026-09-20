#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# Makefile: Validate repository source and preview isolated Plex test libraries.
#

#
# Common target names.
#
CHECK=check
LINT=lint
FORMAT=format
TEST_MAKE_HELPERS=test-make-helpers
HELP=help

#
# Project target names.
#
VALIDATE=validate
CHECK_GENERATED=check-generated
TEST_LIBRARY=test-library
TEST_COLLECTIONS=test-collections
TEST_SUBGENRES=test-subgenres
TEST_SEASONAL=test-seasonal
TEST_TV_SEASONAL=test-tv-seasonal

#
# Internal target names.
#
LINT_CI=lint-ci

#
# Common targets.
#
COMMON_TARGETS= \
	$(CHECK) \
	$(LINT) \
	$(FORMAT) \
	$(TEST_MAKE_HELPERS) \
	$(HELP)

#
# Project targets.
#
PROJECT_TARGETS= \
	$(VALIDATE) \
	$(CHECK_GENERATED) \
	$(TEST_LIBRARY) \
	$(TEST_COLLECTIONS) \
	$(TEST_SUBGENRES) \
	$(TEST_SEASONAL) \
	$(TEST_TV_SEASONAL)

#
# Internal targets.
#
INTERNAL_TARGETS=$(LINT_CI)

#
# Complete target inventory.
#
TARGETS= \
	$(COMMON_TARGETS) \
	$(PROJECT_TARGETS) \
	$(INTERNAL_TARGETS)

#
# Pinned Kometa runtime and private test-library environment settings.
# Keep the image assignment compatible with Renovate's custom manager.
#
KOMETA_IMAGE ?= kometateam/kometa:v2.4.8@sha256:c58f6d4af511613f218b6dafbfc84078af4e5a6089790c1fdba58fd7c5dad70a
TEST_ENV ?= .secrets/test.env

#
# Local tools and project-owned helpers.
#
PYTHON_BIN                ?= python3
PRE_COMMIT                ?= pre-commit
VALIDATE_CMD              ?= scripts/validate-kometa.sh
CHECK_GENERATED_CMD       ?= scripts/check-generated-files.sh
LINT_CI_CMD               ?= scripts/run-pre-commit-ci.sh
TEST_LIBRARY_CMD          ?= scripts/run-test-library.sh
TEST_COLLECTIONS_CMD      ?= scripts/run-collection-tests.sh
MAKE_HELPERS_TEST_CMD     ?= $(PYTHON_BIN) -m unittest discover -s tests/helpers -v
FORMAT_HOOKS              := trailing-whitespace end-of-file-fixer mixed-line-ending

#
# Export only the settings consumed by the preview and validation helpers.
#
export KOMETA_IMAGE
export TEST_ENV

#
# Terminal presentation settings. Enable color only for an interactive terminal
# and honor NO_COLOR; captured output remains plain text.
#
COLOR_RESET   := \033[0m
COLOR_TITLE   := \033[1;36m
COLOR_COMMAND := \033[1;33m
COLOR_INFO    := \033[0;36m

#
# User-facing Make output helpers. Check the terminal at recipe execution time.
#
define print_line_inline
if [ -t 1 ] && [ -z "$$NO_COLOR" ]; then \
	printf '\n%b%s%b\n' "$(1)" "$(2)" "$(COLOR_RESET)"; \
else \
	printf '\n%s\n' "$(2)"; \
fi
endef

define announce
	@$(call print_line_inline,$(COLOR_INFO),$(1))
endef

define help_heading
	@$(call print_line_inline,$(COLOR_TITLE),$(1))
endef

define help_line
	@if [ -t 1 ] && [ -z "$$NO_COLOR" ]; then \
		printf '  %b%-24s%b %s\n' "$(COLOR_COMMAND)" "$(1)" "$(COLOR_RESET)" "$(2)"; \
	else \
		printf '  %-24s %s\n' "$(1)" "$(2)"; \
	fi
endef

#
# Default to help without checking Docker or reading private configuration.
#
.DEFAULT_GOAL := $(HELP)
.PHONY: $(TARGETS)

#
# $(CHECK): Run every local gate required before pull-request review.
#
# Dependencies:
#   $(VALIDATE) - Check pinned Kometa behavior and YAML without Plex access.
#   $(CHECK_GENERATED) - Reject helper-generated YAML from source control.
#   $(TEST_MAKE_HELPERS) - Check Make behavior and repository documentation.
#   $(LINT) - Run formatting, syntax, and secret checks.
#
$(CHECK): $(VALIDATE) $(CHECK_GENERATED) $(TEST_MAKE_HELPERS) $(LINT)

#
# $(LINT): Run all pre-commit hooks against the complete local checkout.
#
# Dependencies: pre-commit from the pinned development requirements.
#
$(LINT):
	$(call announce,🔎 Checking the source credits...)
	@$(PRE_COMMIT) run --all-files

#
# $(FORMAT): Apply safe whitespace fixes and report any hook failure.
#
# Dependencies: pre-commit from the pinned development requirements.
#
$(FORMAT):
	$(call announce,🧹 Tidying whitespace without rewriting YAML structure...)
	@status=0; \
	for hook in $(FORMAT_HOOKS); do \
		$(PRE_COMMIT) run "$$hook" --all-files || status=$$?; \
	done; \
	exit "$$status"

#
# $(TEST_MAKE_HELPERS): Test command routing, failure handling, and local doc links.
#
# Dependencies: Python 3 and GNU Make; no Docker, secrets, or Plex access.
#
$(TEST_MAKE_HELPERS):
	@$(MAKE_HELPERS_TEST_CMD)

#
# $(HELP): List validation commands separately from Plex-mutating previews.
#
# Dependencies: None.
#
$(HELP):
	$(call help_heading,🎬 Kometa command guide)
	@printf 'Usage: make <target> [TEST_ENV=<private-file>]\n'
	$(call help_heading,Local checks — no Plex access)
	$(call help_line,$(CHECK),Run all repository checks.)
	$(call help_line,$(VALIDATE),Run pinned Kometa validation and regression tests.)
	$(call help_line,$(CHECK_GENERATED),Reject tracked generated runtime files.)
	$(call help_line,$(LINT),Run every pre-commit hook.)
	$(call help_line,$(FORMAT),Apply safe whitespace fixes; rerun checks afterward.)
	$(call help_line,$(TEST_MAKE_HELPERS),Test Make behavior and documentation links.)
	$(call help_heading,Plex previews — test libraries only)
	$(call help_line,$(TEST_LIBRARY),Render smoke collections and complete custom overlays.)
	$(call help_line,$(TEST_COLLECTIONS),Preview the guarded movie and TV collection sources.)
	$(call help_line,$(TEST_SUBGENRES),Preview all ranked movie themes.)
	$(call help_line,$(TEST_SEASONAL),Preview seasonal movie collections.)
	$(call help_line,$(TEST_TV_SEASONAL),Preview TV holiday episodes.)
	$(call help_heading,CI and help)
	$(call help_line,$(LINT_CI),Run hooks against files present in a sparse CI checkout.)
	$(call help_line,$(HELP),Show this guide without starting services.)
	@printf '\nRun from the repository root. See docs/testing.md for setup and preview scope.\n'

#
# $(VALIDATE): Validate tracked YAML and behavior with the pinned Kometa image.
#
# Dependencies: Docker with a running engine and Git; no live service credentials.
#
$(VALIDATE):
	@$(VALIDATE_CMD)

#
# $(CHECK_GENERATED): Reject PATTRMM-owned generated YAML from tracked source.
#
# Dependencies: Git.
#
$(CHECK_GENERATED):
	@$(CHECK_GENERATED_CMD)

#
# $(TEST_LIBRARY): Render smoke collections and complete custom overlay sets.
#
# Dependencies: Docker, TEST_ENV, and both configured Plex test libraries.
#
$(TEST_LIBRARY):
	$(call announce,🎞️ Rendering overlays in the test libraries only...)
	@$(TEST_LIBRARY_CMD)

#
# $(TEST_COLLECTIONS): Preview the guarded movie and TV collection sources.
#
# Dependencies: Docker, TEST_ENV, and both configured Plex test libraries.
#
$(TEST_COLLECTIONS):
	@$(TEST_COLLECTIONS_CMD)

#
# $(TEST_SUBGENRES): Preview ranked movie themes without overlays or downloads.
#
# Dependencies: Docker, TEST_ENV, and the movie test library.
#
$(TEST_SUBGENRES):
	@$(TEST_COLLECTIONS_CMD) --subgenres-only

#
# $(TEST_SEASONAL): Preview holiday movies without downloads or scheduled deletion.
#
# Dependencies: Docker, TEST_ENV, and the movie test library.
#
$(TEST_SEASONAL):
	@$(TEST_COLLECTIONS_CMD) --seasonal-only

#
# $(TEST_TV_SEASONAL): Preview TV holiday episodes without scheduled deletion.
#
# Dependencies: Docker, TEST_ENV, and the TV test library.
#
$(TEST_TV_SEASONAL):
	@$(TEST_COLLECTIONS_CMD) --tv-seasonal-only

#
# $(LINT_CI): Run pre-commit against files present in a sparse CI checkout.
#
# Dependencies: Git and pre-commit.
#
$(LINT_CI):
	@$(LINT_CI_CMD)
