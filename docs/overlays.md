# Custom overlays 🎨

The movie and TV libraries use repository-owned artwork and placement with [Kometa Defaults builders](https://kometa.wiki/en/latest/defaults/overlays/). The posters get the costume department; the builders handle casting.

## Edit and preview

1. Update an overlay block in both [production config](../config.yml) and [test config](../tests/kometa/config.yml). The parity check rejects mismatched definitions.
2. Edit shared files under [overlays](../overlays/) once; the preview mounts them directly.
3. Run `make check`, then `make test-library`.
4. Review both fixture libraries using the [testing checklist](testing.md#review-the-result).

> [!IMPORTANT]
> Evaluate overlay files as complete sets. Do not use Kometa's `--run-files` option to narrow overlays; layering and suppression depend on the whole set.

## Artwork and fallbacks

Movie backgrounds, chart ribbons, TV status ribbons, provider fallbacks, and other custom graphics use files from the checkout being previewed.

Provider aliases map upstream keys to local graphics. Categories without matching artwork are disabled; resolution and provider definitions specify fallback badges where available.

Provider graphics share the upper-left corner. Later files layer above earlier files, so ordering is intentional. Read [Kometa's overlay ordering and groups](https://kometa.wiki/en/latest/files/overlays/) before changing precedence.

## Interpret missing badges

Not every fixture matches every overlay. Resolution follows Plex media information; audio badges depend on filenames and audio-track titles; provider badges depend on metadata and current streaming availability. Review actual builder matches in the private log before treating an absent badge as a rendering failure.

Check movie resolution/audio graphics, backgrounds, Mediastingers, and chart ribbons. On TV posters, check provider corners, status ribbons, and charts for legibility and overlap.

## Preserve preview state

Keep original-poster backups and caches under the ignored `.kometa-test/`. A cold cache can make external chart and ID lookups much slower than rendering the tiny library. Collection-only previews leave overlay artwork untouched.

Offline checks compare enabled artwork references with case-sensitive Git filenames and the pinned Defaults catalog. These checks work in sparse CI without downloading the full artwork library.
