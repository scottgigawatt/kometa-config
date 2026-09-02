#!/bin/sh
#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# validate-kometa.sh: Validate YAML with the pinned official Kometa image.
#
# Purpose: Run Kometa's schema-aware directory validator without access to
#          Plex, secrets, or writable repository content.
# Usage: KOMETA_IMAGE=<image> scripts/validate-kometa.sh
#

set -eu

if [ -z "${KOMETA_IMAGE:-}" ]; then
    echo "KOMETA_IMAGE is required; run this check through 'make validate'." >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required to run the official Kometa validator." >&2
    exit 1
fi

repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
runtime_directory=$(mktemp -d "${TMPDIR:-/tmp}/kometa-validation.XXXXXX")

trap 'rm -rf "$runtime_directory"' EXIT HUP INT TERM

# Kometa's entrypoint requires a local base config before dispatching the
# standalone directory validator; the sandbox template contains no real secrets.
cp "$repository_root/tests/kometa/config.yml" "$runtime_directory/config.yml"

docker run --rm \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --mount "type=bind,src=$repository_root,dst=/workspace,readonly" \
    --mount "type=bind,src=$runtime_directory,dst=/config" \
    "$KOMETA_IMAGE" \
    --validate-dir /workspace
