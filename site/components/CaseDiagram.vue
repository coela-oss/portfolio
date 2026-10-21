<script setup lang="ts">
import type { CaseStory } from '../case-types'
defineProps<{ story: CaseStory }>()
</script>
<template>
  <section class="case-flow">
    <h2>{{ story.flowTitle }}</h2>
    <ol>
      <li v-for="(step, index) in story.flow" :key="step.title">
        <span class="flow-index" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
        <strong>{{ step.title }}</strong><p>{{ step.text }}</p>
      </li>
    </ol>
  </section>
</template>
