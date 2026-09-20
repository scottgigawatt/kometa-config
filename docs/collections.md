# Collection behavior

The source files define membership and presentation. Rules may add or remove titles as Plex or provider metadata changes; historical membership is not preserved artificially.

## Movie franchises, genres, and settings

[Franchises](../movies/franchise.yml) follow native [TMDb collection membership](https://kometa.wiki/en/latest/files/builders/tmdb/standard/collection/) and use release order. Standalone additions are not used to recreate broader fan lists.

[Genres](../movies/genre.yml) use Plex tags for Horror, War, and Western. LGBTQ+, Sports, Spy, and Stand-up Comedy combine the named TMDb keywords documented in source. Browse these alphabetically.

[Cities](../movies/cities.yml) use setting keywords, not filming locations. [Universes](../movies/universes.yml) use MCU/DC Extended Universe keywords or combine native Star Trek, Alien/Predator/AVP, and X-Men/Wolverine/Deadpool collections. Universe collections need at least three matches. The corresponding Defaults keys are excluded to prevent duplicate definitions; other universe Defaults remain separate sources.

## Ranked subgenres

All 101 themes live in [subgenre-top.yml](../movies/subgenre-top.yml). Their shared template supplies local posters, weekly schedules, hidden visibility, a 250-item collection limit, and release-order browsing.

Ninety themes use [TMDb Discover](https://kometa.wiki/en/latest/files/builders/tmdb/discover/movie/), selecting up to 1,000 candidates by rating with English as the original language. In these queries, pipe-separated keyword IDs mean OR and comma-separated genre IDs mean AND. For example, Romantic Comedy requires Romance and Comedy; Utopian excludes the dystopia keyword.

Eleven themes use native [IMDb keyword searches](https://kometa.wiki/en/latest/files/builders/imdb/search/) where TMDb tagging is sparse: Chick-flick, Epics, Experimental, Historical Event, Medical, Melodrama, Mindfuck, Psychedelic, Spaghetti Western, Splatter, and Urban Fantasy. These searches need no IMDb account and load no personal lists.

The usual rating/vote floors are 5 and 1,000, with explicit exceptions beside each definition. Regression tests protect names, posters, schedules, limits, readable IDs, and the absence of personal-list builders or external templates.

## Weekly Shuffle

The [movie shuffle](../movies/shuffle.yml) includes watched and unwatched movies. Every Monday it samples up to 250 random candidates, applies TMDb rating ≥6 and vote-count ≥250 filters, and keeps up to 25 qualifying films.

Christmas/Xmas titles and the TMDb Christmas keyword are excluded year-round. Keyword coverage depends on provider metadata. If fewer sampled films qualify, the collection stays smaller rather than relaxing the rules. The custom poster remains in use.

## People collections

[Top Actors](../movies/top-actors.yml) ranks people from Plex credits. Nicholas Galitzine, Chris Farley, and Ray Liotta have explicit collections and are excluded from dynamic actor generation before its limit is filled. Directors and writers use separate ranked groups; inspect future logs for cross-role name collisions.

## TV series and holiday episodes

[Curated TV collections](../shows/shuffle.yml) use repository-owned TMDb show IDs for Adult Animation, Saturday Morning Cartoons, Classic Sitcoms, and Modern Sitcoms. They contain whole shows, browse alphabetically, and support Plex's Shuffle action. Plex groups both Will & Grace runs under the original series ID.

[TV holidays](../shows/seasonal.yml) build episode-level collections from local title or summary matches. A matching parent show does not add all its episodes. Expressions recognize specific holiday language, not generic winter weather, parties, or turkey dinners; no air-date cutoff applies.

Metadata can omit holidays or mention them incidentally, so review actual matches. Episode collections contain no Sonarr attributes, including false ones. The preview disables scheduled deletion; production retains its configured windows.

## Seasonal movies

[Seasonal definitions](../scheduled/seasonal.yml) use TMDb keywords/Discover plus Plex genre searches for Valentine's Day and Halloween. St. Patrick's Day covers Irish settings, culture, folklore, diaspora, and the named holiday. Mother's Day covers motherhood and the holiday.

Christmas discovery has no popularity cutoff. Hallmark, Lifetime, and Rankin/Bass require matching company credits plus Christmas tagging; a channel broadcast alone does not qualify. Vintage Christmas covers primary releases through December 31, 1979, including specials. Horror Christmas also requires Horror; the broad Christmas collection retains its explicit title exclusions.

Every seasonal movie collection disables Radarr additions, searches, upgrades, and monitoring changes. Existing Radarr entries or queued downloads are not removed. The guarded preview omits only those already-false Radarr attributes because Kometa otherwise requires a Radarr connection; it rejects enabled writers.

## Charts and download boundaries

Production retains provider chart sources, including Trakt popularity charts. The move away from unreliable personal lists does not remove these charts.

Only the Top 10 Pirated Movies of the Week chart explicitly enables its collection-specific Radarr missing-item additions and searches. That chart is not loaded by collection previews. Production download behavior requires a separately approved run with private Radarr settings.

Existing-item Radarr and Sonarr monitoring remains false. Preview configurations contain no download-client connections or external list writers. See [testing](testing.md) for the supported preview scope.
