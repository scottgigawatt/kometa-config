# Documentation style

Write for someone completing a task. Follow [GitHub Docs style](https://docs.github.com/en/contributing/style-guide-and-content-model/style-guide), [GitHub writing best practices](https://docs.github.com/en/contributing/writing-for-github-docs/best-practices-for-github-docs), and the governing plain-language principles in [ISO 24495-1:2023](https://www.iso.org/standard/78907.html). This policy applies to project-owned documentation, agent guidance, and issue/PR templates.

## Write for the reader

Identify the audience and task before drafting. Review each page against four required outcomes:

- **Relevant:** Give readers the information they need for their task or decision. Remove obsolete history, repeated explanations, and details already clear in linked source.
- **Findable:** Use descriptive headings and task-based navigation. Give each explanation a canonical home and link to it.
- **Understandable:** Use common words, active voice, concise sentences and coherent paragraphs. Explain necessary technical terms in context.
- **Usable:** Put prerequisites before numbered steps and state the expected result. Preserve risks, side effects, compatibility constraints, and recovery limits.

A little cinema humor is welcome; commands, risks, privacy guidance, and troubleshooting stay literal.

## Organize by purpose

Keep the README as an introduction and navigation page, with the project heading and purpose before the existing badge/community block. Preserve that block and its links. Put operating guides and community policies under `docs/`, `AGENTS.md` at the root, and issue/PR templates under `.github/`.

Preserve recognized community filenames: `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, and `CODE_OF_CONDUCT.md`. Use lowercase kebab-case for ordinary articles. Separate one-time setup, recurring procedures, and reference. Retain currently actionable migration and compatibility instructions; omit superseded history.

## Format clearly

- Use one descriptive H1 and sentence-case headings without skipped levels.
- Use numbered steps for procedures, bullets for choices, and tables for genuine comparisons.
- Keep ordinary prose paragraphs on one physical line; use editor word wrapping.
- Use descriptive relative links for repository files and specific upstream links for external behavior.
- Put blank lines around headings, lists, and fences. Give images meaningful alt text and preserve attribution.
- Put occasional emoji after descriptive headings; words must carry the meaning.
- Correct spelling; add only genuine vocabulary to `cSpell.words` in `.vscode/settings.json`.

Use language-labelled fences: `sh` for copyable commands without prompts or explanatory comments, `console` for transcripts, `text` for output, and the actual language for configuration. Explain working directory, dependencies, required values, and consequential side effects before the command.

Use native GitHub alerts sparingly for significant information; most pages need at most one or two. Reserve `<details>` for optional diagnostics, never prerequisites or safety warnings. Use task lists in issue and PR templates. Follow [GitHub's Markdown syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

## Verify before publishing

1. Check commands, paths, defaults, and behavior against source and the pinned stable runtime; label unreleased behavior.
2. Update inbound links and the [documentation index](index.md) after moves or heading changes.
3. Run spelling checks and `make check` for lint, local links, configuration, and helper tests.
4. Review rendered GitHub Markdown, including narrow layouts, images, tables, fences, and alerts.
5. Walk through the reader's task using the documented prerequisites, steps, and expected result. Assess relevance, findability, understanding, and usability; report what was checked and any limits.
6. Inspect the staged diff for credentials, private addresses, runtime output, and unrelated changes.

Lint and a task walkthrough support review; they do not establish certified ISO conformity. Local-link tests do not verify external availability. Preserve point-of-use warnings and backup/rollback limits when shortening content.
