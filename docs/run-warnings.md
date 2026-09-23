<!--
  Copyright 2025-2026 Scott Gigawatt
  Licensed under the Apache License, Version 2.0.
  run-warnings.md: Explain scoped configuration workarounds and provider limitations.
-->

# Run warnings

A completed run can still skip individual source entries or fail to send a notification. Review the error summary alongside each affected collection's result. Keep full logs private; this guide contains only sanitized findings from the September 23, 2026, 17:00 run on Kometa 2.5.0.

## Configuration workarounds

| Finding | Configuration response | Tradeoff |
| --- | --- | --- |
| Five movie lookup errors across Letterboxd charts | Pass four reviewed IDs through the Letterboxd Defaults file's `ignore_ids` template variable. | These records stay excluded from those charts until the source mappings are verified and the exclusions removed. |
| Ten HTTP 400 change-webhook failures in ranked subgenres | Set `changes_webhooks: []` in the shared `ranked_theme` template. | All ranked themes stop sending membership-change notifications; their collections, normal logs, reports, and separately configured run/error notifications remain enabled. |
| Old Letterboxd Top 250 visibility variables | Use the current `top_500` key for library, home, and shared-home visibility. | Restores the intended promotion of the current Top 500 chart. This was a silent configuration mismatch, not a counted warning. |
| Five missing optional settings | Keep the existing settings explicitly `null` in the public base config. | No behavior change; the deployment must retain these keys too. |

### Unresolved movie records

The exclusions apply only to the Letterboxd chart file, never globally or to TV libraries:

| TMDb movie ID | Affected collections in the reviewed run |
| --- | --- |
| 712168 | Top 250 Black-Directed |
| 753972 | Top 250 Black-Directed |
| 1016041 | 1,001 To See Before You Die; Top 250 Black-Directed |
| 1567451 | One Million Watched Club |

The log establishes failed lookups, not permanent deletion or the correct replacement title. No replacement IDs have been guessed. These are explicit exclusions, not repaired provider records. Check the originating list and its current TMDb movie mapping before removing an exclusion; valid replacement IDs can enter normally. Kometa's cached Letterboxd mappings may also need time to expire after a provider correction. Do not delete the entire cache as a routine workaround.

### Large change notifications

All ten webhook errors occurred after ranked-theme membership changes. For example, Fairytales removed 216 items. Kometa 2.5.0's Discord formatter puts the entire additions/removals list into individual embed fields without splitting it. Discord limits each field value to 1,024 characters and all embed text to 6,000 characters. The large changes and `{'embeds': ['0']}` response are consistent with exceeding those limits; the log does not contain the rejected payload to verify its exact size.

The scoped override prevents those per-theme payloads. It does not repair Kometa's formatter, alter collection membership, or disable notifications for other collections. See the [Discord embed limits](https://docs.discord.com/developers/resources/message#embed-limits) and [Kometa definition settings](https://kometa.wiki/en/latest/files/settings/).

### Missing settings in a private deployment

`settings.default_collection_order`, `settings.auto_sort_hubs`, `settings.playlist_exclude_users`, `settings.custom_repo`, and `plex.verify_ssl` were already present as blank YAML values in repository source. Kometa accepts those explicit nulls without the “not found” warning. The reviewed run therefore used a configuration missing these keys; rewriting null syntax in Git alone cannot update that private file.

