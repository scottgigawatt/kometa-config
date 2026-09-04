#!/bin/sh

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# run-pre-commit-ci.sh: Lint files present in the text-only CI checkout.
#
# Purpose: Avoid downloading gigabytes of artwork for repository linting.
# Usage: scripts/run-pre-commit-ci.sh
#

#
# Exit immediately when a command fails or an unset variable is referenced.
#
set -eu

#
# Resolve and enter the sparse text-only checkout used by continuous integration.
#
repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)

cd "$repository_root"

#
# Pass every present file to pre-commit without downloading excluded artwork.
#
find . -path ./.git -prune -o -type f -print0 \
    | xargs -0 pre-commit run --show-diff-on-failure --files
