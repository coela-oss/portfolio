<script setup lang="ts">
import type { Section } from '../types'
defineProps<{ sections: Section[]; local: (path: string) => string }>()
</script>
<template>
  <section v-for="(section, index) in sections" :key="section.title" class="site-section">
    <div class="site-section-heading"><span class="site-number" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span><h2>{{ section.title }}</h2></div>
    <div class="site-section-body"><p>{{ section.text }}</p><pre v-if="section.code" class="site-code"><code>{{ section.code }}</code></pre><div v-if="section.links?.length" class="site-links">
      <NuxtLink v-for="link in section.links" :key="link.href" :to="local(link.href)" class="site-link-card">
        <img v-if="link.icon" :src="link.icon" width="48" height="48" alt="" loading="lazy">
        <span><strong>{{ link.title }}</strong><span v-if="link.summary">{{ link.summary }}</span></span><span aria-hidden="true">↗</span>
      </NuxtLink>
    </div></div>
  </section>
</template>
