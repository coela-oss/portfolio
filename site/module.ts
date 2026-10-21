import { fileURLToPath } from 'node:url'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import type { NuxtModule } from 'nuxt/schema'
import data from './content.json'
import redirects from './redirects.json'
import { validateContent } from './check.mjs'

// A site-owned scaffold: no checkout, manager service, or unreleased package required.
const sitePages: NuxtModule = (_options, nuxt) => {
  if (process.env.SITE_ID && process.env.SITE_ID !== data.siteId) return
  validateContent(data)
  const publicPages = data.locales.en.pages.filter(page => page.status !== 'draft')
  const paths = (['ja', 'en'] as const).flatMap(locale => publicPages.map(page => ({
    path: `${locale === data.defaultLocale ? '' : `/${locale}`}${page.path === '/' ? '/' : page.path}`,
    locale, source: page.path
  })))
  const file = fileURLToPath(new URL('./SitePage.vue', import.meta.url))
  nuxt.options.css.push(fileURLToPath(new URL('./site.css', import.meta.url)))
  nuxt.options.css.push(fileURLToPath(new URL('./experience.css', import.meta.url)))
  nuxt.options.css.push(fileURLToPath(new URL('./portfolio.css', import.meta.url)))
  nuxt.hook('pages:extend', pages => {
    pages.splice(0, pages.length, ...paths.map(({ path, locale, source }) => ({ name: `site-${locale}-${source.replace(/\W/g, '-')}`, path, file, meta: { layout: false } })))
  })
  nuxt.options.nitro.prerender ??= {}
  // Only reviewed published routes are crawlable; draft content is authoring-only.
  nuxt.options.nitro.prerender.routes = paths.map(item => item.path)
  nuxt.options.nitro.prerender.crawlLinks = false
  nuxt.hook('prerender:routes', context => {
    context.routes.clear()
    for (const { path } of paths) context.routes.add(path)
  })
  nuxt.hook('nitro:config', config => {
    config.prerender ??= {}
    config.prerender.routes = paths.map(item => item.path)
    config.prerender.crawlLinks = false
  })
  const directory = join(nuxt.options.buildDir, 'site-public')
  const urls = paths.map(({ path }) => `<url><loc>${data.origin}${path}</loc></url>`).join('')
  nuxt.hook('build:before', () => {
    mkdirSync(directory, { recursive: true })
    writeFileSync(join(directory, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>\n`)
    writeFileSync(join(directory, 'site-content.json'), JSON.stringify(data) + '\n')
    const rules = Object.entries(redirects).flatMap(([from, to]) => ['', '/ja'].flatMap(prefix => {
      const target = to.startsWith('/') ? prefix + to : to
      return [`${prefix}${from} ${target} 301`, `${prefix}${from}/ ${target} 301`]
    }))
    writeFileSync(join(directory, '_redirects'), rules.join('\n') + '\n')
  })
  nuxt.options.nitro.publicAssets ??= []
  nuxt.options.nitro.publicAssets.push({ dir: directory, maxAge: 0 })
  nuxt.options.routeRules ??= {}
  for (const locale of ['', `/${data.defaultLocale === 'en' ? 'ja' : 'en'}`]) {
    nuxt.options.routeRules[`${locale}/docs/security`] = { redirect: `${locale}/security` }
    if (data.siteId === 'coela') nuxt.options.routeRules[`${locale}/ai-cto`] = { redirect: `${locale}/about` }
  }
}
export default sitePages
