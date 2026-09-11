#!/bin/sh

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# scan-secrets.sh: Scan the source files selected by pre-commit with Gitleaks.
#
# Purpose: Check actual file contents during commits, full local validation,
#          and sparse CI runs, even when the Git index has no staged changes.
# Usage: scripts/scan-secrets.sh <file> [file ...]
#

#
# Exit immediately when a command fails or an unset variable is referenced.
#
set -eu

#
# Use the repository policy regardless of the caller's working directory.
# Pre-commit supplies its pinned Gitleaks executable through the hook environment.
#
repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)

#
# Scan each selected text file without traversing private runtime directories.
# Redact findings and preserve a failing status if any file contains a secret
# or the scanner encounters an error.
#
status=0
for source_file do
    if ! gitleaks dir --config "$repository_root/.gitleaks.toml" \
        --redact --no-banner "$source_file"; then
        status=1
    fi
done

exit "$status"
