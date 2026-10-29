# Pull request

## What changed

<!-- Describe the configuration, tooling, documentation, or artwork change. -->

## Plex impact

<!-- Name affected libraries, collections, overlays, playlists, or state that there is no Plex behavior change. -->

## Validation

- [ ] `make check` (validation, generated-file policy, helper tests, and lint)
- [ ] Plex fixture-library render, when behavior or artwork changes
- [ ] Changed documentation reviewed for the reader's task: relevant, findable, understandable, and usable; links and rendered Markdown checked

<!-- Explain checks that were skipped. See docs/testing.md and docs/CONTRIBUTING.md. -->

## Safety

- [ ] No credentials, private server addresses, logs, caches, reports, or generated files are included
- [ ] External lists and local asset paths were verified when changed
- [ ] The rollback path is clear
