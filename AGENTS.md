<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  AGENTS.md: Contributor and AI-agent instructions for the configuration repository.
-->

# AGENTS.md

## Project purpose

This repository is the source-controlled Kometa configuration for a private Plex deployment. It owns declarative collection, overlay, playlist, asset, editor, validation, and documentation files. It does not own Plex application data, Kometa logs and caches, credentials, or helper-generated runtime files.

## Repository layout

- `config.yml`: Main Kometa configuration and library wiring.
- `movies/`, `shows/`, and `scheduled/`: Collection files.
- `overlays/`: Custom overlay definitions and artwork.
- `playlists/`: Playlist definitions.
- `assets/`: Collection, playlist, and media artwork.
- `tests/kometa/`: Isolated configuration for the two upstream Plex fixture libraries.
- `pattrmm/settings.yml`: Authored PATTRMM Neo cores and collection presentation.
- `scripts/`: Repository validation and test-library helpers.
- `docs/`: Current operating documentation.
- `.github/`: Workflows, ownership, and issue/PR templates.

## Source and runtime ownership

Treat the Git checkout as the source of truth for human-authored configuration. The Hera deployment mounts this checkout at Kometa's `/config` path.

PATTRMM Neo mounts that path read-write and reads `pattrmm/settings.yml` through its read-only `/settings` mount. Its collections and paired Plex-GUID text lists belong under `generated/pattrmm/`, remain ignored, and must not be committed. Update the authored Neo settings when their contents need to change. The enabled status core generates collections only; preserve the independently maintained custom overlays. Generated collection definitions must use builders supported by the pinned Kometa runtime.

Logs, caches, missing-item reports, `.kometa-test/`, and `.secrets/` are private runtime state. Never treat them as repository source.

## Secrets

Never commit real Plex tokens, API keys, OAuth state, webhook URLs, passwords, private server URLs or hostnames, private environment files, or generated authentication data. Checked-in configuration uses obvious placeholders or Kometa secret substitutions. Private values belong under the ignored `.secrets/` directory or the deployment's private environment.

Treat Plex server addresses as confidential even when publicly reachable. Never reproduce them in source, documentation, commit messages, pull requests, issues, or shared tool output. Runtime logs can contain connection details; keep them private and report only reviewed, sanitized results.

Do not read, print, diff, or stage `.secrets/` content while performing unrelated work. Always inspect staged files before committing.

## YAML and comments

Use two-space YAML indentation, UTF-8, LF line endings, a final newline, and no trailing whitespace. Keep one logical definition per block and preserve meaningful ordering. Do not run an unconstrained formatter across Kometa YAML; key ordering and nearby comments are part of the maintainability of these files.

Comments use concise plain English and explain intent, ownership, scheduling, external-source choices, or Plex side effects. Do not comment obvious syntax. New project-owned configuration, scripts, and workflow files begin with the established copyright, Apache-2.0, filename, and purpose header.

Write explicit TMDb IDs one per YAML list line with a descriptive inline comment. Align adjacent end-of-line comments within logical groups at the same indentation, placing two spaces after the longest code entry. Shorter entries receive padding to that same comment column; standalone entries use two spaces. Apply this rule to all authored YAML, including `movies/top-rated-subgenres.yml`. Movie and show IDs identify the title and premiere year; collection IDs identify the TMDb collection name, not an individual movie. Follow native TMDb collection membership without adding standalone films to recreate a broader franchise.

Collection summaries describe the characters, stories, moods, and themes for viewers. Use concise original prose, with wit and occasional emoji where appropriate; keep serious subjects respectful. Avoid references to the library, metadata providers, keyword matching, vote thresholds, sorting, or how the collection is assembled. Do not introduce summaries with generic invitations such as 'this collection' or 'dive into'. Keep operational details in source comments and documentation.

Use the established framed block style for standalone comments: a `#` line before and after the explanatory text. Put a blank line before a standalone comment that introduces the next logical block. GitHub Actions workflows comment every job and step with its operational purpose or safety constraint. Shell helpers comment setup, validation, state preparation, and consequential commands as logical blocks; keep error messages literal and corrective.

Use descriptive lowercase kebab-case for human-authored filenames. Name collection files for the collections they contain, such as `critics-choice.yml`, `weekly-shuffle.yml`, and `holiday-episodes.yml`. Preserve tool-required configuration filenames. Generated PATTRMM names are controlled by the upstream application and are exempt.

## Python helpers and tests

Use four-space indentation, module and callable docstrings, and explicit return annotations. Document nontrivial helpers with `Args`, `Returns`, and `Raises` sections where applicable. Give every test a short behavioral docstring; use framed comments to explain test groups, setup boundaries, and non-obvious safety checks without narrating each assertion.

