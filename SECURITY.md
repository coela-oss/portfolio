# Security

Do not post credentials, personal records or private reproduction material in
public Issues. Use GitHub private vulnerability reporting if enabled; otherwise
request a private reporting channel without describing the vulnerability publicly.

Dependency updates are proposed by repository-owned Dependabot. Source acceptance
validates content, screenshot provenance, types and static generation. A successful
build does not establish production authentication or authorization.

The public site has no product execution authority. Product commands, trust
registration, credentials and MCP endpoints belong to their respective owners.

## Dependency backports

Registry scans still report the upstream versions matching
[braces GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
and [node-forge GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv).
This source retains the reviewed bounded-depth and strict-signature backports in
`patches/`, their upstream attribution/hashes, and executable regression tests.
An upstream audit result is not changed to a clean result, nor are alerts globally
dismissed. Replace the backports when suitable upstream fixes can be validated.

### Current dependency paths

The 2026-10-22 review resolved the affected dependencies through Nuxt 4.6.2 and
Nitropack 2.13.4: `globby` / `fast-glob` / `micromatch` pulls in braces 3.0.3,
and `listhen` 1.10.1 pulls in node-forge 1.4.0. Both official advisories still
list no patched version; the latest official releases have the same versions.
The build tree therefore retains both reviewed patches and regression tests.
These are build/development dependencies of the generated static site, not a
server-side signing or pattern-parsing API offered by the deployed portfolio.

Do not swap incompatible packages, force a prerelease toolchain, remove required
build functionality or dismiss alerts to obtain a clean version-only audit.
Keep the 72-hour Dependabot maturity policy. Update the real dependency tree and
remove a backport only when an appropriate fixed upstream release is available.
The Node runtime floor is 24.22.1; CI installs that exact patched runtime.
