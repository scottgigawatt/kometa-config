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

Use Kometa 2.5.0 or newer with PATTRMM Neo. Generated definitions and paired text lists remain ignored runtime files; edit their authored settings to change their output.

## PATTRMM Neo

[PATTRMM Neo](https://github.com/InsertDisc/pattrmm/tree/neo) generates local Plex-GUID lists consumed by Kometa's `text_file` builder. [pattrmm/settings.yml](../pattrmm/settings.yml) owns four collections: Movies by Size, This Month in Movie History, This Month in TV History, and Returning Soon. The library names must match Plex exactly.

The [Plundarr Neo service](https://github.com/scottgigawatt/plundarr/blob/main/docker/services/pattrmm/README.md) defaults to `ghcr.io/insertdisc/pattrmm:neo`. It mounts this checkout's `pattrmm/` directory read-only at `/settings`, its private cache at `/data`, and this checkout at `/config`. Set `PATTRMM_SETTINGS=settings.yml`; `PATTRMM_TIMES=02:00,14:00` runs before Kometa's `05:00,17:00` schedule. Give the configured container user write access to the cache and generated output directories.

Neo reads literal Plex URL/token and TMDb key, language, and region values from `/config/config.yml`. Keep them private. Its authored settings contain no credentials and select that file through `settings.kometa_config`.

Output belongs in `generated/pattrmm/movies/` and `generated/pattrmm/shows/`. The main Kometa configuration loads those directories. Keep each generated YAML file beside its paired `.txt` file. Returning Soon uses collection-only mode; Neo does not replace or add to the custom overlays.

From the generated Duplex directory, create the output before the first Kometa run:

```sh
docker compose run --rm --no-deps pattrmm --run
```

Confirm every settings run reports `All operations complete` with no failed-settings messages or tracebacks, then start the scheduler with `docker compose up -d pattrmm`. Allow generation to finish before Kometa reads its files. Do not point fixture settings at production libraries or commit generated output.

## Tracearr

Set the `tracearr.url` and Public API key in the deployment's `config.yml`. The URL must be reachable from the Duplex containers; `localhost` refers to the container itself. Leave `server_id` blank for automatic Plex-server selection, or supply the server's Tracearr UUID when selection is ambiguous.

Movie and TV watch-history collections use a 30-day window and up to 25 items. They retain the `Plex Popular` and `Plex Watched` names, with the additional Tracearr charts disabled.

See the [Tracearr connection reference](https://kometa.wiki/en/latest/config/tracearr/) and [Tracearr chart defaults](https://kometa.wiki/en/latest/defaults/chart/tracearr/).
