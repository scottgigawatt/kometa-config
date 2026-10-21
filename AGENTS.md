<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  AGENTS.md: Contributor and AI-agent instructions for the configuration repository.
-->

# AGENTS.md

## Project purpose

This repository is the source-controlled Kometa configuration for a private Plex deployment. It owns declarative collection, overlay, playlist, asset, editor, validation, and documentation files. It does not own Plex application data, Kometa logs and caches, credentials, or helper-generated runtime files.

## Repository map and nested guidance

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

This root file applies throughout the checkout. Read any applicable nested `AGENTS.md` and task-relevant `.agents/skills/` guidance before editing their scope; narrower instructions refine these rules. No nested guidance or `.agents/skills/` directory is currently tracked. Keep essential safety and validation rules here so this file remains self-sufficient. If linked local guidance contradicts these rules or the requested scope, report the conflict instead of silently changing other files.

## Scope and working tree

Inspect the branch, status, diff, and relevant source before editing. Keep changes focused on the requested outcome, preserve unrelated staged and unstaged work, and use an isolated checkout when needed. Do not reset, clean, overwrite, reformat, or stage unrelated files. Keep behavior changes separate from incidental cleanup; inspect the complete diff and staged paths before committing. Preserve project and upstream license attribution.

## Source and runtime ownership

Treat the Git checkout as the source of truth for human-authored configuration. The private deployment mounts this checkout at Kometa's `/config` path.

PATTRMM Neo mounts that path read-write and reads `pattrmm/settings.yml` through its read-only `/settings` mount. Its collections and paired Plex-GUID text lists belong under `generated/pattrmm/`, remain ignored, and must not be committed. Update the authored Neo settings when their contents need to change. The enabled status core generates collections only; preserve the independently maintained custom overlays. Generated collection definitions must use builders supported by the pinned Kometa runtime.

Logs, caches, missing-item reports, `.kometa-test/`, and `.secrets/` are private runtime state. Never treat them as repository source.

## Secrets and confidentiality

Never commit real Plex tokens, API keys, OAuth state, webhook URLs, passwords, private server URLs or hostnames, private environment files, or generated authentication data. Checked-in configuration uses obvious placeholders or Kometa secret substitutions. Private values belong under the ignored `.secrets/` directory or the deployment's private environment.

Treat Plex server addresses as confidential even when publicly reachable. Never reproduce them in source, documentation, commit messages, pull requests, issues, or shared tool output. Runtime logs can contain connection details; keep them private and report only reviewed, sanitized results.

Do not read, print, diff, or stage `.secrets/` content while performing unrelated work. Always inspect staged files before committing.

## Formatting, YAML, and comments

Follow `.editorconfig` and checked-in linter configurations: UTF-8, LF line endings, a final newline, two-space YAML and Markdown indentation, four-space Python and shell indentation, and literal tabs in Make recipes. Avoid trailing whitespace except intentional Markdown hard breaks. Keep one logical definition per block and preserve meaningful ordering. Do not run an unconstrained formatter across Kometa YAML; key ordering and nearby comments are part of the maintainability of these files.

Comments use concise plain English and explain intent, ownership, scheduling, external-source choices, or Plex side effects. Do not comment obvious syntax. New project-owned configuration, scripts, and workflow files begin with the established copyright, Apache-2.0, filename, and purpose header.

Write explicit TMDb IDs one per YAML list line with a descriptive inline comment. Align adjacent end-of-line comments within logical groups at the same indentation, placing two spaces after the longest code entry. Shorter entries receive padding to that same comment column; standalone entries use two spaces. Apply this rule to all authored YAML, including `movies/top-rated-subgenres.yml`. Movie and show IDs identify the title and premiere year; collection IDs identify the TMDb collection name, not an individual movie. Follow native TMDb collection membership without adding standalone films to recreate a broader franchise.

Collection summaries describe the characters, stories, moods, and themes for viewers. Use concise original prose, with wit and occasional emoji where appropriate; keep serious subjects respectful. Avoid references to the library, metadata providers, keyword matching, vote thresholds, sorting, or how the collection is assembled. Do not introduce summaries with generic invitations such as 'this collection' or 'dive into'. Keep operational details in source comments and documentation.

Use the established framed block style for standalone comments: a `#` line before and after the explanatory text. Put a blank line before a standalone comment that introduces the next logical block. GitHub Actions workflows comment every job and step with its operational purpose or safety constraint. Shell helpers comment setup, validation, state preparation, and consequential commands as logical blocks; keep error messages literal and corrective.

Use descriptive lowercase kebab-case for human-authored filenames. Name collection files for the collections they contain, such as `critics-choice.yml`, `weekly-shuffle.yml`, and `holiday-episodes.yml`. Preserve tool-required configuration filenames. Generated PATTRMM names are controlled by the upstream application and are exempt.

## Shell and Python quality

Keep shell helpers compatible with their declared interpreter; use `set -eu` where appropriate, quote expansions, preserve argument boundaries and exit statuses, and use temporary directories with cleanup traps. Validate inputs before consequential commands. Do not use `eval`, print private environment values, or bypass fixture and writer guards. Run the repository's ShellCheck hook for shell changes and add focused regression coverage when behavior changes.

