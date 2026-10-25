# Production verification

`current-production-verification.json` records the latest actual operator check,
its reviewed source/archive, verifier dependency identities and evidence hashes.
Use that record for the current version and counts; they are not repeated here.
Public response details stay local. Reproduce the read-only check using the
owner observation commands in the repository README.

Operator public-byte/redirect verification, authenticated provider preservation
and hosted public observation are separate evidence. The hosted observer may
encounter Cloudflare HTTP 403 challenges even when the operator's exact-byte
check succeeds. A failed hosted result remains failed and does not establish
which particular defense rule caused the challenge. Do not weaken defenses or
resend a deployment in response to an observer failure.

The read-only observation job resolves the committed Node/pnpm dependency tree
without lifecycle scripts before using the public pure edge verifier. It has no
Cloudflare credentials and performs no deployment or provider configuration writes.
