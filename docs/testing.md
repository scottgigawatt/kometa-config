# Test Kometa changes safely

The repository has two validation layers. Offline checks catch syntax, schema, formatting, secret, and repository-policy problems. A small Plex sandbox catches collection and artwork behavior before thousands of production items are touched.

## Run offline validation

Install the pinned development tool and run all checks:

```sh
python3 -m pip install -r requirements-dev.txt
make check
```

`make validate` runs the official Kometa 2.4.8 directory validator in an immutable container with no secrets or Plex access and a read-only repository mount. Kometa performs its normal upstream version check, but the directory validator does not initialize the configured services or modify the repository.

## Prepare Plex fixture libraries

Kometa recommends the [`plex-test-libraries`](https://github.com/chazlarson/plex-test-libraries) fixtures for fast iteration. Clone that repository outside this checkout and make the two fixture directories available to Plex:

```sh
git clone https://github.com/chazlarson/plex-test-libraries.git
```

Create two Plex libraries with these exact names:

- `test_movie_lib`, pointed at the fixture repository's `test_movie_lib` directory.
- `test_tv_lib`, pointed at the fixture repository's `test_tv_lib` directory.

Keep both libraries private, unpinned, and separate from production media. The checked-in test configuration names only these libraries; a typo therefore fails safely instead of falling back to `Movies` or `TV Shows`.

## Configure private test access

Copy the environment template into the ignored secrets directory:

```sh
mkdir -p .secrets
cp example.test.env .secrets/test.env
```

Edit `.secrets/test.env` with a direct Plex server URL, a Plex token that can manage the two fixture libraries, and a TMDb API key. Never commit that file.

## Render the sandbox

Run the isolated configuration:

```sh
make test-library
```

The container mounts the repository read-only and writes only logs and cache data under ignored `.kometa-test/`. The sandbox creates one hidden smoke collection and applies maintained Kometa default overlays to the fixture media. It does not load production playlists, mass-update operations, PATTRMM output, or production library names.

Review both Plex libraries after the run:

- Confirm the smoke collection contains expected comedy titles.
- Confirm resolution, audio, and Mediastingers render legibly on movies.
- Confirm network, streaming, and studio overlays render legibly on shows.
- Review `.kometa-test/logs/meta.log` for failures and unexpected warnings.

## Test a future configuration change

Add only the candidate collection or overlay block to `tests/kometa/config.yml`, or temporarily point that file at the changed source file. Keep production operations and playlists disabled. Run `make validate`, then `make test-library`, and inspect the result before changing Hera.

Kometa's `--run-files` option may narrow collection and playlist runs, but it must not be used for overlays because overlay files are designed to run as one set.

Once the fixture result is acceptable, deploy one clean commit and run the smallest affected production scope before allowing the next full schedule.
