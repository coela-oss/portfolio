# Portfolio presentation

`content.json` owns reviewed bilingual routes. `work.en.json` and `work.ja.json`
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