Keep local editor dependencies in `requirements-dev.txt`, with `ruamel.yaml` matching the pinned Kometa runtime. Use the ignored `.venv` for editor imports and local lint tools. Regression tests run inside Kometa through `make validate`; do not suppress missing-import diagnostics to hide an unconfigured interpreter.

## External lists and assets

Prefer native Kometa, Plex, TMDb, or IMDb builders over third-party lists when the membership can be expressed as a rule. Prefer repository-owned text lists or owner-controlled services for static curated membership. Third-party sources need a clear reason and must be verified before merge.

Do not add artwork without checking its source, license, intended mapping, and whether Kometa Defaults already maintain the same dynamic category. Keep filenames case-correct for Linux and Synology. Do not introduce Git LFS or rewrite asset history without explicit approval.

## Validation

Run the smallest relevant checks, then the complete repository gate before handoff:

```sh
make validate
make validate-editor
make check-generated
make test-make-helpers
make lint
```

`make validate` uses the immutable Kometa image configured in `Makefile`, with no secrets or Plex access and a read-only snapshot of Git-tracked YAML from the working tree. Stage new YAML files before validation; ignored credentials and runtime output are not mounted. Kometa performs its normal upstream version check, but the directory validator does not initialize the configured services. Schema gaps reported by upstream Kometa are warnings; syntax, type, and required-field errors must fail.

`make validate-editor` generates the ignored `.vscode/.schemas/config-schema.json` from the same runtime version and validates all public base configs. Keep compatibility fixes narrow and runtime-verified; never disable validation or permit arbitrary unknown properties. Add negative tests under `tests/editor/` when extending the schema adapter. CI runs this target through Make.

For collection membership or artwork changes, use the [isolated preview workflow](docs/testing.md) before running against production. Choose the smallest supported preview that covers the change. Never point test configuration at production library names. Overlay files must be evaluated together; do not use Kometa's `--run-files` option for overlays.

Keep collection previews guarded: validate production source before creating private runtime copies, disable scheduled deletion, and omit only explicitly approved download attributes. Reject unexpected writer attributes, download-client connections, and external list writers. Keep production favorites, charts, playlists, and PATTRMM output outside fixture runs. Midnight Cinema's preview must also exclude the series-request helper and hide collections from home and shared screens.

Use the native builders and thresholds defined in source. Subgenres prohibit personal-list builders and external templates. Seasonal movies explicitly disable Radarr additions, searches, upgrades, and monitoring changes. TV holiday collections match episode titles or summaries, never parent-show metadata, and contain no Sonarr attributes. Preserve positive, negative, metadata-boundary, and CLI-isolation regression coverage when changing these rules. See [collection behavior](docs/collections.md) for membership and download settings.

CodeQL uses the checked-in `.github/workflows/codeql-actions.yml` with independent Python and GitHub Actions analyses. Preserve its digest pins, minimal permissions, separate language categories, and framed job/step comments. Keep GitHub Default setup disabled; do not introduce a competing CodeQL workflow or enable separate billable analysis features as part of routine maintenance.

## Production changes

Repository validation does not prove that external lists still exist or that Plex will render the desired result. After a test-library pass, deploy one clean Git commit to Hera, run only the affected library or definition where Kometa supports it, inspect the log and Plex result, and then perform the full scheduled run.

Separate repository-only guardrail changes from Plex-mutating behavior changes. Preserve unrelated worktree edits and do not alter the live checkout while preparing a pull request unless the user explicitly requests deployment work.

## Documentation

Follow [the documentation style guide](docs/documentation-style.md). Keep the README concise, operating guides and recognized community policies under `docs/`, and issue/PR templates under `.github/`. Keep this file at the repository root for discovery. Update the documentation index and inbound links when moving pages.

Document only the current supported arrangement. Do not preserve historical migration instructions, superseded paths, or compatibility notes for configurations that no longer exist. Use sentence-case headings, descriptive links, native GitHub alerts only for important information, and copyable `sh` command fences. Keep ordinary prose paragraphs on one physical line and enable visual word wrapping in the editor. Public prose may use light cinema humor; technical comments and security guidance remain literal.

## Makefile conventions

Follow Plundarr and Privateerr's structure: centralized target names, common/project/internal target groups, helper command variables, framed target comments, dependency notes, and reusable terminal output helpers. Keep Kometa's own supported target inventory; do not import unrelated Docker lifecycle or destructive cleanup commands.

Plain `make` must remain help-only, with no Docker or secret prerequisites. Preserve the pinned runtime, private environment exports, preview flags, and guarded helper boundaries. Honor `NO_COLOR` and keep captured output plain. Do not hide hook failures. Run `make test-make-helpers` after Make or documentation changes and the complete `make check` before handoff.
