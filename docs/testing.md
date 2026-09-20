# Test changes safely

Run repository commands from the workstation checkout. Use small, private Plex fixture libraries to review behavior before deploying to a large library.

## Prerequisites

Complete [contributor setup](CONTRIBUTING.md#prepare-the-checkout) for local checks. For previews, also complete the one-time [test-library setup](test-libraries.md). Keep Docker running and activate `.venv` in each new terminal session.

## Run local checks

```sh
make check
```

This runs pinned Kometa validation and regression tests, artwork/parity checks, generated-file policy, documentation and Make helper tests, lint, and secret scans. It does not connect to Plex. Stage new source files first: Kometa's read-only snapshot includes Git-tracked YAML with your working-tree edits, not ignored runtime files.

The validator may contact upstream for its version check; “local checks” does not mean every component is network-isolated. Container regression tests run with networking disabled. See [automation](automation.md) for individual commands and CI coverage.

## Choose a preview

These commands connect to Plex and modify only the named test libraries.

| Command | What it previews | Fixture libraries |
| --- | --- | --- |
| `make test-library` | Smoke collections and complete custom overlay sets | Movies and TV |
| `make test-collections` | Guarded franchises, genres, themes, cities, universes, curated TV, and holidays | Movies and TV |
| `make test-subgenres` | All 101 ranked movie themes | Movies |
| `make test-seasonal` | Thirteen holiday movie collections | Movies |
| `make test-tv-seasonal` | Halloween, Thanksgiving, and Christmas episodes | TV |

Movie and TV fixture names are `test_movie_lib` and `test_tv_lib`. The scoped collection previews ignore schedules so out-of-season results can be reviewed. They disable scheduled deletion in private runtime copies and reject download clients or external list writers. They do not load production playlists, mass-update operations, or PATTRMM output.

The collection runner loads a deliberate subset of source files, not every collection in the repository. Weekly Shuffle, people collections, pre-rolls, and production charts are not included in `make test-collections`. Pre-rolls change a server-wide setting and must not be enabled in a fixture run.

## Review the result

1. Confirm the command succeeded, then inspect its private `logs/meta.log`: a zero Kometa exit code alone does not prove every collection succeeded. The collection runner also checks run summaries.
2. Open the affected test collections in Plex. Check membership, ordering, summary, visibility, and artwork.
3. For overlays, inspect both movie and TV posters and compare the expected badge matches with the log.
4. Investigate empty results. Most sources need one matching item; the five universe collections need three. Add tiny matched fixtures when necessary—an empty collection is not a visual test.

See [collection behavior](collections.md) and [overlay behavior](overlays.md) for the expected results. Collection-only previews leave overlay artwork untouched.

## Keep runtime state private

Overlay output lives under `.kometa-test/`; collection output lives under `.kometa-test/collections/`. Preserve caches and original-poster backups between runs. Edit `tests/kometa/` or the shared source definitions, never the disposable runtime copies.

> [!WARNING]
> Console output and logs can contain tokens and private server URLs. Keep full output local. Review and redact every excerpt or screenshot before posting it, even when the address is publicly reachable.

The runners pass secrets through a private environment file without mounting the secrets directory. Source definitions and artwork are mounted read-only. Collection previews require Plex and TMDb access; the custom rating overlays also require MDBList.

## Troubleshoot a preview

- **Missing private environment:** Create `.secrets/test.env` using the [setup guide](test-libraries.md#configure-private-access); do not overwrite an existing file.
- **Pylance cannot resolve imports:** Select `.venv/bin/python` after installing the development requirements.
- **Container stays in Created:** Check Docker Desktop's status and file-sharing prompts. Restart it only when safe for other local containers.
- **Slow first run:** External chart/provider lookups can outweigh rendering time. Retain the cache and let the scoped run finish.
- **Missing badge or collection:** Confirm Plex matched the fixture, then check source membership, metadata, minimum items, and available artwork.
- **Unexpected schema warning:** Compare the exact pinned editor schema with Kometa's documented runtime behavior; do not disable validation globally.

## Deploy separately

After visual approval, deploy a clean commit through your normal deployment process. Run only the affected production scope where supported, review its log and Plex result, then allow the next full schedule. None of the preview commands deploys the production checkout.
