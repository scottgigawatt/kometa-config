<!--
  Copyright 2025-2026 Scott Gigawatt
  Licensed under the Apache License, Version 2.0.
  service-connections.md: Configure shared runtime files and Tracearr history.
-->

# Service connections

Keep source templates separate from live connection values. These settings describe the deployment; they are not required for the isolated [test-library configuration](test-libraries.md).

## Shared configuration

Duplex mounts the deployment checkout at `/config` for both Kometa and PATTRMM. By default, both read the checkout's root `config.yml`. `KOMETA_RUNTIME_CONFIG_PATH` in Duplex's `.env` can select another existing file; it replaces `/config/config.yml` inside both containers.

Keep the checked-in template free of credentials. Set live values in the deployment copy, and provide literal connection values when PATTRMM needs them; it does not resolve Kometa environment-secret substitutions.

Never copy that private deployment file back into a commit. Both credentials and server addresses follow the [security policy](SECURITY.md).

PATTRMM writes generated metadata, overlays, and text ID lists into the shared checkout. Those files remain ignored; edit the generator's settings to change their output. Kometa 2.5.0 requires Trakt-free generated definitions. Regenerate and inspect private output before a production run; upgrading this repository alone does not update PATTRMM or its existing files.

## PATTRMM Neo

[Neo](https://github.com/InsertDisc/pattrmm/tree/neo) is the selected Trakt-free generator. Its By Size, In History, and Extended Status cores write local Plex-GUID lists consumed by Kometa's `text_file` builder. Keep the generated YAML and its paired `.txt` file together; both are runtime state, not authored collections.

Neo uses `/settings` for named YAML settings files, `/data` for its cache, and `/config` for Kometa's configuration and generated output. Set `PATTRMM_SETTINGS` to the intended settings filename and `PATTRMM_TIMES` to the daily run times. Each settings file selects its Kometa config with `settings.kometa_config` and explicitly names the Plex libraries and enabled cores. Do not point fixture settings at production libraries.

The deployment service chart must supply these mounts and environment variables; changing only the image tag is insufficient. Keep literal private Plex/TMDb connection values in the selected runtime config, never in the repository. Neo collection settings pass through to Kometa, so review them for download-client or deletion actions before loading generated files. Preserve the complete existing custom overlay set when reviewing any additional generated status overlays.

## Tracearr

Set the `tracearr.url` and Public API key in the deployment's `config.yml`. The URL must be reachable from the Duplex containers; `localhost` refers to the container itself. Leave `server_id` blank for automatic Plex-server selection, or supply the server's Tracearr UUID when selection is ambiguous.

Movie and TV watch-history collections use a 30-day window and up to 25 items. They retain the `Plex Popular` and `Plex Watched` names, with the additional Tracearr charts disabled.

See the [Tracearr connection reference](https://kometa.wiki/en/latest/config/tracearr/) and [Tracearr chart defaults](https://kometa.wiki/en/latest/defaults/chart/tracearr/).
