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

See [license scope](LICENSES/README.md). Original extensions use MIT; original
content uses CC BY 4.0. Existing Apache-2.0 and third-party notices are preserved.
