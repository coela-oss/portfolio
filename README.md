# Coela — engineering portfolio

Coela takes its name from the coelacanth. This is the public source of
[coela.org](https://coela.org/): working interfaces, architecture, trade-offs and
links to implementations. English is the default; Japanese has separate routes.

Start at **Work** for four technical case studies, **Open source** for projects
by discipline, and **Notes** for implementation-grounded design writing.
The case studies include the released Zix CLI, NuxtJP, the iHAT directory and sem-lang.

## Development

Use the pinned Node 24 and pnpm versions in `package.json`.

```sh
pnpm install --frozen-lockfile
pnpm test
pnpm typecheck
pnpm build
pnpm dev
```

Only the `coela` site is registered. Drafts, credentials, author evidence and
source history from earlier repositories are not included. Data and articles
are independently maintained at [engineering](https://github.com/coela-oss/engineering).
This site consumes published references; it is not a central job runner or MCP host.

## Case studies and evidence

Edit `site/work.en.json`, `site/work.ja.json` and `site/content.json` together.
Each case contains a problem, architecture, trade-off, verification and direct
source/live exits. `site/captures.json` records actual URLs, dates, source versions
and screenshot hashes; tests reject invented paths or changed image bytes.
Images show real public Web interfaces or an explicitly labelled formatted view
of actual CLI output. `examples/zix` retains the synthetic inputs and recorded
outputs of the credential-free local CLI observation.
Never insert customer data or private application screens without permission.

## Independent release

A `site/coela/v<version>` tag must match `.github/site-release.json` and accepted
main CI. The owner workflow builds a source-bound static archive before any
Cloudflare credential is available. Production is disabled until a reviewed
production Environment and a dedicated credential have been accepted. Re-runs
verify matching deployments and cannot resend an unknown write.
No DNS, Worker, credential or permission change is implied by a source update.

Production HTML can contain Cloudflare Web Analytics and JavaScript Detections
tags added at the edge. The release contract pins the complete tag hashes.
Only JSD's hex ray ID and base64 numeric timestamp are normalized before hashing.
Verification may remove at most one of each pinned tag at the end of the body;
all remaining HTML bytes and every non-HTML asset must match the prepared archive.
Unknown scripts, modified page content, duplicate tags and upstream template
changes fail verification. Review new hashes explicitly when templates change.
The workflow saves the DNS digest and domain bindings before deployment, then
records each read-back phase so a later failure can be reconciled without writes.

For a hosted-only mismatch, dispatch `observe-site.yml` with the reviewed release
run ID and archive SHA256. It binds the owning artifact, executes no artifact
code, and reads public responses using hosted curl. Its report retains safe
response headers and bounded public HTML samples for mismatches. Cookies are
excluded. The workflow has no Cloudflare credential, production Environment,
deployment tool or publication capability; it cannot replace release acceptance.

The same owner script supports local observation with the existing GitHub login.
Set `reviewed_run_id` and `reviewed_archive_sha256` to the reviewed values:

```sh
SITE_RELEASE_RUN_ID="$reviewed_run_id" SITE_ARCHIVE_SHA256="$reviewed_archive_sha256" \
  python3 .github/scripts/site_observe.py download .local/acceptance/fresh-readback
python3 .github/scripts/site_observe.py observe .local/acceptance/fresh-readback
```

Cloudflare challenge responses are reported as `public_observation_blocked`,
retain a nonzero exit code, and are separate from content mismatches. Current
operator verification is recorded in
[`docs/operations/current-production-verification.json`](docs/operations/current-production-verification.json).
Hosted summaries label this local evidence separately and bind it to the exact
source/archive. They do not turn a blocked hosted probe into a successful check.

See [license scope](LICENSES/README.md). Original extensions use MIT; original
content uses CC BY 4.0. Existing Apache-2.0 and third-party notices are preserved.

## Updating canonical Engineering presentation

The Web 0.1.0 release owns the validated title, excerpt and provenance. Portfolio
owns navigation and page composition. Do not edit `site/guidance.json` or the
vendored reader manually, or infer a heading from a content-ID prefix.
Download the three assets from the reviewed immutable Engineering Web release,
independently admit both archive and `release.json` SHA256 values, then run:

```sh
node scripts/update-engineering.mts /path/to/verified-release ARCHIVE_SHA256 RECEIPT_SHA256
```

The command makes no network requests. It validates the bounded archive, exact
11-file closure and file hashes, regenerates rows from the complete admitted
snapshot and compares the release's rows before updating caller files. The site
verifier repeats file and row checks; hosted browser acceptance compares rendered
headings as well as excerpts, versions and source links in both locales.

Provider-state readback runs before public asset checks and retains a separate
`provider-acceptance.json`. This proves only authenticated DNS/custom-domain
preservation and disabled development URLs; `public_content_verified` stays
false in that receipt. Edge challenge failures still fail the hosted job and
never create final `acceptance.json`. Independent local public-byte and redirect
checks may supplement that provider receipt only when exact source, version and
archive hashes agree. Original pre-deployment receipts remain the comparison
baseline across any recovery; a later matching snapshot does not erase an older
unverified change. No Cloudflare defense is disabled to obtain a green job.
