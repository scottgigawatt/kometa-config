# Documentation style

Write for someone trying to complete a task. A little cinema humor is welcome; commands, risks, privacy guidance, and troubleshooting stay literal.

## Organize by purpose

Keep the root README as an introduction and navigation page. Put operating guides and community policies under `docs/`; keep `AGENTS.md` at the root for discovery and issue/PR templates under `.github/`.

Preserve GitHub's recognized community filenames: `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, and `CODE_OF_CONDUCT.md`. Use lowercase kebab-case for ordinary articles.

Separate one-time setup, repeatable procedures, and detailed reference material. Link to the canonical explanation instead of repeating it. Describe the current supported setup. Omit migration history, superseded paths, and comparisons with past behavior.

## Write and format clearly

- Use one descriptive H1 per page and sentence-case headings without skipped levels.
- Put the outcome first, prerequisites before steps, and optional details afterward.
- Use numbered steps for procedures and bullets for choices; use tables only for useful comparisons.
- Write ordinary prose paragraphs on one physical line and let the editor wrap visually.
- Use descriptive relative links for repository files and specific upstream links for external behavior.
- Put blank lines around headings, lists, and code fences.
- Give meaningful alt text to images. Use occasional emoji after descriptive headings; words must carry the meaning.
- Keep movie and TV references brief and relevant. Leave commands, warnings, and security policies literal.
- Correct misspellings and add genuine project terms to `cSpell.words` in `.vscode/settings.json`; never allowlist a typo.

Keep copyable commands in `sh` fences without prompt characters or explanatory comments. Use `console` for transcripts, `text` for non-executable output, and the appropriate language for configuration snippets. Put explanations outside the fence.

## Use GitHub features sparingly

Use native `[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, or `[!CAUTION]` alerts for information readers must notice. Most pages need no more than one or two. Keep alerts separate and concise; do not turn ordinary steps into callouts.

Use task lists in issue and PR templates. Reserve `<details>` for optional diagnostics, never prerequisites or safety warnings. Prefer ordinary Markdown and a small set of useful status badges tied to real workflows. Put the project name and purpose before badges or community links.

## Verify before publishing

1. Check commands, paths, defaults, and behavior against current source.
2. Update inbound links and the [documentation index](index.md) when moving a page.
3. Run `make check` for lint, local-link checks, and Make behavior tests.
4. Review rendered GitHub Markdown, including headings, tables, code blocks, and alerts.
5. Inspect the staged diff for private addresses, credentials, runtime output, and unrelated changes.

Markdown linting does not establish technical accuracy. Local-link tests do not verify external website availability.

## Source guidance

- [GitHub writing and formatting](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
- [GitHub community files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [GitHub issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
