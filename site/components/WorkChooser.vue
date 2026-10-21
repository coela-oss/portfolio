<script setup lang="ts">
import { computed } from 'vue'
import english from '../work.en.json'
import japanese from '../work.ja.json'
import stories from '../case-stories.json'
import type { CaseStory } from '../case-types'
import type { Locale } from '../types'
const props = defineProps<{ locale: Locale; local: (path: string) => string }>()
const works = computed(() => props.locale === 'ja' ? japanese : english)
const cases = computed(() => stories[props.locale] as Record<string, CaseStory>)
</script>
<template>
  <div class="case-table-scroll" role="region" :aria-label="locale === 'ja' ? '作品を目的から選ぶ' : 'Choose a case by purpose'" tabindex="0">
    <table class="case-table work-chooser">
      <caption>{{ locale === 'ja' ? 'どの設計から読みますか？' : 'Which design would you like to explore?' }}</caption>
      <thead><tr><th scope="col">{{ locale === 'ja' ? '作品' : 'Work' }}</th><th scope="col">{{ locale === 'ja' ? '解決したいこと' : 'Purpose' }}</th><th scope="col">{{ locale === 'ja' ? '設計の焦点' : 'Design focus' }}</th></tr></thead>
      <tbody><tr v-for="work in works" :key="work.id"><th scope="row"><NuxtLink :to="local(work.path)">{{ work.title }} →</NuxtLink></th><td>{{ cases[work.id]?.purpose }}</td><td>{{ cases[work.id]?.contribution }}</td></tr></tbody>
    </table>
  </div>
</template>