Use four-space indentation, module and callable docstrings, and explicit return annotations. Document nontrivial helpers with `Args`, `Returns`, and `Raises` sections where applicable. Give every test a short behavioral docstring; use framed comments to explain test groups, setup boundaries, and non-obvious safety checks without narrating each assertion.

Keep local editor dependencies in `requirements-dev.txt`, with `ruamel.yaml` matching the pinned Kometa runtime. Use the ignored `.venv` for editor imports and local lint tools. Regression tests run inside Kometa through `make validate`; do not suppress missing-import diagnostics to hide an unconfigured interpreter. Keep Ruff correctness, import, docstring, and formatting checks passing; avoid blanket lint, type, schema, or test suppressions. Any narrow exception needs a documented reason tied to the specific limitation.

## External lists and assets

Prefer native Kometa, Plex, TMDb, or IMDb builders over third-party lists when the membership can be expressed as a rule. Prefer repository-owned text lists or owner-controlled services for static curated membership. Third-party sources need a clear reason and must be verified before merge.

Do not add artwork without checking its source, license, intended mapping, and whether Kometa Defaults already maintain the same dynamic category. Keep filenames case-correct for Linux and Synology. Do not introduce Git LFS or rewrite asset history without explicit approval.

## Validation

Run commands from the repository root. Inspect `Makefile`, `requirements-dev.txt`, and the relevant helper before choosing checks. Use the pinned development dependencies in an ignored `.venv`, Git, GNU Make, and Docker with a running engine for the runtime gate. The CI Python version is declared in `.github/workflows/validate-pr.yml`; report discrepancies with contributor setup rather than silently changing either file. Tool installation, image pulls, schema downloads, and hook bootstrapping may require public network access; none of these checks requires VPN, Plex, or private credentials.

Run the smallest relevant checks first, then the complete repository gate before handoff:

```sh
make test-make-helpers
make check-generated
make lint
make check
```

`make check` runs `validate`, `validate-editor`, `check-generated`, `test-make-helpers`, and `lint`. These targets can also run individually. Guidance and documentation changes still require the full gate plus rendered Markdown review; do not claim a check passed if a prerequisite prevented it from running.

`make test-make-helpers` runs local Make-contract, generated-file, and documentation-link tests using Python and Git without Docker or service access. Make-contract tests use stubs; they do not replace real runtime validation. `make check-generated` rejects tracked generated files. `make lint` runs every configured pre-commit hook across tracked files; review any automatic fixes and rerun affected checks. `make lint-ci` is for the sparse CI checkout, not a substitute for local validation.

`make validate` uses the immutable Kometa image configured in `Makefile`, with no secrets or Plex access and a read-only snapshot of Git-tracked YAML from the working tree. Stage only intended new YAML files before validation; ignored credentials and runtime output are not mounted. Overlay-asset checks and behavioral regression tests run offline with `--network none`. The final directory validator performs Kometa's upstream version check over the network but does not initialize configured services. Schema gaps reported by upstream Kometa are warnings; syntax, type, and required-field errors must fail.

`make validate-editor` downloads public schemas for the same pinned runtime version, generates ignored `.vscode/.schemas/` files, validates three public base configs and both rating overlays, and runs editor-schema regressions. Keep compatibility fixes narrow and runtime-verified; never disable validation or permit arbitrary unknown properties. Add negative tests under `tests/editor/` when extending the schema adapter. CI runs this target through Make.

### Fixture previews and collection guards

For collection membership or artwork changes, use the [isolated preview workflow](docs/testing.md) before running against production. Choose the smallest supported preview that covers the change. Never point test configuration at production library names. Overlay files must be evaluated together; do not use Kometa's `--run-files` option for overlays.

Keep collection previews guarded: validate production source before creating private runtime copies, disable scheduled deletion, and omit only explicitly approved download attributes. Reject unexpected writer attributes, download-client connections, and external list writers. Keep production favorites, charts, playlists, and PATTRMM output outside fixture runs. Midnight Cinema's preview must also exclude the series-request helper and hide collections from home and shared screens.

Use the native builders and thresholds defined in source. Subgenres prohibit personal-list builders and external templates. Seasonal movies explicitly disable Radarr additions, searches, upgrades, and monitoring changes. TV holiday collections match episode titles or summaries, never parent-show metadata, and contain no Sonarr attributes. Preserve positive, negative, metadata-boundary, and CLI-isolation regression coverage when changing these rules. See [collection behavior](docs/collections.md) for membership and download settings.

## Dependencies and workflows

Preserve the immutable Kometa image tag and SHA-256 digest, exact development dependency and hook versions, and editor schema/runtime alignment. When dependencies are intentionally updated, verify release provenance and compatibility and run the affected real checks; use immutable commit or digest references where supported for new dependencies, and do not float versions or weaken gates to make validation pass. Pin GitHub Actions to full commit SHAs with readable version comments, keep container references digest-pinned, and grant only the minimum permissions needed at workflow and job scope. Treat existing version-pinned pre-commit hooks as their own mechanism; do not claim every dependency already has an immutable digest.