When deploying, retain the five explicit null keys from [config.yml](../config.yml), preserving all private connection values. Null preserves the default collection ordering, hub ordering, user exclusions, repository selection, and Plex SSL inheritance; global `settings.verify_ssl: true` remains enabled. Verify the active config mount using the [shared configuration guidance](service-connections.md#shared-configuration). This PR does not modify the live configuration.

## Warnings that remain

### Letterboxd television entries

The 11 warnings and 11 matching errors represent ten distinct TV entries across four movie charts:

| Chart | Entries rejected as TV |
| --- | --- |
| Sight & Sound Greatest Films | Histoire(s) du cinéma; Twin Peaks: The Return |
| 1,001 To See Before You Die | Dekalog; The Sorrow and the Pity |
| Roger Ebert's Great Movies | Dekalog |
| One Million Watched Club | Chernobyl; Loki; Adolescence; WandaVision; The Queen's Gambit; Squid Game |

This describes the links returned by Letterboxd, not an independent judgment of each work's correct classification. Kometa rejects the TV link inside its Letterboxd parser, before collection filters or `ignore_ids` apply. `run_definition: movie` controls the library that runs a definition; it cannot change the media inside an external list. TV and movie IDs use separate namespaces, so copying a TV ID into `tmdb_movie` would risk selecting an unrelated film.

The pinned parser has no per-entry TV exclusion setting. It also does not support a filtered list URL as a reliable workaround: its list parser accepts only the username/list slug and limited detail/sort suffixes. Preserving these maintained lists therefore leaves the warning/error pairs visible. Removing the lists, freezing their movie membership into local snapshots, or replacing their sources would be a separate membership change. The remaining valid movies still build normally.

### Other missing provider mappings

| Summary | Meaning and action |
| --- | --- |
| 146 IMDb-to-TMDb conversions failed | Source titles lack a usable mapping. The run continued with resolvable entries. Correct known provider mappings when independently verified; do not invent IDs or globally hide conversion warnings. |
| 7,525 TMDb-to-TVDb conversions failed | 7,484 originated in the TMDb network collections, which enumerate broad broadcaster catalogs before matching local shows. Missing cross-provider mappings can omit titles; they are not evidence of broken network IDs. |
| Two remaining movie lookup errors for TMDb 1756073 | Star Wars Saga and Star Wars (Timeline Order) received this mapping through IMDb sources. No verified replacement or originating IMDb ID was available from the log. A TMDb `ignore_ids` override does not stop this pinned runtime's IMDb-to-movie missing-item path, so no ineffective exclusion is added. |
| Two TVDb HTTP 202 / empty-response warnings | TVDb did not return usable pages for series 374725 and 422241. Kometa opened its circuit breaker after retries, limiting further requests. Retry on a later run; this is not proof that either series was deleted. |
| One missing IMDb episode | `tt37231094` resolved to Star Trek: Strange New Worlds, season 4 episode 10, but no matching local episode was found. Leave it eligible for the timeline if it becomes available and correctly matched. |

Replacing TMDb network IDs with Plex network-name searches could reduce remote lookups, but it would change membership to Plex's available network metadata. The current explicit network groups and missing-item reports remain intact. Provider mapping failures can make collections incomplete, so review a specific title if it appears to be missing unexpectedly.

### Empty collections and skipped definitions

The 15 “No items found” warnings belong to Law & Order, Archie Comics, CSI, Stargate, RuPaul's Drag Race, The Twilight Zone, The Real Housewives, 9-1-1, FBI, Spartacus, Reacher, Bosch, Inspector Morse, Father Brown (2013), and Death in Paradise (2011). Their source definitions ran but found no eligible local items. Keep the definitions so they can populate when matching shows are available; verify Plex matching if a title is already present.

“Minimum not met,” “Skipped Run Definition,” and schedules outside the current run window are separate, expected outcomes. Do not lower collection minimums, download missing media, or remove schedules simply to produce an empty error summary.

## Validate and deploy

Run `make check` for the pinned runtime regression tests, schemas, lint, and secret scans. The regression tests exercise the actual Defaults template expansion, missing-movie exclusion path, and notification override without contacting external services. They cannot prove provider availability or a clean future production run.

Deploy the reviewed commit separately, preserving the private configuration and connection values. Review the next affected run for the four ID exclusions, retained notification channels, current Top 500 visibility, and remaining provider warnings. Do not publish the raw log or treat a successful process exit as proof that every collection succeeded.
