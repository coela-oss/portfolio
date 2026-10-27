<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useSeoMeta, useHead, createError } from '#imports'
import data from './content.json'
import experiences from './experience.json'
import type { Experience } from './experience-types'
import VisitorPaths from './components/VisitorPaths.vue'
import PageNextSteps from './components/PageNextSteps.vue'
import type { SiteContent, Locale } from './types'
import SiteHeader from './components/SiteHeader.vue'
import PageSections from './components/PageSections.vue'
import EngineeringGuidance from './components/EngineeringGuidance.vue'
import WorkGallery from './components/WorkGallery.vue'
import CaseStudy from './components/CaseStudy.vue'
import CaseActions from './components/CaseActions.vue'
import WorkChooser from './components/WorkChooser.vue'
import stories from './case-stories.json'
import type { CaseStory } from './case-types'
const route = useRoute()
const locale = computed<Locale>(() => /^\/(ja|en)(\/|$)/.exec(route.path)?.[1] as Locale || data.defaultLocale as Locale)
const path = computed(() => route.path.replace(/^\/(ja|en)(?=\/|$)/, '').replace(/\/$/, '') || '/')
const experience = computed(() => experiences[locale.value] as Experience)
const content = computed(() => data.locales[locale.value] as SiteContent)
const local = (value: string, language = locale.value) => /^https:\/\//.test(value) ? value : `${language === data.defaultLocale ? '' : `/${language}`}${value === '/' ? '/' : value}`
const page = computed(() => content.value.pages.find(item => item.path === path.value && item.status !== 'draft'))
const caseStory = computed(() => path.value.startsWith('/work/') ? (stories[locale.value] as Record<string, CaseStory>)[path.value.slice(6)] : undefined)
const parent = computed(() => {
  const parentPath = path.value.slice(0, path.value.lastIndexOf('/'))
  return parentPath ? content.value.pages.find(item => item.path === parentPath && item.status !== 'draft') : undefined
})
if (!page.value) throw createError({ statusCode: 404, statusMessage: 'Page not found' })
const alternate = computed(() => local(path.value, locale.value === 'ja' ? 'en' : 'ja'))
const articles = computed(() => content.value.pages.filter(item => item.kind === 'article' && item.status === 'published'))
const title = computed(() => `${page.value?.title.replace(/\n/g, ' ')} | ${content.value.brand}`)
useSeoMeta({ title, description: () => page.value?.summary, ogTitle: title, ogDescription: () => page.value?.summary, ogImage: () => `${data.origin}${content.value.icon}` })
useHead(() => ({ htmlAttrs: { lang: locale.value }, link: [
  { rel: 'canonical', href: `${data.origin}${local(path.value)}` },
  ...(['ja', 'en'] as const).map(lang => ({ rel: 'alternate' as const, type: 'text/html', hreflang: lang, href: `${data.origin}${local(path.value, lang)}` })),
  { rel: 'alternate', type: 'text/html', hreflang: 'x-default', href: `${data.origin}${local(path.value, data.defaultLocale as Locale)}` }
] }))
</script>
<template>
  <div v-if="page" class="service-site" :data-brand="data.siteId" :data-page-kind="page.kind" :style="{ '--site-accent': content.accent }">
    <SiteHeader :content="content" :path="path" :local="local" :alternate="alternate" :primary="experience.primary" />
    <main id="content">
      <div v-if="path !== '/'" class="site-breadcrumb"><NuxtLink :to="local('/')">{{ locale === 'ja' ? 'ホーム' : 'Home' }}</NuxtLink><span aria-hidden="true">/</span><template v-if="parent"><NuxtLink :to="local(parent.path)">{{ parent.label || parent.title }}</NuxtLink><span aria-hidden="true">/</span></template><span aria-current="page">{{ page.label || page.title }}</span></div>
      <section class="site-hero" :class="{ 'site-hero-home': page.kind === 'home' }">
        <div><p v-if="page.kind === 'home'" class="site-eyebrow">{{ experience.category }}</p><h1>{{ page.title }}</h1><p class="site-lead">{{ page.summary }}</p>
          <div v-if="page.kind === 'home'" class="site-actions"><NuxtLink :to="local(experience.primary.href)" class="site-button">{{ experience.primary.title }} <span aria-hidden="true">↗</span></NuxtLink><NuxtLink :to="local(experience.secondary.href)">{{ experience.secondary.title }} →</NuxtLink></div>
        </div>
        <div v-if="page.kind === 'home'" class="portfolio-signature"><img :src="content.icon" width="240" height="240" alt="Coela"><p>Software · Interfaces · Systems</p></div>
      </section>
      <div class="site-body" :class="{ 'site-body-privacy': path === '/privacy' }">
        <VisitorPaths v-if="page.kind === 'home'" :experience="experience" :local="local" />
        <WorkChooser v-if="path === '/work'" :locale="locale" :local="local" />
        <WorkGallery v-if="page.kind === 'home' || path === '/work'" :locale="locale" :local="local" />
        <CaseStudy :path="path" :locale="locale" />
        <EngineeringGuidance v-if="path === '/about/principles'" :locale="locale" />
        <PageSections :sections="page.sections" :local="local" />
        <NuxtContactForm v-if="path === '/contact'" :key="locale" :locale="locale" heading-tag="h2" privacy-url="https://hat-tech.co.jp/privacy" :texts="{ heading: locale === 'ja' ? 'お問い合わせフォーム' : 'Contact form' }" />
        <CaseActions v-if="caseStory" :story="caseStory" :locale="locale" :local="local" />
        <section v-if="page.kind === 'journal'" class="site-journal">
          <NuxtLink v-for="article in articles" :key="article.path" :to="local(article.path)" class="site-story"><span>{{ article.category }}</span><h2>{{ article.title }}</h2><p>{{ article.summary }}</p></NuxtLink>
          <p v-if="!articles.length" class="site-empty">{{ locale === 'ja' ? '新しい記事をお届けします。テーマごとのガイドもご覧ください。' : 'New stories are on the way. Explore the topic guides in the meantime.' }}</p>
        </section>
        <section v-if="path === '/sitemap'" class="site-map"><ul><li v-for="entry in content.pages.filter(item => item.status !== 'draft' && item.path !== path)" :key="entry.path"><NuxtLink :to="local(entry.path)">{{ entry.label || entry.title.replace(/\n/g, ' ') }}</NuxtLink></li></ul></section>
        <PageNextSteps v-if="!caseStory && page.kind !== 'home' && !['/privacy', '/security', '/sitemap'].includes(path)" :page="page" :locale="locale" :local="local" />
      </div>
    </main>
    <footer class="site-footer"><div><strong>{{ content.brand }}</strong><p>{{ content.caption }}</p></div><nav :aria-label="locale === 'ja' ? 'フッター' : 'Footer'"><NuxtLink v-for="item in content.navigation" :key="item.href" :to="local(item.href)">{{ item.title }}</NuxtLink><NuxtLink v-if="content.pages.some(item => item.path === '/contact')" :to="local('/contact')">{{ locale === 'ja' ? 'お問い合わせ' : 'Contact' }}</NuxtLink><NuxtLink :to="local('/privacy')">{{ locale === 'ja' ? 'プライバシー' : 'Privacy' }}</NuxtLink><NuxtLink :to="local('/security')">{{ locale === 'ja' ? 'セキュリティ' : 'Security' }}</NuxtLink><NuxtLink :to="local('/sitemap')">{{ locale === 'ja' ? 'サイトマップ' : 'Sitemap' }}</NuxtLink></nav></footer>
  </div>
</template>

<style scoped>
.site-body-privacy { min-width: 0; overflow-wrap: anywhere; }
</style>
