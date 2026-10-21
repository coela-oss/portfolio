<script setup lang="ts">
import { computed } from 'vue'
import type { Locale, Page } from '../types'
import { nextSteps } from '../navigation.mts'
const props = defineProps<{ page: Page; locale: Locale; local: (path: string) => string }>()
const actions = computed(() => nextSteps(props.page.path, props.locale)
  .filter(action => !props.page.sections.some(section => section.links?.some(link => link.href === action.href))))
</script>
<template>
  <aside v-if="actions.length" class="page-next-steps" :aria-label="locale === 'ja' ? '次のステップ' : 'Next steps'">
    <h2>{{ locale === 'ja' ? '関連する設計を読む' : 'Continue exploring the design' }}</h2>
    <div class="visitor-path-grid"><NuxtLink v-for="item in actions" :key="item.href" :to="local(item.href)" class="visitor-path"><span><strong>{{ item.title }}</strong><span v-if="item.summary">{{ item.summary }}</span></span><span aria-hidden="true">→</span></NuxtLink></div>
  </aside>
</template>
