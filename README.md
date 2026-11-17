<!--
  Copyright 2025-2026 Scott Gigawatt

  SPDX-License-Identifier: Apache-2.0

  README.md: Introduce the configuration and link to operating guidance.
-->

# Kometa configuration 🎬

Personal Plex collections, custom overlays, playlists, and artwork for [Kometa](https://kometa.wiki/en/latest/). Movie franchises, TV comfort watches, and seasonal favorites get their own shelves; the posters get a wardrobe department.

<!-- markdownlint-disable MD041 -->
<hr />

<p align="center">
  <em>💫 Star this repo — could this BE any more organized?</em>
</p>

<p align="center">
  <a href="https://github.com/scottgigawatt/kometa-config/stargazers"><img src="https://img.shields.io/github/stars/scottgigawatt/kometa-config?label=Star%20Cast&amp;style=social&amp;logo=github&amp;logoColor=181717" alt="GitHub stars: Star Cast" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/forks"><img src="https://img.shields.io/github/forks/scottgigawatt/kometa-config?label=Spin-offs&amp;style=social&amp;logo=github&amp;logoColor=181717" alt="GitHub forks: Spin-offs" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/watchers"><img src="https://img.shields.io/github/watchers/scottgigawatt/kometa-config?label=Audience&amp;style=social&amp;logo=github&amp;logoColor=181717" alt="GitHub watchers: Audience" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/releases/latest"><img src="https://img.shields.io/github/v/release/scottgigawatt/kometa-config?label=Latest%20Cut&amp;style=social&amp;logo=github&amp;logoColor=181717" alt="Latest kometa-config release" /></a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/scottgigawatt/kometa-config?label=Streaming%20Rights&amp;style=flat&amp;logo=apache&amp;logoColor=white&amp;color=D7263D&amp;labelColor=D7263D" alt="License" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/commits/main"><img src="https://img.shields.io/github/last-commit/scottgigawatt/kometa-config?label=Last%20Rerun&amp;style=flat&amp;logo=git&amp;logoColor=white&amp;color=C45100&amp;labelColor=C45100" alt="Last Commit" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config"><img src="https://img.shields.io/github/repo-size/scottgigawatt/kometa-config?label=Box%20Set%20Size&amp;style=flat&amp;logo=github&amp;logoColor=white&amp;color=8C6900&amp;labelColor=8C6900" alt="Repo Size" /></a>
</p>

<p align="center">
  <a href="https://github.com/scottgigawatt/kometa-config/actions/workflows/validate-pr.yml"><img src="https://img.shields.io/github/actions/workflow/status/scottgigawatt/kometa-config/validate-pr.yml?branch=main&amp;label=Validation&amp;style=flat&amp;logo=githubactions&amp;logoColor=white&amp;color=16823B&amp;labelColor=16823B" alt="Validation on main" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/actions/workflows/codeql-actions.yml"><img src="https://img.shields.io/github/actions/workflow/status/scottgigawatt/kometa-config/codeql-actions.yml?branch=main&amp;label=CodeQL&amp;style=flat&amp;logo=githubactions&amp;logoColor=white&amp;color=116DB4&amp;labelColor=116DB4" alt="CodeQL on main" /></a>
  <a href="https://www.bestpractices.dev/projects/14948"><img src="https://img.shields.io/cii/summary/14948?label=OpenSSF%20Best%20Practices&amp;style=flat&amp;logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyIDMgNnY2YzAgNSA0IDggOSAxMCA1LTIgOS01IDktMTBWNnptLTEgMTQtNC00IDItMiAyIDIgNC00IDIgMnoiLz48L3N2Zz4%3D&amp;logoColor=white&amp;color=7C3BB3&amp;labelColor=7C3BB3" alt="OpenSSF Best Practices: passing" /></a>
</p>

<p align="center">─── ⛧ ───</p>

<p align="center">
  <em>🎬 Posters possessed? Drag that drama through the gates of</em>
  <a href="https://discord.gg/BpEGzWwGYf">
    <img src="https://img.shields.io/discord/1403601106315116626?label=%F0%9F%94%A5HADES%F0%9F%94%A5&amp;style=flat&amp;logo=discord&amp;logoColor=white&amp;color=D62F65&amp;labelColor=D62F65" alt="HADES Discord community" align="absmiddle" />
  </a>
</p>

<hr />
<!-- markdownlint-enable MD041 -->

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

## Read more and get help 📚

- [Configuration guides](docs/index.md): collections, overlays, playlists, and service connections.
- [Testing guide](docs/testing.md): local checks and safe fixture-library previews.
- [Support](docs/SUPPORT.md), [contributing](docs/CONTRIBUTING.md), [security policy](docs/SECURITY.md), and [Code of Conduct](docs/CODE_OF_CONDUCT.md).

## License

Project source is licensed under [Apache License 2.0](LICENSE). Artwork attribution does not imply ownership of third-party images or grant rights beyond those of their creators.
