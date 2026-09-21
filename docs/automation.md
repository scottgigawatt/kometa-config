# Repository automation

Run Make from the repository root with the contributor environment active. Plain `make` and `make help` only print usage; they require neither Docker nor secrets.

## Local commands

| Command | Purpose | Runtime access |
| --- | --- | --- |
| `make check` | Complete local gate | No Plex access |
| `make validate` | Pinned Kometa validation, artwork checks, and container regression tests | Docker; upstream version check may use the network |
| `make validate-editor` | Refresh the editor config schema and check valid fields, typos, and wrong types | Python; downloads the pinned public schema; no Plex access |
| `make check-generated` | Reject tracked PATTRMM runtime files | Git only |
| `make test-make-helpers` | Test Make behavior, documentation links, and community-file placement | Local Python and Make only |
| `make lint` | All pre-commit hooks | Local files; first use may download tools |
| `make format` | Safe whitespace and final-newline fixes | Edits tracked source files selected by hooks |
| `make lint-ci` | Hooks for files present in sparse CI | CI checkout |

`make format` runs all three whitespace hooks and returns nonzero if any hook reports changes or errors. Review the edits and run `make check`; failures are not silently ignored.

See [testing](testing.md#choose-a-preview) for the five Plex-mutating preview targets. There are no Make targets to deploy production, print private environment values, remove media, or delete runtime state.

## Settings and overrides

The [Makefile](../Makefile) centralizes target names, target groups, helper commands, terminal output, and settings. It follows the same structure as Plundarr and Privateerr without importing their service lifecycle commands.

- `KOMETA_IMAGE` selects the exact tag and digest used by validation and previews. Keep the checked-in pin; arbitrary overrides are not the supported validation baseline.
- `TEST_ENV` selects the private preview environment, defaulting to `.secrets/test.env`. Relative paths resolve from the repository root.
- `PYTHON_BIN` selects Python for the editor-schema checks and local helper tests. Kometa regression tests still use the pinned container's Python.
- `NO_COLOR=1` disables terminal colors. Captured output is always plain text.

Helper command variables support isolated tests. Normal operation uses their checked-in defaults; do not replace guarded preview commands with unrestricted production runs.

## Pull-request checks

[Validation CI](../.github/workflows/validate-pr.yml) uses a sparse text checkout to avoid downloading the artwork library. It runs the same validation, generated-file, and helper gates as `make check`, with `lint-ci` selecting only files present in that checkout.

[CodeQL](../.github/workflows/codeql-actions.yml) uses checked-in Advanced setup with independent Python and GitHub Actions analyses on pull requests, pushes to `main`, and manual dispatch. Keep GitHub Default setup disabled so it does not compete with this workflow. Standard queries need no additional CodeQL configuration file.

The repository ruleset requires the `Validate the Configuration Reels 🎞️` check and CodeQL results. Verify both language analyses for the current commit; passing lint alone is not CodeQL coverage. GitHub Code Quality is a separate product and should not be required unless deliberately enabled.

CodeQL does not connect to Plex or replace configuration validation and secret scanning. Action permissions are limited, checkout credentials are not retained, and action revisions are pinned.

## Dependency updates

[Renovate](../.github/renovate.json5) tracks the Kometa image, three direct editor-schema URLs, GitHub Actions, CI Python, development requirements, and pre-commit hooks. The generated config schema derives its version from the image pin; it has no independent version to update. Runtime and schema updates share a PR; validation checks matching releases. Keep `ruamel.yaml` aligned with the pinned image. VS Code updates extensions separately.

Review dependency PRs and their exact-head checks before merging. Do not add a competing Dependabot setup for the same dependencies.

## Editor configuration schema

`make validate-editor` generates the ignored `.vscode/.schemas/config-schema.json` from the pinned upstream release. Run it after cloning or updating Kometa; `make check` also runs it. Reload VS Code's window if it retains old diagnostics.

The [schema adapter](../scripts/editor-schema.py) adds only runtime-supported seasonal, universe, and final-overlay-offset fields missing from upstream, plus complete Plex URL secret placeholders. It preserves unknown-property and type checks; regression tests deliberately introduce misspellings and invalid values. The generated file is not deployed or committed. Refreshing it downloads only public schema data and never reads `.secrets/`.
