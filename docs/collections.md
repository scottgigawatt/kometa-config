# Collection behavior 🍿

Use this guide to understand membership and side effects before changing or running a definition. Linked source files own exact IDs, thresholds, schedules, and artwork.

## Movie franchises, genres, and settings

[Franchises](../movies/franchises.yml) follow native [TMDb collection membership](https://kometa.wiki/en/latest/files/builders/tmdb/standard/collection/) in release order. [Genres](../movies/genres.yml) use Plex tags or the TMDb keywords recorded in source.

[Cities](../movies/cities.yml) match settings, not filming locations. [Universes](../movies/universes.yml) combine native collections or use the MCU keyword, require at least three matches, and exclude corresponding Defaults keys to prevent duplicates. Kometa Defaults supplies the DC Extended Universe; the rebooted DC Universe is excluded.

## Ranked subgenres

[top-rated-subgenres.yml](../movies/top-rated-subgenres.yml) owns the themes and provider-specific rules. Shared templates supply local posters, weekly refreshes, hidden visibility, release order, and a 250-item collection limit.

TMDb Discover ranks up to 1,000 English-original candidates; pipe-separated keywords mean OR and comma-separated genres mean AND. IMDb keyword searches cover themes with sparse TMDb tagging and need no personal account or lists. Both templates normally require rating ≥5 and 1,000 votes; individual exceptions are in source.

## Weekly Shuffle

The [movie shuffle](../movies/weekly-shuffle.yml) samples up to 250 random watched or unwatched movies every Monday. It keeps up to 25 that meet TMDb rating ≥6 and vote-count ≥250. Christmas/Xmas titles and the Christmas keyword are excluded year-round; incomplete metadata can affect matches. Fewer qualifying films produce a smaller collection.

## People collections

[People collections](../movies/actors-directors-writers.yml) rank Plex actor, director, and writer credits using shared artwork and a Saturday schedule. Explicit actor collections are excluded before the dynamic limit is filled. Check private logs for cross-role name collisions.

## TV series and holiday episodes

[Networks](../shows/networks.yml) identify original broadcasters or platforms, not current streaming availability. Country variants remain separate. [Curated TV](../shows/animation-and-sitcoms.yml) uses recorded show IDs, browses alphabetically, and supports Plex Shuffle. Plex groups both Will & Grace runs under the original ID.

[TV holidays](../shows/holiday-episodes.yml) match episode titles or summaries; a parent-show match does not add every episode. Metadata can omit or incidentally mention holidays, so inspect actual matches. No air-date cutoff applies. These definitions contain no Sonarr attributes, including false ones. Previews disable scheduled deletion.

## Seasonal movies

[Seasonal definitions](../scheduled/holiday-movies.yml) use provider keywords and Plex genres. Company-specific Christmas collections require matching credits plus Christmas tagging; a channel broadcast alone is insufficient. Vintage Christmas covers releases through 1979, including specials. Source owns exclusions and holiday windows.

Seasonal movies disable Radarr additions, searches, upgrades, and monitoring changes. Existing Radarr entries and queued downloads remain untouched.

## Award winners

[Critics Choice](../scheduled/critics-choice.yml), [Oscars](../scheduled/oscars.yml), [Golden Globes](../scheduled/golden-globes.yml), and [Emmys](../scheduled/emmy-awards.yml) select winners from six ceremonies using Kometa's validated IMDb award-year data. Premiere year does not determine the ceremony. Nominees are excluded; future ceremonies must be validated before selection. Source defines all-time categories and their historical names.

Movie awards refresh January through April 1. Emmys refresh Mondays and remain available year-round. New ceremony results depend on upstream data updates.

## Midnight Cinema 🌙

[Movies](../movies/midnight-curated.yml) and [TV selections](../shows/midnight-cinema.yml) use recorded IDs and searches. [Local discovery](../movies/midnight-discovery.yml) searches owned Plex media for Hidden Gems and edition labels; Hidden Gems uses the connected account's watch state.

Production collections appear on library, home, and shared screens. Previews hide them from home and shared screens. The late-night lineup gets a dress rehearsal.

## Charts and download boundaries

TMDb, IMDb, and Tracearr supply viewing charts. Library operations update genres and provider ratings while preserving personal Plex ratings.

Global Radarr/Sonarr settings disable additions and searches, with these production exceptions:

| Definition | Download behavior |
| --- | --- |
| Top 10 Pirated Movies of the Week | Add and search for missing movies through Radarr |
| [Edward's favorites](../movies/edwards-favorites.yml) | Add and search for missing movies through Radarr |
| Midnight Cinema's five curated movie collections | Add missing movies, monitor selections, and search new additions through Radarr |
| Weekend Miniseries and the [series-request helper](../shows/midnight-series-requests.yml) | Add full series, monitor all regular episodes, and search new additions through Sonarr |

Midnight Cinema enables monitoring of existing Arr entries. Kometa searches new additions; already-registered missing files require an Arr search. Integrations supply quality profiles and root folders. The series-request helper requests candidate shows without creating a Plex collection.

> [!IMPORTANT]
> These production definitions can trigger downloads. Review their settings and private Radarr/Sonarr connections before running them. [Fixture previews](testing.md#choose-a-preview) contain no download-client connections.

## Personal favorites and ordered playlists

Edit [Edward's favorites](../movies/edwards-favorites.yml) to select movies, including those absent from Plex.

The [Battlestar Galactica playlist](../playlists/battlestar-galactica-timeline.yml) uses ordered TVDb episode and IMDb movie IDs. Preserve their order and title comments; missing specials and alternate edits need explicit entries. No Cylon rearranging the timeline.
