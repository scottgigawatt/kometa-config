<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  README.md: Introduce the configuration and link to operating guidance.
-->

# Kometa configuration 🎬

Personal Plex collections, custom overlays, and the checks that keep them ready for their close-up. This repository contains configuration and artwork; [Kometa](https://kometa.wiki/en/latest/) is the application that runs them.

[![License](https://img.shields.io/github/license/scottgigawatt/kometa-config)](LICENSE) [![Validation](https://github.com/scottgigawatt/kometa-config/actions/workflows/validate-pr.yml/badge.svg)](https://github.com/scottgigawatt/kometa-config/actions/workflows/validate-pr.yml)

## Start here

1. Follow [contributor setup](docs/CONTRIBUTING.md#prepare-the-checkout) to install the pinned checks.
2. Run `make check` before changing a deployment.
3. Prepare the [Plex test libraries](docs/test-libraries.md), then follow the [testing guide](docs/testing.md) for collection or artwork changes.

Run commands from the repository root on your workstation. Plain `make` shows help; it never starts Kometa or changes Plex.

> [!IMPORTANT]
> Keep credentials, private server addresses, logs, caches, reports, and generated files out of Git. Test access belongs in the ignored `.secrets/test.env`; production connections belong in private deployment settings. See the [security policy](docs/SECURITY.md).

## Documentation

The [documentation index](docs/index.md) links to the complete guide.

- [Testing](docs/testing.md): Choose a safe check or preview.
- [Collection behavior](docs/collections.md): Membership, ordering, schedules, and download boundaries.
- [Custom overlays](docs/overlays.md): Artwork, fallbacks, and visual review.
- [Service connections](docs/service-connections.md): Kometa, PATTRMM, and Tracearr.
- [Automation](docs/automation.md): Make commands, CI, CodeQL, and Renovate.
- [Contributing](docs/CONTRIBUTING.md), [support](docs/SUPPORT.md), and [code of conduct](docs/CODE_OF_CONDUCT.md).

## Artwork and credits

Explore the custom [subgenre posters](assets/posters/subgenre_top/) and their [collection definitions](movies/top-rated-subgenres.yml).

![A selection of custom subgenre collection posters](https://github.com/scottgigawatt/kometa-config/assets/16313565/091fc37c-e9d4-4f8e-8e2c-0b537f46e8c0)

Thanks to [TheChrisK](https://github.com/TheChrisK) for original files and posters, [meisnate12](https://github.com/meisnate12) for Kometa and images, [s0len](https://github.com/s0len) for TV overlays, [pterisaur](https://github.com/pterisaur) for people posters, and [0x5f3](https://github.com/0x5f3) for top subgenre collections.

## License

Project source is licensed under [Apache License 2.0](LICENSE). Artwork attribution does not imply ownership of third-party images or grant rights beyond those of their creators.
