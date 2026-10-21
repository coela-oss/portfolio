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
