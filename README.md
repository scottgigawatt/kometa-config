<!--
  Copyright 2025-2026 Scott Gigawatt

  Licensed under the Apache License, Version 2.0.

  README.md: Introduce the configuration and link to operating guidance.
-->

<!-- markdownlint-disable-next-line MD033 MD041 -->
<hr />

<!-- markdownlint-disable MD033 -->
<p align="center">
  <em>🍿 Enjoy the feature? Leave a ⭐. The algorithm demands a sequel.</em>
</p>

<p align="center">
  <a href="https://github.com/scottgigawatt/kometa-config/stargazers"><img src="https://img.shields.io/github/stars/scottgigawatt/kometa-config?style=social&amp;label=Standing%20Ovations" alt="GitHub stars: Standing Ovations" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/forks"><img src="https://img.shields.io/github/forks/scottgigawatt/kometa-config?style=social&amp;label=Spin-offs" alt="GitHub forks: Spin-offs" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/watchers"><img src="https://img.shields.io/github/watchers/scottgigawatt/kometa-config?style=social&amp;label=Next%20Episode" alt="GitHub watchers: Next Episode" /></a>
</p>

<p align="center">
  <a href="https://kometa.wiki/en/latest/"><img src="https://img.shields.io/badge/Directed%20by-Kometa-7C3AED" alt="Configuration for Kometa" /></a>
  <a href="./docs/collections.md"><img src="https://img.shields.io/badge/Now%20Showing-Plex%20Collections-E5A00D?logo=plex&amp;logoColor=white" alt="Plex collection configuration" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/scottgigawatt/kometa-config?label=Fine%20Print&amp;color=8250DF" alt="Apache 2.0 source license" /></a>
</p>

<p align="center">
  <a href="https://github.com/scottgigawatt/kometa-config/actions/workflows/validate-pr.yml"><img src="https://img.shields.io/github/actions/workflow/status/scottgigawatt/kometa-config/validate-pr.yml?branch=main&amp;label=Screen%20Test&amp;logo=githubactions&amp;logoColor=white" alt="Repository validation status on main" /></a>
  <a href="https://github.com/scottgigawatt/kometa-config/actions/workflows/codeql-actions.yml"><img src="https://img.shields.io/github/actions/workflow/status/scottgigawatt/kometa-config/codeql-actions.yml?branch=main&amp;label=Security%20Screening&amp;logo=githubactions&amp;logoColor=white" alt="CodeQL analysis status on main" /></a>
</p>

<p align="center">─── 🎟️ ───</p>

<p align="center">
  <em>💀 Plot holes in your setup? Meet the supporting cast in <strong>🔥HADES🔥</strong>.</em>
</p>

<p align="center">
  <a href="https://discord.gg/BpEGzWwGYf"><img src="https://img.shields.io/discord/1403601106315116626?label=%F0%9F%94%A5HADES%F0%9F%94%A5&amp;logo=discord&amp;logoColor=white&amp;color=5865F2" alt="Join the HADES Discord community" /></a>
</p>
<!-- markdownlint-enable MD033 -->

<!-- markdownlint-disable-next-line MD033 -->
<hr />

# Kometa configuration 🎬

Personal Plex collections, custom overlays, and the checks that keep them ready for their close-up. This repository contains configuration and artwork; [Kometa](https://kometa.wiki/en/latest/) is the application that runs them. Think of it as the production binder, not the projector.

Movie franchises, TV comfort watches, seasonal favorites, and a Weekly Shuffle with actual standards. The posters get a wardrobe department; the YAML gets a script supervisor. Nobody gives Christmas a surprise July cameo. 🍿

## Start here 🎟️

1. Follow [contributor setup](docs/CONTRIBUTING.md#prepare-the-checkout) to install the pinned checks.
2. Run `make check` before changing a deployment.
3. Prepare the [Plex test libraries](docs/test-libraries.md), then follow the [testing guide](docs/testing.md) for collection or artwork changes.

Run commands from the repository root on your workstation. Plain `make` shows help; it never starts Kometa or changes Plex. Rehearse in the test libraries before opening night.

> [!IMPORTANT]
> Keep credentials, private server addresses, logs, caches, reports, and generated files out of Git. Test access belongs in the ignored `.secrets/test.env`; production connections belong in private deployment settings. See the [security policy](docs/SECURITY.md).

## Documentation: behind the scenes 📚

The [documentation index](docs/index.md) links to the complete guide.

- [Testing](docs/testing.md): Choose a safe check or preview.
- [Collection behavior](docs/collections.md): Membership, ordering, schedules, and download boundaries.
- [Custom overlays](docs/overlays.md): Artwork, fallbacks, and visual review.
- [Service connections](docs/service-connections.md): Kometa, PATTRMM, and Tracearr.
- [Automation](docs/automation.md): Make commands, CI, CodeQL, and Renovate.
- [Contributing](docs/CONTRIBUTING.md), [support](docs/SUPPORT.md), and [code of conduct](docs/CODE_OF_CONDUCT.md).

## Artwork and credits 🎨

Explore the custom [subgenre posters](assets/posters/subgenre_top/) and their [collection definitions](movies/top-rated-subgenres.yml).

![A selection of custom subgenre collection posters](https://github.com/scottgigawatt/kometa-config/assets/16313565/091fc37c-e9d4-4f8e-8e2c-0b537f46e8c0)

Thanks to [TheChrisK](https://github.com/TheChrisK) for original files and posters, [meisnate12](https://github.com/meisnate12) for Kometa and images, [s0len](https://github.com/s0len) for TV overlays, and [pterisaur](https://github.com/pterisaur) for people posters. Stay for the credits; these people brought the production value.

## License

Project source is licensed under [Apache License 2.0](LICENSE). Artwork attribution does not imply ownership of third-party images or grant rights beyond those of their creators.
