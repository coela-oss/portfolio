<script setup lang="ts">
import data from './.generated-documents/content.json'
import documents from './.generated-documents/components.mjs'
import experiences from './experience.json'
import type { ServiceSiteData, ServiceExperiences } from '@nuxtjp/localized-site/service-site'
import PortfolioBrand from './components/PortfolioBrand.vue'
import EngineeringGuidance from './components/EngineeringGuidance.vue'
import WorkGallery from './components/WorkGallery.vue'
import CaseStudy from './components/CaseStudy.vue'
import CaseActions from './components/CaseActions.vue'
import WorkChooser from './components/WorkChooser.vue'
import PageNextSteps from './components/PageNextSteps.vue'
import stories from './case-stories.json'
import type { CaseStory } from './case-types'
const siteData = data as ServiceSiteData
const siteExperiences = experiences as ServiceExperiences
const storyFor = (path: string, locale: 'ja' | 'en') => path.startsWith('/work/') ? (stories[locale] as Record<string, CaseStory>)[path.slice(6)] : undefined
</script>
<template>
  <NuxtJpServiceSite :data="siteData" :documents="documents" :experiences="siteExperiences" appearance="portfolio" :downloads="false">
    <template #hero-art="{ content }"><PortfolioBrand :icon="content.icon" /></template>
    <template #before-document="{ path, locale, page, local }">
      <WorkChooser v-if="path === '/work'" :locale="locale" :local="local" />
      <WorkGallery v-if="page.kind === 'home' || path === '/work'" :locale="locale" :local="local" />
      <CaseStudy :path="path" :locale="locale" />
      <EngineeringGuidance v-if="path === '/about/principles'" :locale="locale" />
    </template>
    <template #next-steps="{ path, locale, page, local }">
      <PageNextSteps v-if="!storyFor(path, locale) && page.kind !== 'home' && !['/privacy', '/security', '/sitemap'].includes(path)" :page="page" :locale="locale" :local="local" />
    </template>
    <template #after-document="{ path, locale, local }">
      <NuxtContactForm v-if="path === '/contact'" :key="locale" :locale="locale" heading-tag="h2" privacy-url="https://hat-tech.co.jp/privacy" :texts="{ heading: locale === 'ja' ? 'お問い合わせフォーム' : 'Contact form' }" />
      <CaseActions v-if="storyFor(path, locale)" :story="storyFor(path, locale)!" :locale="locale" :local="local" />
    </template>
  </NuxtJpServiceSite>
</template>
