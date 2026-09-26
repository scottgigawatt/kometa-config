# Collection behavior 🍿

The linked source files define membership, order, schedules, and artwork. Rule-based collections respond to Plex and provider metadata; curated collections use the IDs recorded in source.

## Movie franchises, genres, and settings

[Franchises](../movies/franchises.yml) follow native [TMDb collection membership](https://kometa.wiki/en/latest/files/builders/tmdb/standard/collection/) and use release order.

[Genres](../movies/genres.yml) use Plex tags for Horror, War, and Western. LGBTQ+, Sports, Spy, and Stand-up Comedy combine the named TMDb keywords documented in source. Browse these alphabetically.

[Cities](../movies/cities.yml) use setting keywords, not filming locations. [Universes](../movies/universes.yml) use the MCU keyword or combine native Star Trek, Alien/Predator/AVP, and X-Men/Wolverine/Deadpool collections. Universe collections need at least three matches. The corresponding Defaults keys are excluded to prevent duplicate definitions. Kometa Defaults supplies the DC Extended Universe through its selected MDBList source; the separate rebooted DC Universe is excluded.

## Ranked subgenres

All 101 themes live in [top-rated-subgenres.yml](../movies/top-rated-subgenres.yml). Their shared template supplies local posters, weekly schedules, hidden visibility, a 250-item collection limit, and release-order browsing.

Ninety themes use [TMDb Discover](https://kometa.wiki/en/latest/files/builders/tmdb/discover/movie/), selecting up to 1,000 candidates by rating with English as the original language. In these queries, pipe-separated keyword IDs mean OR and comma-separated genre IDs mean AND. For example, Romantic Comedy requires Romance and Comedy; Utopian excludes the dystopia keyword.

Eleven themes use native [IMDb keyword searches](https://kometa.wiki/en/latest/files/builders/imdb/search/) where TMDb tagging is sparse: Chick-flick, Epics, Experimental, Historical Event, Medical, Melodrama, Mindfuck, Psychedelic, Spaghetti Western, Splatter, and Urban Fantasy. These searches need no IMDb account and load no personal lists.

Both provider templates require a rating of at least 5 and 1,000 votes by default, with exceptions beside each definition.

## Weekly Shuffle

The [movie shuffle](../movies/weekly-shuffle.yml) includes watched and unwatched movies. Every Monday it samples up to 250 random candidates, applies TMDb rating ≥6 and vote-count ≥250 filters, and keeps up to 25 qualifying films.

Christmas/Xmas titles and the TMDb Christmas keyword are excluded year-round. Keyword coverage depends on provider metadata. Fewer qualifying films produce a smaller collection. Even the shuffle has a casting director.

## People collections

[People collections](../movies/actors-directors-writers.yml) rank actors, directors, and writers from Plex credits. A shared local template supplies artwork, ordering, and the Saturday schedule; each dynamic group supplies its credit role. Nicholas Galitzine and Chris Farley have explicit collections and are excluded from dynamic actor generation before its limit is filled. Directors and writers have separate ranked groups. Check the run log for cross-role name collisions.

## TV series and holiday episodes

[Network collections](../shows/networks.yml) use explicit TMDb network IDs, each annotated with its current name and country when available. A network credit identifies an original broadcaster or platform, not current streaming availability. Country-specific variants remain separate IDs.

[Curated TV collections](../shows/animation-and-sitcoms.yml) use repository-owned TMDb show IDs for Adult Animation, Saturday Morning Cartoons, Classic Sitcoms, and Modern Sitcoms. They contain whole shows, browse alphabetically, and support Plex's Shuffle action. Plex groups both Will & Grace runs under the original series ID.

[TV holidays](../shows/holiday-episodes.yml) build episode-level collections from local title or summary matches. A matching parent show does not add all its episodes. Expressions recognize specific holiday language, not generic winter weather, parties, or turkey dinners; no air-date cutoff applies.

Metadata can omit holidays or mention them incidentally, so review actual matches. Episode collections contain no Sonarr attributes, including false ones. Production uses the configured holiday windows; previews disable scheduled deletion.

## Seasonal movies

[Seasonal definitions](../scheduled/holiday-movies.yml) use TMDb keywords/Discover plus Plex genre searches for Valentine's Day and Halloween. St. Patrick's Day covers Irish settings, culture, folklore, diaspora, and the named holiday. Mother's Day covers motherhood and the holiday.

Christmas discovery has no popularity cutoff. Hallmark, Lifetime, and Rankin/Bass require matching company credits plus Christmas tagging; a channel broadcast alone does not qualify. Vintage Christmas covers primary releases through December 31, 1979, including specials. Horror Christmas also requires Horror; the broad Christmas collection uses the title exclusions listed in source.

Seasonal movie collections disable Radarr additions, searches, upgrades, and monitoring changes. They leave existing Radarr entries and queued downloads alone.

## Award winners

[Critics Choice](../scheduled/critics-choice.yml), [Oscars](../scheduled/oscars.yml), [Golden Globes](../scheduled/golden-globes.yml), and [Primetime Emmys](../scheduled/emmy-awards.yml) use Kometa's [IMDb award builder](https://kometa.wiki/en/latest/files/builders/imdb/award/). Each keeps six ceremonies from Kometa's validated event-year index and selects winners from the named ceremony, regardless of when the film or show premiered. Nominees without a win are excluded. Years advance with upstream data, not just when the calendar changes. Future placeholders are not selected until validated.

Critics Choice also includes all-time Best Picture winners. Oscars and Golden Globes include all-time picture and directing winners without a result cap. Golden Globe picture categories cover drama, comedy, musical, and animation, including historical category names; foreign-language and television awards are not included solely for those wins. Oscar categories include historical picture names and the first ceremony's separate comedy and drama directing awards.

The movie award files run from January 1 through April 1. Emmys refresh every Monday and remain available between runs year-round, including after autumn ceremonies. Award records come from Kometa's maintained IMDb award data. New ceremony results depend on upstream data updates.

## Midnight Cinema 🌙

[Curated movies](../movies/midnight-curated.yml) cover first features, queer cult cinema, visual spectacle, filmmaking, and lasting impressions. [TV selections](../shows/midnight-cinema.yml) include Weekend Miniseries, TV's Greatest Episodes, and ordered Star Trek and X-Files story arcs. Edit the recorded IDs and searches to change membership; source links provide curation context.

[Local discovery](../movies/midnight-discovery.yml) finds Hidden Gems using the connected Plex account's watch state and the source's age, rating, and vote thresholds. Director's Cuts & Extended Editions matches edition labels on owned copies. Both search only media in Plex.

These collections appear on library, home, and shared screens in production, using [local posters](../assets/posters/midnight-cinema/). Previews hide them from home and shared screens. The late-night lineup gets its own dress rehearsal.

## Charts and download boundaries

TMDb, IMDb, and Tracearr supply popular, trending, ranked, and local viewing charts. Library operations update genres and provider ratings while leaving personal Plex ratings untouched.

Global Radarr and Sonarr settings disable additions and searches. The following definitions explicitly request media in production:

| Definition | Download behavior |
| --- | --- |
| Top 10 Pirated Movies of the Week | Add and search for missing movies through Radarr |
| [Edward's favorites](../movies/edwards-favorites.yml) | Add and search for missing movies through Radarr |
| Midnight Cinema's five curated movie collections | Add missing movies, monitor selections, and search new additions through Radarr |
| Weekend Miniseries and the [series-request helper](../shows/midnight-series-requests.yml) | Add full series, monitor all regular episodes, and search new additions through Sonarr |

Midnight Cinema enables monitoring of existing Arr entries. Kometa searches new additions; missing files already registered in Arr require a search there. Quality profiles and root folders come from the configured integrations. The series-request helper covers the twenty candidate shows for Greatest Episodes and both story arcs without creating a Plex collection.

> [!IMPORTANT]
> Production runs of these definitions can trigger downloads. Review their settings and private Radarr/Sonarr connections before running them. Fixture previews contain no download-client connections; see [testing](testing.md#choose-a-preview).

## Personal favorites and ordered playlists

[Edward's favorites](../movies/edwards-favorites.yml) uses named TMDb movie IDs. Edit that file to add or remove selections, including movies absent from Plex.

[Battlestar Galactica](../playlists/battlestar-galactica-timeline.yml) uses Kometa's inline `text` builder with ordered TVDb episode IDs and IMDb movie IDs. Keep each title comment beside its ID and preserve the intended episode/movie order. Missing specials and alternate edits require explicit entries. The timeline is complicated enough without a Cylon rearranging it.
