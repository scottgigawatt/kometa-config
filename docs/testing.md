# Test Kometa changes safely

The repository has two validation layers. Offline checks catch syntax, schema, formatting, secret, and repository-policy problems. A small Plex sandbox catches collection and artwork behavior before thousands of production items are touched.

## Run offline validation

Run the repository commands on the Mac from the local checkout, with Docker Desktop running:

```sh
cd /Users/edward/Documents/Workspace/kometa-config
```

Use Python 3.14 to create an ignored local environment, install the pinned development tools, and run all checks:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
make check
```

`make validate` runs the official Kometa directory validator using the immutable image pinned in `Makefile`, with no secrets or Plex access. Its read-only source snapshot contains only Git-tracked YAML, including working-tree edits; stage new YAML files before validation. Ignored credentials and runtime output are not mounted. Kometa performs its normal upstream version check, but the directory validator does not initialize the configured services or modify the repository.

The same command checks enabled custom artwork against the pinned Defaults catalog and case-sensitive Git filenames. It also requires both test overlay sets to match their production definitions. These checks use Git's file inventory, so continuous integration does not need to download the artwork.

Validation also checks native franchise ID comments and collection-preview isolation, with offline regression tests for unsafe libraries, connections, maintenance, download settings, and external list writers. Ruff enforces Python lint, import ordering, module/class/function docstrings, and formatting through pre-commit and CI.

Renovate tracks the Kometa image, all four versioned editor schemas, GitHub Actions (including CodeQL), the CI Python version, Python development dependencies, and pre-commit hooks. Runtime and schema updates share a pull request; confirm their release versions match before merging, and keep `ruamel.yaml` in `requirements-dev.txt` aligned with the selected image. VS Code manages extension updates separately.

## CodeQL security analysis

The checked-in `.github/workflows/codeql-actions.yml` uses GitHub's Advanced setup, matching Plundarr and Privateerr's source-controlled approach. Independent matrix jobs scan Python helpers/tests and GitHub Actions on pull requests to `main`, pushes to `main`, and manual dispatches. Actions are pinned by commit, checkout credentials are not retained, and only the analysis jobs receive `security-events: write` to publish findings. Renovate maintains the action pins.

Keep CodeQL Default setup disabled; the workflow uses standard queries and needs no additional CodeQL configuration file. The ruleset requires CodeQL results, while `Validate the Configuration Reels 🎞️` remains the required repository validation check. Both language analyses must publish successfully; a green lint job alone does not establish CodeQL coverage. Check the Actions runs and the repository's code-scanning tool status for the analyzed commit and branch before merging.

CodeQL does not run Kometa, connect to Plex, or replace configuration validation and secret scanning. GitHub Code Quality is a separate product, not the Ruff checks in this repository. Do not require its results unless that product is available and deliberately enabled.

## Configure Python editing

The workspace defaults to `.venv`, whose `ruamel.yaml` version matches the pinned Kometa image. In an existing VS Code workspace, run **Python: Select Interpreter** and choose `.venv/bin/python` after setup. Pylance resolves imports from the selected environment; an earlier selection is not replaced automatically by the workspace default. See [VS Code's interpreter settings](https://code.visualstudio.com/docs/python/settings-reference).

The local environment supports editing and pre-commit. Run the regression suite through `make validate`: those tests intentionally use container paths and the pinned Kometa Defaults, rather than a local Kometa installation. Do not disable missing-import diagnostics or add container paths to Pylance's import search paths. The environment and Python bytecode remain ignored by Git.

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

## Preview movie and TV collections

Run the collection-only preview when testing native movie franchises, genre and theme rules, and curated TV collections:

```sh
make test-collections
```

This uses the same private `TEST_ENV` as the overlay preview but requires only Plex and TMDb credentials. Its separate configuration loads `movies/franchise.yml` directly, selects every `tmdb_collection` definition, and ignores their production schedules for this explicit test run. It loads the four TV collections from `shows/shuffle.yml` and runs the smoke collection in both fixtures. No membership IDs are duplicated in test YAML.

The movie preview also loads all seven collections in `movies/genre.yml` and the six searches in `movies/subgenre-rules.yml`. Horror, War, and Western follow Plex genre tags. LGBTQ+, Sports, Spy, and Stand-up Comedy combine movies from the named [TMDb keywords](https://kometa.wiki/en/latest/files/builders/tmdb/standard/keyword/) commented in source. These genres have no curated additions or external list synchronization. Genre browsing remains alphabetical and the custom posters remain local.

The six rule-based themes retain custom posters, production schedules, hidden visibility, a 250-item library limit, and release-order browsing. Five use [TMDb Discover](https://kometa.wiki/en/latest/files/builders/tmdb/discover/movie/), ordered by rating when selecting up to 1,000 candidates with an original language of English, a rating of at least 5, and at least 1,000 votes. Pipe-separated keyword IDs mean OR. Mindfuck uses IMDb's `mindbender` keyword search with the same rating and vote thresholds, English-language matching, and movie or TV-movie types; it requires no IMDb account credentials. Provider metadata determines membership, so a film can leave a collection when its tags or qualifying scores change. Other themed collections remain in `movies/subgenre-top.yml` and are not loaded by this preview.

The runner checks the fixture names, loaded files, source templates, and selected definition attributes before starting Kometa. It has no overlay, playlist, Radarr, Sonarr, or production-operation configuration. The TV builders use repository-owned [`tmdb_show` lists](https://kometa.wiki/en/latest/files/builders/tmdb/standard/show/), with each ID commented by title and year. No Trakt list or account credentials are needed for these four collections. Existing overlay artwork is left untouched. Logs, cache, and reports remain private under `.kometa-test/collections/`.

In `test_movie_lib`, review the native franchise collections for their custom posters and release ordering, including The Purge when matching fixture media is present. In `test_tv_lib`, review Adult Animation, Saturday Morning Cartoons, Classic Sitcoms, and Modern Sitcoms for whole-series membership and their custom posters. Only show IDs are included. Collections use alphabetical browsing order; use Plex's Shuffle action to play episodes. Plex groups the original and revived Will & Grace into eleven seasons under the original series, so Classic Sitcoms needs only that series ID to include both runs.

A collection with too few matching fixture items may be skipped below its configured minimum; it must not trigger downloads or deletion. Most preview sources need one item, while the five universe collections need three. Compare membership with the intersection of each configured source and the fixture's matched IDs, rather than expecting every title in the tiny library. Empty fixture results do not validate artwork: add small test media for selected titles and scan the test library before accepting the visual preview. The collection runner rejects failed or incomplete run summaries even when Kometa exits successfully.

The TV preview fixtures include Rick and Morty, Spider-Man (1994), Will & Grace (1998), and The Office (2005). One tiny episode per show covers all four collections; a second Will & Grace episode from season nine checks revival coverage. These black, silent clips are disposable test media, not copies of production episodes.

The movie preview also loads `movies/cities.yml` and `movies/universes.yml`. The six cities follow TMDb city-setting keywords, not filming locations. Marvel Cinematic Universe and DC Universe follow their named universe keywords; DC Universe specifically covers the DC Extended Universe. Star Trek combines its Original Series, Next Generation, and Alternate Reality collections. Alien / Predator combines the Alien, Predator, and AVP collections; X-Men combines X-Men, Wolverine, and Deadpool. These [native collection builders](https://kometa.wiki/en/latest/files/builders/tmdb/standard/collection/) follow TMDb membership without standalone movie additions. Films outside those native groups are not included automatically.

City collections retain their local posters, Saturday schedule, and alphabetical order. The five universes use local franchise posters, release order, and a minimum of three matching movies. Their keys are excluded from the universe Defaults in `config.yml` to prevent duplicate definitions or fallback list builders. The remaining universe Defaults are separate sources and are not part of this preview. Trakt popularity charts remain enabled in production; this preview does not load them. Tracearr continues to build the same watch-history collections with viewer-facing movie and TV summaries.

The movie fixtures include a two-second black, silent clip matched to Bo Burnham: Make Happy (2016) for Stand-up Comedy. Tiny clips for Ferris Bueller's Day Off, RoboCop, Wonder Woman, Star Trek: The Motion Picture, Star Trek: Generations, Star Trek (2009), Predator, and AVP provide coverage for the city and universe rules. These disposable fixtures avoid copying production movies. Review all seven genre posters, six rule-based theme posters, six city posters, and five universe posters in `test_movie_lib`; a successful empty result is not an artwork test.

The production `other_chart` configuration enables both `radarr_add_missing_pirated` and `radarr_search_pirated` only for Top 10 Pirated Movies of the Week. The preview never loads that chart or connects to Radarr. Offline regression tests verify its collection-specific variables against the pinned Defaults; actual Radarr additions and download searches require a separately approved production run with working private Radarr settings.

The command does not deploy configuration to Hera's production checkout.

## Preview seasonal movie collections

Run only the thirteen holiday movie collections in `test_movie_lib`:

```sh
make test-seasonal
```

The command uses the same guarded configuration and private test environment as `make test-collections`, but selects only `scheduled/seasonal.yml` collection names and the movie fixture library. It ignores production schedules so every holiday can be reviewed at any time. The runner validates the production source and renders a private `seasonal.yml` copy with scheduled deletion disabled; production keeps its existing schedule windows and deletion behavior. The full collection preview includes these holidays too.

Holiday membership uses named TMDb keywords and [TMDb Discover](https://kometa.wiki/en/latest/files/builders/tmdb/discover/movie/), supplemented by Plex romantic-comedy/drama searches for Valentine's Day and the Horror genre for Halloween. St. Patrick's Day combines Irish settings, culture, folklore, and diaspora with the holiday keyword. Mother's Day includes motherhood as well as the named holiday. No seasonal movie builder depends on an individual user's Trakt or Letterboxd list.

Christmas discovery has no popularity cutoff. Hallmark, Lifetime, and Rankin/Bass combine Christmas tagging with the named production companies; a film broadcast by one of those channels is not automatically included without matching TMDb company credits. Vintage Christmas uses a primary release date through December 31, 1979, including television specials. Horror Christmas also requires the Horror genre. The broad Christmas collection retains its explicit title exclusions. Membership follows provider metadata, not a fixed historical selection.

All seasonal movie collections explicitly disable Radarr additions, searches, upgrades, and monitoring changes, including every Christmas collection. These flags override global defaults. The test configuration has no download-client connection at all. Because Kometa requires Radarr even for false Radarr attributes, the guarded runtime copy omits only those five already-disabled flags. It preserves every builder, poster, summary, and schedule, and rejects enabled writers instead of silently removing them. Existing Radarr entries and queued downloads are not removed by this configuration.

Review each collection's membership, existing local poster, critic-rating order, and viewer-facing summary. The fixture clips cover general Irish themes and St. Patrick's Day separately, Easter, the three Christmas companies, vintage Christmas, and Christmas horror. They are tiny synthetic clips, not copies of production media. Offline tests protect the schedules, artwork mappings, Christmas exclusions, named IDs, uncapped discovery, and no-download/no-deletion preview boundaries.
