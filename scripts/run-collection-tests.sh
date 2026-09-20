#!/bin/sh

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# run-collection-tests.sh: Preview movie and TV collection builders in Plex fixtures.
#
# Purpose: Reuse production definitions without overlays, downloads, or list writes.
# Usage: KOMETA_IMAGE=<image> TEST_ENV=<path> scripts/run-collection-tests.sh [--seasonal-only]
#

#
# Fail immediately and keep runtime configuration, logs, and reports private.
#
set -eu
umask 077

#
# Require the pinned runtime and an available Docker client before preparation.
#
if [ -z "${KOMETA_IMAGE:-}" ]; then
    echo "KOMETA_IMAGE is required; run 'make test-collections'." >&2
    exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required to run collection previews." >&2
    exit 1
fi

#
# Keep collection output separate from existing overlay backups and caches.
#
repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
test_environment=${TEST_ENV:-"$repository_root/.secrets/test.env"}
runtime_directory="$repository_root/.kometa-test/collections"
case "$test_environment" in
    /*) ;;
    *) test_environment="$repository_root/$test_environment" ;;
esac
if [ ! -f "$test_environment" ]; then
    echo "Missing private test environment; configure .secrets/test.env first." >&2
    exit 1
fi

#
# Copy only the credential-free test configuration into ignored runtime state.
#
mkdir -p "$runtime_directory"
cp "$repository_root/tests/kometa/collections-config.yml" "$runtime_directory/config.yml"

#
# Mount the selected source and artwork read-only, never the repository root or
# secrets directory. The entrypoint checks isolation before connecting to Plex.
#
docker run --rm \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --tmpfs /tmp:rw,noexec,nosuid,size=128m \
    --env-file "$test_environment" \
    --mount "type=bind,src=$runtime_directory,dst=/config" \
    --mount "type=bind,src=$repository_root/assets,dst=/config/assets,readonly" \
    --mount "type=bind,src=$repository_root/movies/franchise.yml,dst=/workspace/movies/franchise.yml,readonly" \
    --mount "type=bind,src=$repository_root/movies/genre.yml,dst=/workspace/movies/genre.yml,readonly" \
    --mount "type=bind,src=$repository_root/movies/subgenre-rules.yml,dst=/workspace/movies/subgenre-rules.yml,readonly" \
    --mount "type=bind,src=$repository_root/movies/cities.yml,dst=/workspace/movies/cities.yml,readonly" \
    --mount "type=bind,src=$repository_root/movies/universes.yml,dst=/workspace/movies/universes.yml,readonly" \
    --mount "type=bind,src=$repository_root/scheduled/seasonal.yml,dst=/workspace/scheduled/seasonal.yml,readonly" \
    --mount "type=bind,src=$repository_root/shows/shuffle.yml,dst=/workspace/shows/shuffle.yml,readonly" \
    --mount "type=bind,src=$repository_root/tests/kometa,dst=/workspace/tests/kometa,readonly" \
    --mount "type=bind,src=$repository_root/scripts/collection-preview.py,dst=/collection-preview.py,readonly" \
    --entrypoint python \
    "$KOMETA_IMAGE" /collection-preview.py --run "$@"
