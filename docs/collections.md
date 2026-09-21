# Collection behavior

The source files define membership and presentation. Rules may add or remove titles as Plex or provider metadata changes; historical membership is not preserved artificially.

## Movie franchises, genres, and settings

[Franchises](../movies/franchises.yml) follow native [TMDb collection membership](https://kometa.wiki/en/latest/files/builders/tmdb/standard/collection/) and use release order. Standalone additions are not used to recreate broader fan lists.

[Genres](../movies/genres.yml) use Plex tags for Horror, War, and Western. LGBTQ+, Sports, Spy, and Stand-up Comedy combine the named TMDb keywords documented in source. Browse these alphabetically.

[Cities](../movies/cities.yml) use setting keywords, not filming locations. [Universes](../movies/universes.yml) use the MCU keyword or combine native Star Trek, Alien/Predator/AVP, and X-Men/Wolverine/Deadpool collections. Universe collections need at least three matches. The corresponding Defaults keys are excluded to prevent duplicate definitions. Kometa Defaults supplies the DC Extended Universe through its selected MDBList source; the separate rebooted DC Universe is excluded.

## Ranked subgenres

All 101 themes live in [top-rated-subgenres.yml](../movies/top-rated-subgenres.yml). Their shared template supplies local posters, weekly schedules, hidden visibility, a 250-item collection limit, and release-order browsing.

Ninety themes use [TMDb Discover](https://kometa.wiki/en/latest/files/builders/tmdb/discover/movie/), selecting up to 1,000 candidates by rating with English as the original language. In these queries, pipe-separated keyword IDs mean OR and comma-separated genre IDs mean AND. For example, Romantic Comedy requires Romance and Comedy; Utopian excludes the dystopia keyword.

Eleven themes use native [IMDb keyword searches](https://kometa.wiki/en/latest/files/builders/imdb/search/) where TMDb tagging is sparse: Chick-flick, Epics, Experimental, Historical Event, Medical, Melodrama, Mindfuck, Psychedelic, Spaghetti Western, Splatter, and Urban Fantasy. These searches need no IMDb account and load no personal lists.

Both provider templates share rating/vote defaults of 5 and 1,000 through a YAML anchor, with explicit exceptions beside each definition. Regression tests protect names, posters, schedules, limits, readable IDs, and the absence of personal-list builders or external templates.

## Weekly Shuffle

The [movie shuffle](../movies/weekly-shuffle.yml) includes watched and unwatched movies. Every Monday it samples up to 250 random candidates, applies TMDb rating ≥6 and vote-count ≥250 filters, and keeps up to 25 qualifying films.

Christmas/Xmas titles and the TMDb Christmas keyword are excluded year-round. Keyword coverage depends on provider metadata. If fewer sampled films qualify, the collection stays smaller rather than relaxing the rules. The custom poster remains in use.

## People collections

[People collections](../movies/actors-directors-writers.yml) rank actors, directors, and writers from Plex credits. A shared local template supplies artwork, ordering, and the Saturday schedule; each dynamic group supplies its credit role. Nicholas Galitzine and Chris Farley have explicit collections and are excluded from dynamic actor generation before its limit is filled. Ray Liotta uses only the dynamic actor definition, subject to the same credit-count and ranking thresholds as other actors. Directors and writers use separate ranked groups; inspect future logs for cross-role name collisions.

## TV series and holiday episodes

[Network collections](../shows/networks.yml) use explicit TMDb network IDs, each annotated with its current name and country when available. A network credit identifies an original broadcaster or platform, not current streaming availability. Country-specific variants remain separate IDs.

[Curated TV collections](../shows/animation-and-sitcoms.yml) use repository-owned TMDb show IDs for Adult Animation, Saturday Morning Cartoons, Classic Sitcoms, and Modern Sitcoms. They contain whole shows, browse alphabetically, and support Plex's Shuffle action. Plex groups both Will & Grace runs under the original series ID.

[TV holidays](../shows/holiday-episodes.yml) build episode-level collections from local title or summary matches. A matching parent show does not add all its episodes. Expressions recognize specific holiday language, not generic winter weather, parties, or turkey dinners; no air-date cutoff applies.

Metadata can omit holidays or mention them incidentally, so review actual matches. Episode collections contain no Sonarr attributes, including false ones. The preview disables scheduled deletion; production retains its configured windows.

## Seasonal movies

[Seasonal definitions](../scheduled/holiday-movies.yml) use TMDb keywords/Discover plus Plex genre searches for Valentine's Day and Halloween. St. Patrick's Day covers Irish settings, culture, folklore, diaspora, and the named holiday. Mother's Day covers motherhood and the holiday.

Christmas discovery has no popularity cutoff. Hallmark, Lifetime, and Rankin/Bass require matching company credits plus Christmas tagging; a channel broadcast alone does not qualify. Vintage Christmas covers primary releases through December 31, 1979, including specials. Horror Christmas also requires Horror; the broad Christmas collection retains its explicit title exclusions.

Every seasonal movie collection disables Radarr additions, searches, upgrades, and monitoring changes. Existing Radarr entries or queued downloads are not removed. The guarded preview omits only those already-false Radarr attributes because Kometa otherwise requires a Radarr connection; it rejects enabled writers.

## Award winners

[Critics Choice](../scheduled/critics-choice.yml), [Oscars](../scheduled/oscars.yml), [Golden Globes](../scheduled/golden-globes.yml), and [Primetime Emmys](../scheduled/emmy-awards.yml) use Kometa's [IMDb award builder](https://kometa.wiki/en/latest/files/builders/imdb/award/). Each keeps six ceremonies from Kometa's validated event-year index and selects winners from the named ceremony, regardless of when the film or show premiered. Nominees without a win are excluded. Years advance with upstream data, not just when the calendar changes. Future placeholders are not selected until validated.

Critics Choice also includes all-time Best Picture winners. Oscars and Golden Globes include all-time picture and directing winners without a result cap. Golden Globe picture categories cover drama, comedy, musical, and animation, including historical category names; foreign-language and television awards are not included solely for those wins. Oscar categories include historical picture names and the first ceremony's separate comedy and drama directing awards.

The movie award files run from January 1 through April 1. Emmys refresh every Monday and remain available between runs year-round, including after autumn ceremonies. Award records come from Kometa's maintained IMDb award data, not personal Trakt, Letterboxd, or TMDb lists. New ceremony results depend on upstream data updates.

## Charts and download boundaries

TMDb, IMDb, and Tracearr supply popular, trending, ranked, and local viewing charts. Personal Plex ratings are left untouched by library operations.

Among chart collections, only Top 10 Pirated Movies of the Week explicitly enables collection-specific Radarr missing-item additions and searches. That chart is not loaded by collection previews. Production download behavior requires a separately approved run with private Radarr settings.

Existing-item Radarr and Sonarr monitoring remains false. Preview configurations contain no download-client connections or external list writers. See [testing](testing.md) for the supported preview scope.

## Personal favorites and ordered playlists

[Edward's favorites](../movies/edwards-favorites.yml) is a repository-owned list of named TMDb movie IDs. Add or remove favorites in that file; its template retains explicit Radarr add-and-search overrides for missing movies. A Plex snapshot contains only movies present in Plex, so favorites absent from Plex must be supplied separately before they can be requested.

[Battlestar Galactica](../playlists/battlestar-galactica-timeline.yml) uses Kometa's inline `text` builder with ordered TVDb episode IDs and IMDb movie IDs. The list is authoritative: neither missing specials nor alternate edits are inferred automatically. Keep each title comment beside its ID and preserve intentional episode/movie ordering.
