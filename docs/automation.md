# Repository automation ⚙️

Run Make from the repository root with the [contributor environment](CONTRIBUTING.md#prepare-the-checkout) active. `make help` lists all commands without Docker or secrets. [Testing](testing.md) covers Plex fixture previews.

## Local commands

| Command | Purpose | Requirements |
| --- | --- | --- |
| `make check` | Complete repository gate | Docker and development tools; no Plex access |
| `make validate` | Kometa validation, artwork checks, and container regression tests | Pinned Docker image; upstream version check may use the network |
| `make validate-editor` | Refresh editor schemas and test configuration validation | Python and pinned public schemas |
| `make test-make-helpers` | Test Make behavior, documentation links, and community-file placement | Python and Make |
| `make lint` | Run all pre-commit hooks | Development tools; first use may download hook environments |
| `make format` | Fix whitespace and final newlines | Edits source files selected by hooks |

`make check` also rejects tracked PATTRMM runtime files. `make format` returns nonzero when hooks change files or fail; review edits and rerun checks. `make lint-ci` is reserved for sparse CI checkouts.

## Settings and overrides

The [Makefile](../Makefile) owns supported commands and defaults:

- `KOMETA_IMAGE`: Exact runtime tag and digest for validation and previews; use the checked-in pin.
- `TEST_ENV`: Private preview environment, default `.secrets/test.env`; relative paths start at the repository root.
- `PYTHON_BIN`: Python for editor/schema checks and helper tests. Kometa regression tests use container Python.
- `NO_COLOR=1`: Disable terminal colors; captured output is always plain.

## Pull-request checks

[Validation CI](../.github/workflows/validate-pr.yml) runs configuration, editor, generated-file, helper, lint, and secret checks. Sparse CI validates artwork through Git's inventory.

[CodeQL](../.github/workflows/codeql-actions.yml) analyzes Python and GitHub Actions separately. Check both analyses and `Validate the Configuration Reels 🎞️` for the current commit before merging.

## Dependency updates

[Renovate](../.github/renovate.json5) manages runtime, schemas, Actions, CI Python, development requirements, and hooks. Runtime and schema updates share a PR; keep `ruamel.yaml` aligned with the image. VS Code manages extension updates.

## Editor schemas

Run `make validate-editor` after cloning or changing Kometa; `make check` includes it. Schemas are cached under ignored `.vscode/.schemas/`. Reload VS Code if diagnostics do not refresh.

The [schema adapter](../scripts/editor-schema.py) supports runtime fields missing upstream while rejecting unknown properties and incorrect types. Optional rating overlays are validated but remain outside the active overlay set.
