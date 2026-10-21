# Site-owned multi-page template

This scaffold was adopted from `nuxtjp/site-builder/templates/service-site`.
It runs on the published localized-site module; no manager checkout, workspace
path dependency, credential or new registry release is required.

Edit `content.json` for reviewed pages, navigation, categories and resource links.
Both languages must contain the same unique paths. Keep navigation to five
visitor goals; place detailed pages under their parent section. Every internal
link must resolve. `module.ts` prerenders published pages and generates the XML
sitemap from that same manifest. `/sitemap` is the human-readable index.

Draft article prompts live in `content-drafts` outside this imported directory.
They have no public URL, navigation entry or bundled text. To publish an article,
add reviewed bilingual page entries with `kind: "article"`, a topic in `category`,
and `status: "published"`. Empty collections show a normal empty state. Never add
fake dates, customer names, testimonials, download links, prices or achievements.
Run the site build and local link/browser checks before merging. Site sources
are ready for a later deployment batch; merging does not create a release tag.

Each owner can change its presentation independently. Retain LICENSE/NOTICE and
asset attribution when adapting this Apache-2.0 scaffold. Brand assets retain
their existing site-specific rights. Public pages do not describe migration,
authoring placeholders or infrastructure approval procedures.
