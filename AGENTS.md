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
- `scripts/`: Repository validation and test-library helpers.
- `docs/`: Current operating documentation.

## Source and runtime ownership

Treat the Git checkout as the source of truth for human-authored configuration. The Hera deployment mounts this checkout at Kometa's `/config` path.

PATTRMM also mounts that path read-write and generates files such as `*-in-history.yml`, `*-by-size.yml`, `*-returning-soon-metadata.yml`, and `*-returning-soon-overlay.yml`. Those files are expected runtime inputs, remain ignored, and must not be committed. Update PATTRMM preferences when their contents need to change.

Logs, caches, missing-item reports, `.kometa-test/`, and `.secrets/` are private runtime state. Never treat them as repository source.

## Secrets

Never commit real Plex tokens, API keys, OAuth state, webhook URLs, passwords, private server URLs or hostnames, private environment files, or generated authentication data. Checked-in configuration uses obvious placeholders or Kometa secret substitutions. Private values belong under the ignored `.secrets/` directory or the deployment's private environment.

Treat Plex server addresses as confidential even when publicly reachable. Never reproduce them in source, documentation, commit messages, pull requests, issues, or shared tool output. Runtime logs can contain connection details; keep them private and report only reviewed, sanitized results.

Do not read, print, diff, or stage `.secrets/` content while performing unrelated work. Always inspect staged files before committing.

## YAML and comments

Use two-space YAML indentation, UTF-8, LF line endings, a final newline, and no trailing whitespace. Keep one logical definition per block and preserve meaningful ordering. Do not run an unconstrained formatter across Kometa YAML; key ordering and nearby comments are part of the maintainability of these files.

Comments use concise plain English and explain intent, ownership, scheduling, external-source choices, or Plex side effects. Do not comment obvious syntax. New project-owned configuration, scripts, and workflow files begin with the established copyright, Apache-2.0, filename, and purpose header.

Write explicit TMDb IDs one per YAML list line with at least two spaces before a descriptive inline comment. In `movies/subgenre-top.yml`, use exactly two spaces before inline comments instead of column alignment. Other files may align end-of-line comments within logical groups where practical. Movie and show IDs identify the title and premiere year; collection IDs identify the TMDb collection name, not an individual movie. Follow native TMDb collection membership without adding standalone films to recreate a broader franchise.

Collection summaries describe the films and their themes for viewers. Avoid references to the library, metadata providers, keyword matching, vote thresholds, or how the collection is assembled. Keep those operational details in source comments and documentation.

Use the established framed block style for standalone comments: a `#` line before and after the explanatory text. Put a blank line before a standalone comment that introduces the next logical block. GitHub Actions workflows comment every job and step with its operational purpose or safety constraint. Shell helpers comment setup, validation, state preparation, and consequential commands as logical blocks; keep error messages literal and corrective.

Use lowercase kebab-case for human-authored filenames. Generated PATTRMM names are controlled by the upstream application and are exempt.

## Python helpers and tests

Use four-space indentation, module and callable docstrings, and explicit return annotations. Document nontrivial helpers with `Args`, `Returns`, and `Raises` sections where applicable. Give every test a short behavioral docstring; use framed comments to explain test groups, setup boundaries, and non-obvious safety checks without narrating each assertion.

Keep local editor dependencies in `requirements-dev.txt`, with `ruamel.yaml` matching the pinned Kometa runtime. Use the ignored `.venv` for editor imports and local lint tools. Regression tests still run inside Kometa through `make validate`; do not suppress missing-import diagnostics to hide an unconfigured interpreter.

## External lists and assets

Prefer native Kometa, Plex, TMDb, or IMDb builders over third-party lists when the membership can be expressed as a rule. Prefer repository-owned text lists or owner-controlled services for static curated membership. Third-party sources need a clear reason and must be verified before merge.

Do not add artwork without checking its source, license, intended mapping, and whether Kometa Defaults already maintain the same dynamic category. Keep filenames case-correct for Linux and Synology. Do not introduce Git LFS or rewrite asset history without explicit approval.

