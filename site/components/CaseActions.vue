<script setup lang="ts">
import type { CaseStory } from '../case-types'
import type { Locale } from '../types'
defineProps<{ story: CaseStory; locale: Locale; local: (path: string) => string }>()
</script>
<template>
  <section class="case-actions">
    <h2>{{ locale === 'ja' ? '試す・実装を読む' : 'Try it or explore the implementation' }}</h2>
    <p>{{ locale === 'ja' ? '製品を使う入口と、設計を調べる入口を選べます。' : 'Choose a product entry point or a reference for exploring the design.' }}</p>
    <div class="visitor-path-grid"><a v-for="action in story.actions" :key="action.href" class="visitor-path" :href="action.href"><span><strong>{{ action.title }}</strong><span>{{ action.summary }}</span></span><span aria-hidden="true">↗</span></a></div>
    <NuxtLink :to="local('/work')" class="case-back">{{ locale === 'ja' ? '作品一覧へ戻る' : 'Back to selected work' }} →</NuxtLink>
  </section>
</template>
