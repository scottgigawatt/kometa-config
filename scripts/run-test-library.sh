#!/bin/sh
#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# run-test-library.sh: Run the isolated Kometa Plex test-library configuration.
#
# Purpose: Render smoke collections and maintained default overlays against the
#          tiny upstream Plex fixture libraries before production rollout.
# Usage: KOMETA_IMAGE=<image> TEST_ENV=<path> scripts/run-test-library.sh
#

set -eu

if [ -z "${KOMETA_IMAGE:-}" ]; then
    echo "KOMETA_IMAGE is required; run this check through 'make test-library'." >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required to run the Kometa test-library workflow." >&2
    exit 1
fi

repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
test_environment=${TEST_ENV:-"$repository_root/.secrets/test.env"}
runtime_directory=${KOMETA_TEST_RUNTIME:-"$repository_root/.kometa-test"}

case "$test_environment" in
    /*) ;;
    *) test_environment="$repository_root/$test_environment" ;;
esac

if [ ! -f "$test_environment" ]; then
    echo "Missing private test environment: $test_environment" >&2
    echo "Copy example.test.env to .secrets/test.env and fill in its values." >&2
    exit 1
fi

mkdir -p "$runtime_directory"

docker run --rm \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --tmpfs /tmp:rw,noexec,nosuid,size=128m \
    --env-file "$test_environment" \
    --mount "type=bind,src=$repository_root,dst=/workspace,readonly" \
    --mount "type=bind,src=$runtime_directory,dst=/config" \
    "$KOMETA_IMAGE" \
    --config /workspace/tests/kometa/config.yml \
    --run
