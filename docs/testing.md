# Test Kometa changes safely

The repository has two validation layers. Offline checks catch syntax, schema, formatting, secret, and repository-policy problems. A small Plex sandbox catches collection and artwork behavior before thousands of production items are touched.

## Run offline validation

Run the repository commands on the Mac from the local checkout, with Docker Desktop running:

```sh
cd /Users/edward/Documents/Workspace/kometa-config
```

Install the pinned development tool and run all checks:

```sh
python3 -m pip install -r requirements-dev.txt
make check
```

`make validate` runs the official Kometa 2.4.8 directory validator in an immutable container with no secrets or Plex access. Its read-only source snapshot contains only Git-tracked YAML, including working-tree edits; stage new YAML files before validation. Ignored credentials and runtime output are not mounted. Kometa performs its normal upstream version check, but the directory validator does not initialize the configured services or modify the repository.

The same command checks enabled custom artwork against the pinned Defaults catalog and case-sensitive Git filenames. It also requires both test overlay sets to match their production definitions. These checks use Git's file inventory, so continuous integration does not need to download the artwork.

Validation also checks native franchise ID comments and collection-preview isolation, with offline regression tests for unsafe libraries, connections, maintenance, download settings, and external list writers. Ruff enforces Python lint, import ordering, and formatting through pre-commit and CI.

## Prepare Plex fixture libraries

