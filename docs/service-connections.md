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

PATTRMM writes its generated metadata, overlays, and text ID lists into the shared checkout. Those files remain ignored; edit PATTRMM preferences to change their output. Kometa 2.5.0 requires Trakt-free generated definitions, such as those produced by PATTRMM's `traktless` build using `text_file`. Regenerate and inspect the private output before a production run; upgrading this repository alone does not update PATTRMM or its existing files.

## Tracearr

Set the `tracearr.url` and Public API key in the deployment's `config.yml`. The URL must be reachable from the Duplex containers; `localhost` refers to the container itself. Leave `server_id` blank for automatic Plex-server selection, or supply the server's Tracearr UUID when selection is ambiguous.

Movie and TV watch-history collections use a 30-day window and up to 25 items. They retain the `Plex Popular` and `Plex Watched` names, with the additional Tracearr charts disabled.

See the [Tracearr connection reference](https://kometa.wiki/en/latest/config/tracearr/) and [Tracearr chart defaults](https://kometa.wiki/en/latest/defaults/chart/tracearr/).
