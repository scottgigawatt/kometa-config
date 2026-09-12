# Collection sources

Native builders keep predictable movie groups independent of another person's list account. Curated themes and live charts still use their configured sources; a missing movie mapping is not proof that the whole list has disappeared.

## Native franchise membership

The TMDb-backed definitions in `movies/franchise.yml` follow upstream collection membership and use release order. Collection names, custom posters, sort positions, and the Sunday/Thursday schedule are maintained locally. The ordinary `tmdb_collection` builder supplies membership without replacing local artwork or descriptions through a details builder.

| Plex collection | TMDb collection |
| --- | --- |
| Jurassic Park Collection | [Jurassic Park Collection](https://www.themoviedb.org/collection/328) |
| American Pie Collection | [American Pie Collection](https://www.themoviedb.org/collection/2806) |
| Batman Collection | [Batman Collection](https://www.themoviedb.org/collection/120794) |
| Dune Collection | [Dune Collection](https://www.themoviedb.org/collection/726871) |
| Indiana Jones Collection | [Indiana Jones Collection](https://www.themoviedb.org/collection/84) |
| Jack Ryan Collection | [The Jack Ryan Collection](https://www.themoviedb.org/collection/192492) |
| James Bond Collection | [James Bond Collection](https://www.themoviedb.org/collection/645) |
| Jason Bourne Collection | [The Bourne Collection](https://www.themoviedb.org/collection/31562) |
| Kung Fu Panda Collection | [Kung Fu Panda Collection](https://www.themoviedb.org/collection/77816) |
| Planet of the Apes | [Original](https://www.themoviedb.org/collection/1709) and [reboot](https://www.themoviedb.org/collection/173710) collections |
| Pirates of the Caribbean | [Pirates of the Caribbean Collection](https://www.themoviedb.org/collection/295) |
| The Purge Collection | [The Purge Collection](https://www.themoviedb.org/collection/256322) |
| Transformers Collection | [Transformers Collection](https://www.themoviedb.org/collection/8650) |

These are TMDb's groups, not exhaustive franchise filmographies. Spin-offs, adaptations, standalone remakes, and future entries are included only when present in the selected upstream collection. Planet of the Apes combines its two named TMDb groups without standalone additions. Other definitions in the file retain their Plex searches or explicit IMDb membership.

`sync_mode: sync` removes out-of-scope movies from these Plex collections; it does not delete media. No download or search behavior is enabled by the franchise template. See [Kometa's TMDb collection builder](https://kometa.wiki/en/latest/files/builders/tmdb/standard/collection/) for matching behavior.

## Readable identifiers

Place each explicit TMDb ID on its own line with two spaces before an identifying comment. A collection ID names the upstream collection. An individual movie ID names the movie and release year. Keep comments adjacent to their values and avoid copying a changing collection's entire membership into comments.

## Favorites and curated sources

Edward's movie favorites remain connected to the owner-controlled Trakt list. Its existing missing-movie acquisition settings are production-only and are never loaded by the fixture preview.

Non-owner movie favorites are commented out. TV favorites are retained in `shows/favorites.yml.disabled`, outside Kometa's `.yml` folder discovery. Disabling those definitions does not explicitly delete existing Plex collections or artwork; they simply stop being managed by those definitions.

For curated themes, compare actual membership before adopting a replacement with the same title. Prefer an owner-maintained ID snapshot when a stable curated selection is more important than continuous updates. Letterboxd copies remain dependent on Letterboxd access; its private API is not a prerequisite for Kometa's URL-based list builder. See [Letterboxd builder documentation](https://kometa.wiki/en/latest/files/builders/letterboxd/list/).

## Diagnose source failures

Keep original runtime logs private. Distinguish missing or inaccessible lists from HTTP authentication/rate-limit failures, individual deleted TMDb records, unsupported media types, and missing local artwork. Do not suppress all errors, ignore arbitrary IDs globally, or replace an entire curated list because a few items cannot be mapped.

Use the [collection-only fixture preview](testing.md#preview-native-franchise-collections) before deployment. Fixture success verifies matching for present media, not coverage of every upstream title. A full source lookup and a fixture-membership comparison complement the visual review.
