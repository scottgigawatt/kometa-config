#!/bin/sh

#
# Copyright 2025-2026 Scott Gigawatt
#
# Licensed under the Apache License, Version 2.0.
#
# check-generated-files.sh: Keep PATTRMM-owned Kometa inputs out of Git history.
#
# Purpose: Fail when generated PATTRMM metadata, overlays, or ID lists are tracked.
# Usage: scripts/check-generated-files.sh
#

#
# Exit immediately when a command fails or an unset variable is referenced.
#
set -eu

#
# Resolve the checkout and define every PATTRMM-generated filename family.
#
repository_root=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
generated_pattern='(^|/).+-(by-size|in-history|returning-soon-metadata|returning-soon-overlay|returning-soon-collection)\.(yml|txt)$'

#
# Find tracked generated inputs without allowing an empty match to fail early.
#
tracked_generated=$(git -C "$repository_root" ls-files | grep -E "$generated_pattern" || true)

#
# Reject generated inputs with their tracked paths available for remediation.
#
if [ -n "$tracked_generated" ]; then
    echo "PATTRMM-generated inputs must remain runtime-owned and untracked:" >&2
    echo "$tracked_generated" >&2
    exit 1
fi

#
# Confirm the repository preserves the source and runtime ownership boundary.
#
echo "PATTRMM-generated inputs are not tracked."
