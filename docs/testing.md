# Test changes safely 🧪

Run checks first, then preview collection or artwork changes in private Plex test libraries. Give the YAML a screen test before the premiere.

## Prerequisites

Complete [contributor setup](CONTRIBUTING.md#prepare-the-checkout). Run commands from the workstation checkout with Docker running and `.venv` active. Previews also require the one-time [test-library setup](test-libraries.md).

## Run local checks

Stage new source files so validation includes them, then run:

```sh
make check
```

This checks configuration, artwork references, editor schemas, regression tests, documentation links, lint, and secrets without connecting to Plex. It uses the pinned Kometa image and tracked files with your working-tree edits. Tool installation, schema downloads, and Kometa's version check need network access.

For documentation-only changes, this completes validation; also review the rendered Markdown. Individual checks are listed in [automation](automation.md).

## Choose a preview

These commands modify the `test_movie_lib` and `test_tv_lib` fixture libraries. Run the smallest preview that covers your change.

| Command | What it previews | Libraries |
| --- | --- | --- |
| `make test-library` | Smoke collections, the default DCEU collection, and complete custom overlay sets | Movies and TV |
| `make test-collections` | Franchises, genres, subgenres, cities, universes, curated TV, holidays, and Midnight Cinema | Movies and TV |
| `make test-subgenres` | Ranked movie themes | Movies |
| `make test-seasonal` | Holiday movies | Movies |
| `make test-tv-seasonal` | Halloween, Thanksgiving, and Christmas episodes | TV |
| `make test-midnight` | Midnight Cinema movies, miniseries, and episodes | Movies and TV |

Collection previews ignore schedules and disable scheduled deletion in private runtime copies. They validate production download settings, then omit those settings and all download-client connections. Midnight Cinema previews also hide their collections from home and shared screens. Collection-only previews leave overlays untouched.

The previews cover the sources listed above. They do not load production favorites, people collections, Weekly Shuffle, charts, playlists, PATTRMM output, or the Midnight Cinema series-request helper. Never enable pre-rolls in a fixture run: they change a server-wide setting.

## Review the result

1. Confirm the command succeeded and inspect its private `logs/meta.log` for errors. A zero exit code alone does not prove every collection succeeded.
2. In Plex, check membership, order, summary, visibility, and artwork against [collection behavior](collections.md) or [overlay behavior](overlays.md).
3. For overlays, inspect both movie and TV posters for missing badges, overlap, and legibility.
4. Investigate empty collections: check matching, provider metadata, and minimum-item rules. Add tiny matched fixtures as needed; an empty collection is not a visual test.

Overlay output lives under `.kometa-test/`; collection output lives under `.kometa-test/collections/`. Preserve caches and original-poster backups. Edit source definitions or `tests/kometa/`, never disposable runtime copies.

> [!WARNING]
> Logs and console output can contain tokens and private server URLs. Keep full output local and redact every excerpt or screenshot before sharing it.

## Troubleshoot a preview

- **Missing private environment:** Create `.secrets/test.env` using the [setup guide](test-libraries.md#configure-private-access); preserve existing values.
- **Container stays in Created:** Check Docker Desktop's status and file-sharing prompts.
- **Slow first run:** Provider lookups can take longer than rendering. Preserve the cache and let the scoped run finish.
- **Missing badge or collection:** Check Plex matching, source rules, minimum items, and artwork. See [overlay diagnostics](overlays.md#interpret-missing-badges).
- **Editor errors:** Select `.venv/bin/python` for imports. Run `make validate-editor` to refresh the schema and reload VS Code if needed; investigate remaining diagnostics without disabling validation.

## Deploy separately

After visual approval, deploy a clean commit through your normal process. Run the affected production scope where supported, review its log and Plex result, then allow the next full schedule. Preview commands do not deploy production.
