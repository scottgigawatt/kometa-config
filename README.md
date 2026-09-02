<hr />

<p align="center">
  <em>💫 Star this repo — could this BE any more organized?</em>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/scottgigawatt/kometa-config?label=Streaming%20Rights&color=blue" alt="License" />
  <img src="https://img.shields.io/github/last-commit/scottgigawatt/kometa-config?label=Last%20Rerun&logo=git&color=green" alt="Last Commit" />
  <img src="https://img.shields.io/github/repo-size/scottgigawatt/kometa-config?label=Box%20Set%20Size&color=orange" alt="Repo Size" />
</p>

<p align="center">─── ⛧ ───</p>

<p align="center">
    <em>📺 Got messy metadata or stubborn seasons? We’ll be there for you… in <strong>🔥HADES🔥</strong>.</em>
</p>

<p align="center">
  <a href="https://discord.gg/BpEGzWwGYf">
    <img src="https://img.shields.io/discord/1403601106315116626?label=%F0%9F%94%A5HADES%F0%9F%94%A5&logo=discord&logoColor=white&color=5865F2" alt="🔥HADES🔥 Discord" />
  </a>
</p>

<hr />

# Kometa Configuration

This repository contains configuration files tailored for enhancing Plex media libraries using Kometa.

![collections](https://github.com/scottgigawatt/kometa-config/assets/16313565/70ca085d-0259-44bb-8849-f4f99a8f5d75 "Collections")

## Description

Configuration, artwork, and validation tooling for my Kometa-managed Plex libraries. The Git checkout is the source of truth for human-authored files; credentials, logs, caches, reports, and helper-generated runtime files remain private and untracked.

## Credits

Special thanks to contributors:

- **[TheChrisK](https://github.com/TheChrisK)**: Original files and posters
- **[meisnate12](https://github.com/meisnate12)**: Kometa and images
- **[s0len](https://github.com/s0len)**: TV overlays
- **[pterisaur](https://github.com/pterisaur)**: People posters
- **[0x5f3](https://github.com/0x5f3)**: Top subgenre collections

## My Contributions

### Subgenre Posters

Custom [subgenre posters](assets/posters/subgenre_top/) to enhance Plex libraries. View the [subgenre collection configuration](movies/subgenre-top.yml).

![subgenre-posters](https://github.com/scottgigawatt/kometa-config/assets/16313565/091fc37c-e9d4-4f8e-8e2c-0b537f46e8c0 "Subgenre Posters")

## Usage

Clone the repository, install the pinned local checks, and validate it before connecting Kometa to Plex:

```sh
git clone https://github.com/scottgigawatt/kometa-config.git
cd kometa-config
python3 -m pip install -r requirements-dev.txt
make check
```

Real credentials belong under the ignored `.secrets/` directory or in the private deployment environment. The obvious values in `config.yml` are placeholders.

The production Duplex deployment mounts this checkout as Kometa's writable `/config` directory. PATTRMM shares that mount and generates `*-in-history.yml`, `*-by-size.yml`, `*-returning-soon-metadata.yml`, and `*-returning-soon-overlay.yml` runtime inputs. Those generated files are ignored and must not be committed.

See the [Kometa documentation](https://kometa.wiki/en/latest/) for application behavior and the [testing guide](docs/testing.md) for the isolated Plex fixture-library workflow.

## Validation

The default Make target lists the supported commands:

```sh
make
```

Run the complete local gate with:

```sh
make check
```

The pull-request workflow performs the same configuration and lint checks from a text-only sparse checkout, avoiding a multi-gigabyte artwork download.

## Test libraries

Kometa recommends small fixture libraries for fast collection and overlay iteration. This repository includes a safe test configuration for the upstream `test_movie_lib` and `test_tv_lib` fixtures:

```sh
cp example.test.env .secrets/test.env
make test-library
```

Complete the private values and Plex library setup described in [the testing guide](docs/testing.md) before running the command. The test configuration never names the production `Movies` or `TV Shows` libraries.

## Generated files

PATTRMM intentionally writes changing YAML into the mounted runtime checkout. Repository checks reject those filenames if they are accidentally staged, while `.gitignore` keeps normal regeneration quiet. Change their behavior through PATTRMM preferences rather than editing the generated output.

## License

Licensed under the [Apache License 2.0](LICENSE). See LICENSE file for details.

---

For questions or issues, open an issue on this repository.
