# Contributing

This is a personal Kometa configuration. Focused fixes and reusable improvements are welcome; production media is not a test fixture.

## Prepare the checkout

Install Git, GNU Make, Docker with a running engine, and Python 3.14 on your workstation. Use Docker Desktop on macOS. Commands below run from the repository root, not from the NAS media share.

1. Clone the source:

   ```sh
   git clone https://github.com/scottgigawatt/kometa-config.git
   cd kometa-config
   ```

2. Create an isolated tool environment and install commit hooks:

   ```sh
   python3.14 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   pre-commit install
   ```

3. Confirm the starting point:

   ```sh
   make check
   ```

In VS Code, run **Python: Select Interpreter** and choose `.venv/bin/python`. The selected environment supplies `ruamel.yaml` for editing; regression tests that depend on Kometa run inside the pinned container. Do not hide missing-import diagnostics or add container paths to the editor's search path.

## Make a focused change

Follow [AGENTS.md](../AGENTS.md), [EditorConfig](../.editorconfig), and the [documentation style guide](documentation-style.md). Use concise, framed comments for non-obvious behavior. Document TMDb IDs by title and year; use exactly two spaces before inline ID comments in `movies/subgenre-top.yml`.

Prefer native builders and repository-owned definitions over personal lists maintained by other users. Preserve custom artwork unless the change explicitly concerns artwork. Document the current supported arrangement, not migration history.

Keep credentials, private URLs, logs, caches, reports, `.secrets/`, and PATTRMM-generated files out of commits. See the [security policy](SECURITY.md) before sharing diagnostics.

## Validate and review

1. Stage new source files so the validator's Git-tracked snapshot includes them.
2. Run `make check`.
3. For collection or artwork changes, use the [isolated preview workflow](testing.md). Never point test configuration at production library names.
4. Review the staged diff for unrelated edits and private values.
5. Sign commits and open a focused pull request describing the change, Plex impact, and checks performed.

Explain any behavior changes separately from formatting changes. State tests that were skipped and why. Keep deployment separate from PR preparation, and leave the PR open for maintainer review.

## Ask for help

Use [support](SUPPORT.md) for non-sensitive questions and the [code of conduct](CODE_OF_CONDUCT.md) for community expectations. Report vulnerabilities privately through the [security policy](SECURITY.md).
