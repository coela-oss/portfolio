<script setup lang="ts">
// SPDX-License-Identifier: MIT
import { computed } from 'vue'
import english from '../work.en.json'
import japanese from '../work.ja.json'
import type { Locale } from '../types'
import type { Work } from '../work-types'
const props = defineProps<{ locale: Locale; local: (path: string) => string }>()
const works = computed<Work[]>(() => props.locale === 'ja' ? japanese : english)
</script>
<template>
  <section class="portfolio-work" :aria-label="locale === 'ja' ? 'ケーススタディ' : 'Case studies'">
    <div class="portfolio-heading"><span>{{ locale === 'ja' ? '選んだ作品' : 'Selected work' }}</span><p>{{ locale === 'ja' ? '画面から、設計の奥へ。' : 'From the interface to the system behind it.' }}</p></div>
    <NuxtLink v-for="work in works" :key="work.id" :to="local(work.path)" class="work-card">
      <div class="work-image"><img :src="work.image" :alt="work.alt" width="1440" height="1100" loading="lazy" decoding="async"></div>
      <div class="work-description"><p class="work-category">{{ work.category }}</p><h2>{{ work.title }} <span aria-hidden="true">↗</span></h2><p>{{ work.summary }}</p><ul class="work-stack"><li v-for="item in work.stack" :key="item">{{ item }}</li></ul><span class="work-read">{{ locale === 'ja' ? '設計を読む' : 'Read the case study' }} →</span></div>
    </NuxtLink>
  </section>
</template>