CodeQL uses the checked-in `.github/workflows/codeql-actions.yml` with independent Python and GitHub Actions analyses. Preserve its commit pins, minimal permissions, separate language categories, and framed job/step comments. Keep GitHub Default setup disabled; do not introduce a competing CodeQL workflow or enable separate billable analysis features as part of routine maintenance. Do not change repository security settings without an explicit request.

## Production changes

Repository edits, validation, and a pull request do not authorize production access or mutations. Only perform deployment work when explicitly requested. After fixture-library validation and visual approval, the authorized operator can deploy one clean Git commit through the normal process, run only the affected library or definition where Kometa supports it, inspect private logs and Plex results, and then allow the full scheduled run.

Keep repository-only guardrail changes separate from Plex-mutating behavior changes. Do not alter the live checkout while preparing a pull request. Validation does not prove external lists still exist or that Plex will render the desired result. Preserve caches and original-poster backups; never delete runtime state as routine cleanup.

## Documentation

Keep the README concise, operating guides and recognized community policies under `docs/`, and issue/PR templates under `.github/`. Keep this file at the repository root for discovery. Use [the documentation style guide](docs/documentation-style.md) for additional local detail; the essential rules are below.

- Use one descriptive H1, sentence-case headings without skipped levels, and blank lines around headings, lists, tables, and fences. Put outcomes first, prerequisites before procedures, and optional details afterward.
- Use numbered lists for procedures, bullets for choices, and readable tables for genuine comparisons. Keep ordinary prose paragraphs on one physical line and use editor word wrapping.
- Use descriptive relative links with valid, case-correct destinations and heading anchors. Update the [documentation index](docs/index.md) and inbound links when moving pages. Check external references when their behavior matters; local-link tests do not verify external availability.
- This repository renders GitHub-flavored Markdown. Use native blockquote alerts such as `[!WARNING]` sparingly for significant risks; do not insert Material `!!!` or `???` syntax. Keep prerequisites and warnings visible, outside collapsed details.
- Label every fenced block with its language. Put copyable commands in `sh` fences without prompt characters or explanatory comments; use `console` for transcripts, `text` for output, and the actual language for configuration. Explain working directory, dependencies, required access, side effects, and destructive-operation warnings before the command.
- Verify commands, paths, defaults, and claims against current source and the pinned stable runtime. Clearly label unreleased behavior rather than presenting it as available. Describe current source/runtime architecture and applicable backup or rollback requirements; never suggest configuration rollback restores mutated Plex state or missing poster backups.
- Document the current supported arrangement without reviving obsolete paths or migration history. If a requested change requires actionable migration or compatibility instructions, identify that need and the conflict with the style guide's omission rule for maintainer resolution before publishing those instructions.
- Keep examples and screenshots free of real credentials, private addresses, and runtime diagnostics. Give images meaningful alt text and verify artwork rights and mappings. Public prose may use light cinema humor; commands, technical comments, security guidance, and troubleshooting remain literal.
- Run `make test-make-helpers` for links and anchors and `make lint` for Markdown and hygiene, then `make check` for the complete gate. Review rendered GitHub Markdown for heading hierarchy, lists, tables, fences, links, images, and alerts. There is no separate documentation-site build target; do not invent one or treat lint as a render check.

## Makefile conventions

Keep local Make rules complete and explicit:

- Centralize target names and maintain the common, project, and internal target groups plus the complete `.PHONY` inventory. Keep `.DEFAULT_GOAL` help-only, with no Docker, credential, network, or service prerequisites.
- Use helper command variables for the existing validation and preview entrypoints. Export only the settings the helpers consume; preserve the pinned `KOMETA_IMAGE`, private `TEST_ENV` handling, preview flags, and guarded helper boundaries.
- Use framed target comments that explain purpose, dependencies, and side effects. List local checks separately from Plex-mutating fixture previews in help. Keep the existing target inventory; do not import Docker lifecycle or destructive cleanup commands.
- Reuse terminal output helpers, honor `NO_COLOR`, and keep captured output plain. Propagate helper and hook failures; whitespace formatting may continue through hooks but must return a failure if any hook fails.
- Treat `make format` as a working-tree mutation limited to its configured whitespace hooks; inspect its diff and rerun checks. Do not imply it rewrites or validates all YAML semantics.
- Run `make test-make-helpers` after Make or documentation changes and `make check` before handoff. Stubbed routing tests complement real validators and never establish that live previews succeeded.

## Handoff and review

Review the complete diff for scope, correctness, license attribution, secrets, generated files, and unrelated changes. Stage explicit paths only. Follow the local signed-commit convention. Report the changed files, behavior and Plex impact, exact validation commands and results, and checks failed or not run with their reasons. Distinguish local/offline checks, network-dependent validation, credentialed fixture previews, and production work; never substitute one for another.

Keep the handoff concise and truthful, with remaining limitations or guidance conflicts, the head SHA, and the PR URL when created. Leave draft PRs for manual review when requested. Do not approve, merge, enable auto-merge, tag, or release on the user's behalf without explicit authorization for that action.
