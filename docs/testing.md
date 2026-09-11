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

Edit `.secrets/test.env` with a direct Plex server URL, a Plex token that can manage the two fixture libraries, and a TMDb API key. Use Hera's LAN address, such as `http://HERA_LAN_IP:32400`, rather than `localhost`, which points inside the Kometa container. Never commit that file. Every value in it is private, including a publicly reachable Plex URL; do not copy those values into tracked files, commits, pull requests, or issues.

## Render the sandbox

Run the isolated configuration from the Mac checkout with Docker Desktop running:

```sh
make test-library
```

The container connects to Hera through the Plex API; only native Plex needs filesystem access to the fixture media. The helper copies the test configuration into ignored `.kometa-test/` so Kometa writes adjacent logs, cache, reports, and overlay backups there. Edit the source under `tests/kometa/`, not the disposable runtime copy. The container mounts the repository read-only and disables configuration rewriting. The sandbox creates one hidden smoke collection and applies maintained Kometa default overlays to the fixture media. It does not load production playlists, mass-update operations, PATTRMM output, or production library names.

Console output and runtime logs may contain private server addresses or credentials. Keep the original output local and review any diagnostic excerpt for private values before sharing it.

Review both Plex libraries after the run:

- Confirm the smoke collection contains expected comedy titles.
- Confirm resolution, audio, and Mediastingers render legibly on movies.
- Confirm network, streaming, and studio overlays render legibly on shows.
- Review `.kometa-test/logs/meta.log` for failures and unexpected warnings.

The preview uses the same dynamic defaults as the production configuration: `resolution`, `audio_codec`, and `mediastinger` for movies, plus `network`, `streaming`, and `studio` for shows. Their artwork, backgrounds, and positions come from [Kometa Defaults](https://kometa.wiki/en/latest/defaults/overlays/). Custom chart ribbons and show-status artwork remain outside this focused preview.

Not every fixture matches every overlay. Resolution follows Plex media information, audio badges depend on filenames and audio-track titles, and provider badges depend on the show's metadata and current streaming availability. Check the run log for actual matches before interpreting an absent badge as a rendering failure.

## Test a future configuration change

Add only the candidate collection or overlay block to `tests/kometa/config.yml`, or temporarily point that file at the changed source file. Keep production operations and playlists disabled. Run `make validate`, then `make test-library`, and inspect the result before changing Hera.

Kometa's `--run-files` option may narrow collection and playlist runs, but it must not be used for overlays because overlay files are designed to run as one set.

Once the fixture result is acceptable, deploy one clean commit and run the smallest affected production scope before allowing the next full schedule.
