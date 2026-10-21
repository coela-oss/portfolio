<script setup lang="ts">
import type { CaseStory } from '../case-types'
import type { Locale } from '../types'
defineProps<{ story: CaseStory; locale: Locale }>()
</script>
<template>
  <div class="case-table-scroll" role="region" :aria-label="locale === 'ja' ? '設計上の選択' : 'Design decisions'" tabindex="0">
    <table class="case-table">
      <caption>{{ locale === 'ja' ? '設計の選択と、その理由' : 'Design choices and their reasons' }}</caption>
      <thead><tr><th scope="col">{{ locale === 'ja' ? '選択' : 'Choice' }}</th><th scope="col">{{ locale === 'ja' ? '理由' : 'Reason' }}</th><th scope="col">{{ locale === 'ja' ? '適用範囲' : 'Scope' }}</th></tr></thead>
      <tbody><tr v-for="row in story.decisions" :key="row.choice"><th scope="row">{{ row.choice }}</th><td>{{ row.reason }}</td><td>{{ row.scope }}</td></tr></tbody>
    </table>
  </div>
</template>
