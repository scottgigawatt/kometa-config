#!/bin/sh

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# run-test-library.sh: Run the isolated Kometa Plex test-library configuration.
#
# Purpose: Render smoke collections and the complete custom overlays against the
#          tiny upstream Plex fixture libraries before production rollout.
# Usage: KOMETA_IMAGE=<image> TEST_ENV=<path> scripts/run-test-library.sh
#

#
# Exit immediately when a command fails or an unset variable is referenced.
#
set -eu

#
# Keep newly created runtime directories and copied configuration private.
#
umask 077

#
# Require the immutable Kometa image exported by the Makefile.
#
if [ -z "${KOMETA_IMAGE:-}" ]; then
    echo "KOMETA_IMAGE is required; run this check through 'make test-library'." >&2
    exit 1
fi

#
# Fail before touching Plex when the local Docker runtime is unavailable.
#
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required to run the Kometa test-library workflow." >&2
    exit 1
fi

#
# Resolve private connection settings and disposable test output locations.
#
repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
test_environment=${TEST_ENV:-"$repository_root/.secrets/test.env"}
runtime_directory=${KOMETA_TEST_RUNTIME:-"$repository_root/.kometa-test"}

#
# Interpret relative environment paths from the repository root.
#
case "$test_environment" in
    /*) ;;
    *) test_environment="$repository_root/$test_environment" ;;
esac

#
# Require the ignored private environment before starting the container.
#
if [ ! -f "$test_environment" ]; then
    echo "Missing private test environment: $test_environment" >&2
    echo "Copy example.test.env to .secrets/test.env and fill in its values." >&2
    exit 1
fi

#
# Create the ignored writable directory used for Kometa logs and cache state.
#
mkdir -p "$runtime_directory"

#
# Place the selected test configuration beside its writable runtime output.
# Kometa creates logs and cache files relative to the configuration path.
#
cp "$repository_root/tests/kometa/config.yml" "$runtime_directory/config.yml"

#
# Mount only the source inputs needed by this preview, never the secrets folder.
# Individual artwork mounts leave the parent overlay cache writable for Kometa.
#
set -- \
    --mount "type=bind,src=$repository_root/assets,dst=/workspace/assets,readonly" \
    --mount "type=bind,src=$repository_root/tests/kometa,dst=/workspace/tests/kometa,readonly"

for overlay_source in \
    chart-award-ribbons.yml corner-background.yml series-status.yml network-fallback.yml \
    background bottom-left bottom-right resolution-top-left-45deg \
    audio-top-left-45deg status-top-left streaming-top-left studio-top-left network-top-left
do
    set -- "$@" --mount "type=bind,src=$repository_root/overlays/$overlay_source,dst=/config/overlays/$overlay_source,readonly"
done

#
# Allow an existing private MDBList credential to be supplied by the caller.
# Docker reads its value from the environment, never from command arguments.
#
if [ -n "${KOMETA_MDBLISTAPIKEY:-}" ]; then
    set -- "$@" --env KOMETA_MDBLISTAPIKEY
fi

#
# Run Kometa without privileges or repository write access, while allowing its
# disposable logs and cache to persist for inspection after the test.
# Skip missing-item lookups because fixtures intentionally omit most titles.
#
docker run --rm \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --tmpfs /tmp:rw,noexec,nosuid,size=128m \
    --env-file "$test_environment" \
    --mount "type=bind,src=$runtime_directory,dst=/config" \
    "$@" \
    "$KOMETA_IMAGE" \
    --config /config/config.yml \
    --read-only-config \
    --no-missing \
    --run
