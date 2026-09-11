# Contributing

This is a personal Kometa configuration, but focused corrections and reusable improvements are welcome.

## Before changing configuration

Keep credentials and runtime data outside Git. PATTRMM-generated YAML, Kometa logs, missing-item reports, caches, and `.secrets/` content do not belong in commits.

Install the local checks:

```sh
python3 -m pip install -r requirements-dev.txt
pre-commit install
```

Run the repository gate before opening a pull request:

```sh
make check
```

Changes that alter collections, playlists, or artwork must also be rendered in the isolated Plex fixture libraries described in [the testing guide](docs/testing.md).

## Pull requests

Keep source-only cleanup separate from Plex behavior changes. Explain the affected libraries, external sources, expected Plex changes, validation performed, and rollback path. Do not include generated runtime files or unrelated artwork.
