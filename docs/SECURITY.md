# Security policy

Protect private services and credentials before sharing anything about a failure.

## Supported source

Security fixes target the current `main` branch. Older checkouts and third-party services are not maintained by this repository. Report vulnerabilities in Kometa itself through [Kometa's security guidance](https://github.com/Kometa-Team/Kometa/security/policy).

## Report privately

Use [GitHub's private vulnerability reporting form](https://github.com/scottgigawatt/kometa-config/security/advisories/new) for credential exposure, unsafe runtime access, or other exploitable behavior in this repository.

Include the affected commit, files, minimal reproduction, impact, and sanitized evidence. Do not open a public issue, PR, or Discord discussion with vulnerability details.

If the private form is unavailable, request a private reporting channel from the maintainer without disclosing the vulnerability. Acknowledgment and fixes are best effort; there is no guaranteed response time.

## Protect sensitive data

> [!WARNING]
> Never publish Plex tokens, API keys, OAuth data, webhook URLs, private server addresses, environment files, raw logs, or screenshots containing them. A publicly reachable Plex URL is still private.

Use placeholders or secret substitutions in tracked configuration. Keep test values in ignored `.secrets/` files and deployment credentials in private runtime settings. Review staged changes manually even when automated secret checks pass.

If a credential is exposed, revoke or rotate it first. Removing it from the latest commit does not remove Git history or copies already fetched. Coordinate any history cleanup separately.

## Scope and disclosure

This repository owns configuration, artwork mappings, helpers, and workflows—not Plex server data or the security of upstream applications. Keep dependency/runtime updates current and verify changes in isolated fixtures.

The maintainer will investigate private reports, coordinate accepted fixes, and discuss disclosure and attribution with the reporter where practical. Use [support](SUPPORT.md) for non-sensitive questions.
