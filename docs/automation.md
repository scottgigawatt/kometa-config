# Repository automation ⚙️

Run Make from the repository root with the [contributor environment](CONTRIBUTING.md#prepare-the-checkout) active. Plain `make` and `make help` print usage without Docker or secrets.

## Local commands

| Command | Purpose | Requirements |
| --- | --- | --- |
| `make check` | Complete repository gate | Docker and development tools; no Plex access |
| `make validate` | Kometa validation, artwork checks, and container regression tests | Pinned Docker image; upstream version check may use the network |
| `make validate-editor` | Refresh editor schemas and test configuration validation | Python and pinned public schemas |
| `make check-generated` | Reject tracked PATTRMM runtime files | Git |
| `make test-make-helpers` | Test Make behavior, documentation links, and community-file placement | Python and Make |
| `make lint` | Run all pre-commit hooks | Development tools; first use may download hook environments |
| `make format` | Fix whitespace and final newlines | Edits source files selected by hooks |
| `make lint-ci` | Run hooks for files present in sparse CI | CI checkout |

`make format` returns nonzero when a hook changes files or fails. Review the edits and rerun `make check`. For commands that modify Plex fixtures, use the [preview guide](testing.md#choose-a-preview).

## Settings and overrides

The [Makefile](../Makefile) defines the supported commands and defaults.

- `KOMETA_IMAGE`: Exact runtime tag and digest for validation and previews. Use the checked-in pin for supported validation.
- `TEST_ENV`: Private preview environment; defaults to `.secrets/test.env`. Relative paths resolve from the repository root.
- `PYTHON_BIN`: Python for editor-schema checks and local helper tests. Kometa regression tests use the container's Python.
- `NO_COLOR=1`: Disable terminal colors. Captured output is always plain text.

## Pull-request checks

[Validation CI](../.github/workflows/validate-pr.yml) runs the configuration, editor, generated-file, helper, lint, and secret checks. Its sparse checkout omits artwork binaries; artwork checks use Git's file inventory.

[CodeQL](../.github/workflows/codeql-actions.yml) analyzes Python and GitHub Actions separately on pull requests, pushes to `main`, and manual runs. Check both analyses and `Validate the Configuration Reels 🎞️` for the current commit before merging. CodeQL complements configuration validation and secret scanning.

## Dependency updates

[Renovate](../.github/renovate.json5) manages the Kometa image, editor-schema URLs, GitHub Actions, CI Python, development requirements, and pre-commit hooks. Runtime and schema updates share a PR; validation checks matching releases. Keep `ruamel.yaml` aligned with the pinned image. VS Code manages extension updates.

## Editor schemas

Run `make validate-editor` after cloning or updating Kometa; `make check` includes it. Generated schemas are cached under the ignored `.vscode/.schemas/` directory. Reload VS Code if diagnostics do not refresh.

The [schema adapter](../scripts/editor-schema.py) accepts runtime-supported fields missing from upstream while preserving checks for unknown properties and incorrect types. Regression tests verify accepted fields and rejected mistakes. Optional rating-overlay files are checked against the upstream overlay schema and remain outside the active overlay set.
