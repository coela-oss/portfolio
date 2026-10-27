# Portfolio presentation

`documents/{ja,en}/**/*.md` owns reviewed bilingual page bodies.
`site.json` registers their publication order and public site metadata. `work.en.json` and `work.ja.json`
provide case-study editorial data; `captures.json` records live screenshot evidence.
`module.ts` generates public routes, the XML sitemap and the public content JSON
from the same published page manifest. All internal links must resolve.

Add a case study with its actual capture, source/live destinations, architecture,
trade-off and verification. Update both locales and run the screenshot/hash and
route tests. Do not infer individual contribution, runtime behavior, customer
results or historical dates from the existence of a repository.

The existing presentation foundation retains Apache-2.0 in LICENSE and NOTICE.
New MIT extensions are identified in source; original prose and images follow
`../LICENSES/README.md`. Shared Nuxt generation remains in the independently
published `@nuxtjp/localized-site` package.

## Visitor journeys and case studies

The work index compares purposes before opening a case. `case-stories.json`
provides bilingual purpose/contribution/outcome summaries, four-step explanatory
flows, decision tables and three distinct product/source/reference exits. These
are explanations of existing behavior, not new runtime features or measurements.
Capture versions and dates remain the evidence of the pictured historical build;
a current-release link is a separate destination. The sem-lang implementation and
its presentation website have separate, explicitly labelled links.

`navigation.mts` supplies context-specific related reading. Case actions own their
exits; do not reintroduce a generic work/about loop below every page. OSS category
pages describe repository purposes and link to the relevant case directly.

`pnpm test`, strict types and static generation run locally within bounded units.
The owner CI runs `.github/scripts/browser-check.mts` against the actual generated
site with hosted Chrome: both languages, three widths, menu state, page overflow,
images, headings, case diagrams/tables/exits and screenshots. The script refuses
local execution; no local browser or product runtime is needed for source checks.

## Generated document outputs

`content.mjs` validates the current MDC source and parses the official MDC AST and renders Vue components,
`/raw/*.md` and `/llms.txt` from the same published selection. HTML links to
its Markdown alternate. Ignore `.generated-documents/`; edit the source MDC,
never the generated content snapshot. The removed authored `content.json` and
PageSections renderer have no compatibility fallback.
