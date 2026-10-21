<script setup lang="ts">
import type { Experience } from '../experience-types'
defineProps<{ experience: Experience; local: (path: string) => string }>()
</script>
<template>
  <section class="visitor-paths" aria-labelledby="visitor-paths-title">
    <h2 id="visitor-paths-title">{{ experience.pathsTitle }}</h2>
    <div class="visitor-path-grid">
      <NuxtLink v-for="item in experience.paths" :key="item.href" :to="local(item.href)" class="visitor-path">
        <span><strong>{{ item.title }}</strong><span>{{ item.summary }}</span></span><span aria-hidden="true">↗</span>
      </NuxtLink>
    </div>
  </section>
</template>
