<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  README.md: Introduce the configuration and link to operating guidance.
-->

<!-- markdownlint-disable MD041 -->
<hr />

<p align="center">
  <em>💫 Star this repo — could this BE any more organized?</em>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/scottgigawatt/kometa-config?label=Streaming%20Rights&amp;color=blue" alt="License" />
  <img src="https://img.shields.io/github/last-commit/scottgigawatt/kometa-config?label=Last%20Rerun&amp;logo=git&amp;color=green" alt="Last Commit" />
  <img src="https://img.shields.io/github/repo-size/scottgigawatt/kometa-config?label=Box%20Set%20Size&amp;color=orange" alt="Repo Size" />
  <a href="https://www.bestpractices.dev/projects/14948"><img src="https://www.bestpractices.dev/projects/14948/badge" alt="OpenSSF Best Practices: passing" /></a>
</p>

<p align="center">─── ⛧ ───</p>

<p align="center">
  <em>📺 Got messy metadata or stubborn seasons? We’ll be there for you… in <strong>🔥HADES🔥 Discord</strong>.</em>
</p>

<p align="center">
  <a href="https://discord.gg/BpEGzWwGYf">
    <img src="https://img.shields.io/discord/1403601106315116626?label=%F0%9F%94%A5HADES%F0%9F%94%A5%20Discord&amp;logo=discord&amp;logoColor=white&amp;color=5865F2" alt="🔥HADES🔥 Discord" />
  </a>
</p>

<hr />
<!-- markdownlint-enable MD041 -->

# Kometa configuration 🎬

Personal Plex collections, custom overlays, playlists, and artwork for [Kometa](https://kometa.wiki/en/latest/). Movie franchises, TV comfort watches, and seasonal favorites get their own shelves; the posters get a wardrobe department.

[![Validation on main](https://img.shields.io/github/actions/workflow/status/scottgigawatt/kometa-config/validate-pr.yml?branch=main&label=Validation)](https://github.com/scottgigawatt/kometa-config/actions/workflows/validate-pr.yml)
[![CodeQL on main](https://img.shields.io/github/actions/workflow/status/scottgigawatt/kometa-config/codeql-actions.yml?branch=main&label=CodeQL)](https://github.com/scottgigawatt/kometa-config/actions/workflows/codeql-actions.yml)

## Start here 🎟️

This repository supplies configuration for your own Plex and Kometa deployment. Start with the guide for your task:

- **Explore the setup:** Browse [collections](docs/collections.md), [overlays](docs/overlays.md), and the [documentation index](docs/index.md).
- **Connect services:** Configure the shared runtime and credentials in [service connections](docs/service-connections.md).
- **Make a change:** Follow [contributor setup](docs/CONTRIBUTING.md#prepare-the-checkout), then the [testing guide](docs/testing.md). Rehearse before opening night.

Run repository commands from your workstation checkout. Plain `make` lists the available checks and previews.

> [!IMPORTANT]
> Keep credentials, private server addresses, logs, and generated runtime files out of Git. Use private deployment settings and the ignored `.secrets/test.env` for tests. See the [security policy](docs/SECURITY.md).

## Artwork and credits 🎨

Explore the custom [subgenre posters](assets/posters/subgenre_top/) and their [collection definitions](movies/top-rated-subgenres.yml).

![Scrolling tour of movie collection posters in Plex](assets/previews/movie-collections.gif)

[View a still image of the collection posters](assets/previews/movie-collections.jpg).

Thanks to [TheChrisK](https://github.com/TheChrisK) for original files and posters, [meisnate12](https://github.com/meisnate12) for Kometa and images, [s0len](https://github.com/s0len) for TV overlays, and [pterisaur](https://github.com/pterisaur) for people posters. Stay for the credits; these people brought the production value.

## Help and contributions

Join [🔥HADES🔥 Discord](https://discord.gg/BpEGzWwGYf) for community help, or use [support](docs/SUPPORT.md) to report an issue. Contributions follow the [contribution guide](docs/CONTRIBUTING.md) and [code of conduct](docs/CODE_OF_CONDUCT.md).

## License

Project source is licensed under [Apache License 2.0](LICENSE). Artwork attribution does not imply ownership of third-party images or grant rights beyond those of their creators.
