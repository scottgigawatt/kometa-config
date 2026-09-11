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

Never commit real Plex tokens, API keys, OAuth state, webhook URLs, passwords, private environment files, or generated authentication data. Checked-in configuration uses obvious placeholders or Kometa secret substitutions. Private values belong under the ignored `.secrets/` directory or the deployment's private environment.

Do not read, print, diff, or stage `.secrets/` content while performing unrelated work. Always inspect staged files before committing.

## YAML and comments

Use two-space YAML indentation, UTF-8, LF line endings, a final newline, and no trailing whitespace. Keep one logical definition per block and preserve meaningful ordering. Do not run an unconstrained formatter across Kometa YAML; key ordering and nearby comments are part of the maintainability of these files.

Comments use concise plain English and explain intent, ownership, scheduling, external-source choices, or Plex side effects. Do not comment obvious syntax. New project-owned configuration, scripts, and workflow files begin with the established copyright, Apache-2.0, filename, and purpose header.

Use the established framed block style for standalone comments: a `#` line before and after the explanatory text. Put a blank line before a standalone comment that introduces the next logical block. GitHub Actions workflows comment every job and step with its operational purpose or safety constraint. Shell helpers comment setup, validation, state preparation, and consequential commands as logical blocks; keep error messages literal and corrective.

Use lowercase kebab-case for human-authored filenames. Generated PATTRMM names are controlled by the upstream application and are exempt.

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

`make validate` uses the immutable Kometa image configured in `Makefile`, with no secrets or Plex access and a read-only repository mount. Kometa performs its normal upstream version check, but the directory validator does not initialize the configured services. Schema gaps reported by upstream Kometa are warnings; syntax, type, and required-field errors must fail.

For changes affecting collection membership or rendered artwork, use the isolated Plex fixtures documented in `docs/testing.md` before running against production:

```sh
make test-library
```

Never point the test configuration at production library names. Overlay files must be evaluated together; do not use Kometa's `--run-files` option for overlays.

## Production changes

Repository validation does not prove that external lists still exist or that Plex will render the desired result. After a test-library pass, deploy one clean Git commit to Hera, run only the affected library or definition where Kometa supports it, inspect the log and Plex result, and then perform the full scheduled run.

Separate repository-only guardrail changes from Plex-mutating behavior changes. Preserve unrelated worktree edits and do not alter the live checkout while preparing a pull request unless the user explicitly requests deployment work.

## Documentation

Document only the current supported arrangement. Do not preserve historical migration instructions, superseded paths, or compatibility notes for configurations that no longer exist. Keep commands literal and copyable.