Kometa recommends the [`plex-test-libraries`](https://github.com/chazlarson/plex-test-libraries) fixtures for fast iteration. Plex runs natively on Hera and reads media from `/volume1/plex`. Create `/volume1/plex/test` in Synology File Station, then run these commands in an SSH session on Hera:

```sh
cd /volume1/plex/test
git clone https://github.com/chazlarson/plex-test-libraries.git
```

If Git is unavailable on Hera, mount the `plex` share on the Mac and clone into `/Volumes/plex/test` instead. The fixtures already include tiny media files; no production movies or episodes need to be copied. Confirm that the `PlexMediaServer` system internal user inherits read access to the test folder, its subfolders, and files.

In Plex Web, open **Settings → Manage → Libraries → Add Library** and create these libraries:

- **Movies**, named `test_movie_lib`, pointed at `/volume1/plex/test/plex-test-libraries/test_movie_lib`.
- **TV Shows**, named `test_tv_lib`, pointed at `/volume1/plex/test/plex-test-libraries/test_tv_lib`.

Use the current Plex Movie and Plex Series agents. Keep both libraries private and unpinned, and wait for Plex to scan and match the fixture titles. Point each library at its specific fixture directory, not at `/volume1/plex` or `/volume1/plex/test`. The checked-in test configuration names only these libraries; a typo therefore fails safely instead of falling back to `Movies` or `TV Shows`.

## Configure private test access

Back on the Mac, copy the environment template into the ignored secrets directory. Create it once; preserve any existing private values:

```sh
cd /Users/edward/Documents/Workspace/kometa-config
mkdir -p .secrets
cp -n example.test.env .secrets/test.env
```

Edit `.secrets/test.env` with a direct Plex server URL, a Plex token that can manage the two fixture libraries, a TMDb API key, and an MDBList API key for the custom rating ribbons. Use Hera's LAN address, such as `http://HERA_LAN_IP:32400`, rather than `localhost`, which points inside the Kometa container. Never commit that file. Every value in it is private, including a publicly reachable Plex URL; do not copy those values into tracked files, commits, pull requests, or issues.

## Render the sandbox

Run the isolated configuration from the Mac checkout with Docker Desktop running:

```sh
make test-library
```

The container connects to Hera through the Plex API; only native Plex needs filesystem access to the fixture media. The helper copies the test configuration into ignored `.kometa-test/` so Kometa writes adjacent logs, cache, reports, and overlay backups there. Edit the source under `tests/kometa/`, not the disposable runtime copy. The container mounts only the required test definitions and artwork read-only, keeps the secrets directory unmounted, and disables configuration rewriting. The sandbox creates one hidden smoke collection and applies the complete custom overlay sets to the fixture media. It does not load production playlists, mass-update operations, PATTRMM output, or production library names.

Console output and runtime logs may contain private server addresses or credentials. Keep the original output local and review any diagnostic excerpt for private values before sharing it.

The test runner uses `--no-missing` to skip reports about titles absent from the fixture libraries. Those lookups can dwarf the actual artwork work; skipping them does not change matching or overlays for titles present in Plex.

Chart and streaming builders still fetch their source lists and translate external IDs before matching the fixtures. A cold-cache run can therefore take substantially longer than rendering the small library. Preserve `.kometa-test/` between previews, including its cache and original-poster backups.

Review both Plex libraries after the run:

- Confirm the smoke collection contains expected comedy titles.
- Confirm the angled resolution and audio artwork, background, Mediastingers, and matching chart ribbons render legibly on movies.
- Confirm the provider corners, status ribbons, and matching chart ribbons render legibly on shows.
- Review `.kometa-test/logs/meta.log` for failures and unexpected warnings.

The preview uses [Kometa Defaults](https://kometa.wiki/en/latest/defaults/overlays/) for the dynamic builders, with repository-owned artwork and placement overrides. Movie and TV chart ribbons, movie backgrounds, TV status ribbons, and provider fallbacks come from local overlay definitions. Local file references ensure that a branch preview uses its own artwork, without fetching those images from the main branch on GitHub.

Provider aliases map renamed or differently capitalized upstream keys to existing custom graphics. Categories without matching artwork are explicitly disabled; movie resolution falls back to a supported base badge, and TV retains the existing provider fallback. The original file order and placement remain intentional: provider graphics share the upper-left corner, with later files layered above earlier ones. See [Kometa's overlay ordering and groups](https://kometa.wiki/en/latest/files/overlays/) before changing their precedence.

Not every fixture matches every overlay. Resolution follows Plex media information, audio badges depend on filenames and audio-track titles, and provider badges depend on the show's metadata and current streaming availability. Check the run log for actual matches before interpreting an absent badge as a rendering failure.

## Test a future configuration change

Update an overlay block in both `config.yml` and `tests/kometa/config.yml`; the parity check prevents a partial preview. Shared definitions under `overlays/` are mounted directly into the test runtime and need only one edit. Keep production operations and playlists disabled. Run `make validate`, then `make test-library`, and inspect the result before changing Hera.

Kometa's `--run-files` option may narrow collection and playlist runs, but it must not be used for overlays because overlay files are designed to run as one set.

Once the fixture result is acceptable, deploy one clean commit and run the smallest affected production scope before allowing the next full schedule.

## Preview native franchise collections

Run the collection-only preview when testing native franchise membership and posters:

```sh
make test-collections
```

This uses the same private `TEST_ENV` as the overlay preview but requires only Plex and TMDb credentials. Its separate configuration loads `movies/franchise.yml` directly, selects every `tmdb_collection` definition, and ignores their production schedules for this explicit test run. It also runs the smoke collection in both fixtures. No membership IDs are duplicated in test YAML.

The runner checks the fixture names, loaded files, source template, and selected definition attributes before starting Kometa. It has no overlay, playlist, Trakt, Radarr, Sonarr, or production-operation configuration. Existing overlay artwork is left untouched. Logs, cache, and reports remain private under `.kometa-test/collections/`.

In `test_movie_lib`, review the native franchise collections for their custom posters and release ordering, including The Purge when matching fixture media is present. A collection with no matching fixture media may be skipped below the minimum of one item; it must not trigger downloads or deletion. In `test_tv_lib`, confirm the smoke collection still works. Compare membership with the intersection of the configured TMDb collections and the fixture's matched movie IDs, rather than expecting every upstream title to be in the tiny library.

See [collection sources](collection-sources.md) for upstream membership policy and current collection mappings. The command does not deploy configuration to Hera's production checkout.
