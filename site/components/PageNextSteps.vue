<script setup lang="ts">
import { computed } from 'vue'
import type { Experience } from '../experience-types'
import type { Locale, Page, Link } from '../types'
const props = defineProps<{ experience: Experience; page: Page; locale: Locale; local: (path: string) => string }>()
const actions = computed(() => {
  const candidates: Link[] = [...props.page.sections.flatMap(section => section.links ?? []), props.experience.primary, props.experience.secondary]
  const unique = new Map(candidates.filter(link => link.href !== props.page.path && link.href !== '/').map(link => [link.href, link]))
  return [...unique.values()].slice(0, 3)
})
</script>
<template>
  <aside v-if="actions.length" class="page-next-steps" :aria-label="locale === 'ja' ? '次のステップ' : 'Next steps'">
    <h2>{{ locale === 'ja' ? 'ここから、次の一歩へ。' : 'Take the next step.' }}</h2>
    <div class="visitor-path-grid"><NuxtLink v-for="item in actions" :key="item.href" :to="local(item.href)" class="visitor-path"><span><strong>{{ item.title }}</strong><span v-if="item.summary">{{ item.summary }}</span></span><span aria-hidden="true">→</span></NuxtLink></div>
  </aside>
</template>