## Validation

Run the smallest relevant checks, then the complete repository gate before handoff:

```sh
make validate
make check-generated
make lint
```

`make validate` uses the immutable Kometa image configured in `Makefile`, with no secrets or Plex access and a read-only snapshot of Git-tracked YAML from the working tree. Stage new YAML files before validation; ignored credentials and runtime output are not mounted. Kometa performs its normal upstream version check, but the directory validator does not initialize the configured services. Schema gaps reported by upstream Kometa are warnings; syntax, type, and required-field errors must fail.

For changes affecting collection membership or rendered artwork, use the isolated Plex fixtures documented in `docs/testing.md` before running against production:

```sh
make test-library
```

Use `make test-collections` for collection previews without rerunning overlays. It reuses the TMDb builders from `movies/franchise.yml`, the genre rules from `movies/genre.yml`, all 101 searches in `movies/subgenre-top.yml`, the city keywords from `movies/cities.yml`, the five native sources from `movies/universes.yml`, the show-only collections from `shows/shuffle.yml`, and smoke collections in both fixtures. Use `make test-subgenres` to run only all 101 ranked themes in `test_movie_lib`. Ninety themes use TMDb Discover; eleven use native IMDb keyword searches. No personal-list builders or external templates are permitted anywhere in the subgenre file. Themes use a rating floor of 5 and 1,000 votes by default, with explicit per-theme overrides protected by regression tests. Keep every keyword and genre ID query documented with an inline comment separated by exactly two spaces. TV membership is maintained as named TMDb show IDs in source, with no external curated-list dependency. The runtime remains isolated under `.kometa-test/collections/`; production favorites, charts, download clients, and external list writers are not loaded.

The collection preview also loads the thirteen holiday movie collections from `scheduled/seasonal.yml`. Use `make test-seasonal` to run only those collections in `test_movie_lib`. The runner validates production source before rendering a private runtime copy with scheduled deletion disabled and the five already-false Radarr attributes omitted; Kometa requires a Radarr connection even for false attributes. Do not remove enabled writer attributes to bypass validation. Keep all seasonal Radarr add, search, upgrade, and monitoring flags explicitly false in production source. Vintage Christmas includes first releases through 1979; St. Patrick's Day includes Irish-themed films and the holiday itself.

Never point the test configuration at production library names. Overlay files must be evaluated together; do not use Kometa's `--run-files` option for overlays.

TV holiday collections in `shows/seasonal.yml` use `builder_level: episode`, `plex_all`, and separate title/summary regex filter sets. Match episode metadata, never parent-show metadata. Avoid generic seasonal words and air-date restrictions. Episode collections do not support Sonarr attributes, including false ones; the preview guard rejects all download-client attributes and external builders. Use `make test-tv-seasonal` for the three holidays in `test_tv_lib`. The private runtime copy changes only scheduled deletion, preserving the production rules and artwork. Keep positive, negative, summary-only, and CLI-isolation regression coverage when changing these rules.

CodeQL uses the checked-in `.github/workflows/codeql-actions.yml` with independent Python and GitHub Actions analyses. Preserve its digest pins, minimal permissions, separate language categories, and framed job/step comments. Keep GitHub Default setup disabled; do not introduce a competing CodeQL workflow or enable separate billable analysis features as part of routine maintenance.

## Production changes

Repository validation does not prove that external lists still exist or that Plex will render the desired result. After a test-library pass, deploy one clean Git commit to Hera, run only the affected library or definition where Kometa supports it, inspect the log and Plex result, and then perform the full scheduled run.

Separate repository-only guardrail changes from Plex-mutating behavior changes. Preserve unrelated worktree edits and do not alter the live checkout while preparing a pull request unless the user explicitly requests deployment work.

## Documentation

Document only the current supported arrangement. Do not preserve historical migration instructions, superseded paths, or compatibility notes for configurations that no longer exist. Keep commands literal and copyable.
