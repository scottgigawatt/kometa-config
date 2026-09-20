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

#
# Exit immediately when a command fails or an unset variable is referenced.
#
set -eu

#
# Require the immutable Kometa image exported by the Makefile.
#
if [ -z "${KOMETA_IMAGE:-}" ]; then
    echo "KOMETA_IMAGE is required; run this check through 'make validate'." >&2
    exit 1
fi

#
# Fail before validation when the local Docker runtime is unavailable.
#
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required to run the official Kometa validator." >&2
    exit 1
fi

#
# Require Git to identify source files without including private runtime state.
#
if ! command -v git >/dev/null 2>&1; then
    echo "Git is required to select source-controlled Kometa YAML." >&2
    exit 1
fi

#
# Resolve the checkout and create an isolated writable Kometa runtime directory.
#
repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
runtime_directory=$(mktemp -d "${TMPDIR:-/tmp}/kometa-validation.XXXXXX")

#
# Remove disposable validation state on normal exit and interruption.
#
trap 'rm -rf "$runtime_directory"' EXIT HUP INT TERM

#
# Snapshot tracked YAML from the working tree, preserving paths and local edits.
# Null-delimited paths keep filenames intact while excluding ignored secrets,
# logs, caches, and generated test or deployment configuration.
#
source_directory="$runtime_directory/source"
mkdir -p "$source_directory"
git -C "$repository_root" ls-files -z -- '*.yml' '*.yaml' > "$runtime_directory/yaml-files"

#
# Expand snapshot variables in the child shell, not the calling shell.
#
# shellcheck disable=SC2016
xargs -0 sh -c '
    set -eu
    repository_root=$1
    source_directory=$2
    shift 2

    for source_file do
        mkdir -p "$source_directory/$(dirname "$source_file")"
        cp "$repository_root/$source_file" "$source_directory/$source_file"
    done
' sh "$repository_root" "$source_directory" < "$runtime_directory/yaml-files"

#
# Seed the local base configuration required by Kometa's entrypoint. The
# sandbox template contains placeholders instead of real credentials.
#
cp "$repository_root/tests/kometa/config.yml" "$runtime_directory/config.yml"

#
# Check every enabled custom artwork mapping against the pinned Defaults using
# Git paths, so sparse CI checkouts do not need to download the artwork itself.
#
git -C "$repository_root" ls-files -z -- overlays/ > "$runtime_directory/overlay-files"
docker run --rm \
    --network none \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$source_directory,dst=/workspace,readonly" \
    --mount "type=bind,src=$runtime_directory,dst=/config,readonly" \
    --mount "type=bind,src=$repository_root/scripts/check-overlay-assets.py,dst=/check-overlay-assets.py,readonly" \
    --entrypoint python \
    "$KOMETA_IMAGE" /check-overlay-assets.py

#
# Check native collection selection, readable ID comments, and preview isolation.
# Exercise regression tests offline with the same pinned YAML implementation.
# Give CLI tests disposable scratch space while keeping source mounts read-only.
#
docker run --rm \
    --network none \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --env PYTHONDONTWRITEBYTECODE=1 \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --mount "type=bind,src=$source_directory,dst=/workspace,readonly" \
    --mount "type=bind,src=$repository_root/scripts,dst=/scripts,readonly" \
    --mount "type=bind,src=$repository_root/tests/unit,dst=/tests,readonly" \
    --entrypoint sh \
    "$KOMETA_IMAGE" -c 'python /scripts/collection-preview.py && python -m unittest discover -s /tests -v'

#
# Validate the complete repository without privileges, secrets, network-bound
# services, or writable access to source-controlled files.
#
docker run --rm \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --user "$(id -u):$(id -g)" \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --mount "type=bind,src=$source_directory,dst=/workspace,readonly" \
    --mount "type=bind,src=$runtime_directory,dst=/config" \
    "$KOMETA_IMAGE" \
    --validate-dir /workspace
