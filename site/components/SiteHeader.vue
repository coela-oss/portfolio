<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from '#imports'
import type { SiteContent, Link } from '../types'
defineProps<{ content: SiteContent; path: string; local: (path: string) => string; alternate: string; primary: Link }>()
const route = useRoute()
const open = ref(false)
const trigger = ref<HTMLButtonElement | null>(null)
function closeMenu() { open.value = false; trigger.value?.focus() }
watch(() => route.path, () => { open.value = false })
</script>
<template>
  <a class="site-skip" href="#content">{{ content.locale === 'ja' ? '本文へ' : 'Skip to content' }}</a>
  <header class="site-header" @keydown.esc="closeMenu">
    <NuxtLink :to="local('/')" class="site-wordmark"><img :src="content.icon" width="40" height="40" alt=""><span>{{ content.brand }}<small v-if="content.caption">{{ content.caption }}</small></span></NuxtLink>
    <button ref="trigger" class="site-menu" :aria-expanded="open" aria-controls="site-navigation" @click="open = !open">{{ content.locale === 'ja' ? 'メニュー' : 'Menu' }}</button>
    <nav id="site-navigation" :class="{ open }" :aria-label="content.locale === 'ja' ? '主要メニュー' : 'Main navigation'">
      <NuxtLink v-for="item in content.navigation.filter(item => item.href !== primary.href)" :key="item.href" :to="local(item.href)" :data-active="path === item.href || path.startsWith(item.href + '/')" :aria-current="path === item.href ? 'page' : undefined">{{ item.title }}</NuxtLink>
      <NuxtLink :to="local(primary.href)" class="header-cta" :aria-current="path === primary.href ? 'page' : undefined">{{ primary.title }}</NuxtLink>
      <NuxtLink :to="alternate" :lang="content.locale === 'ja' ? 'en' : 'ja'" class="site-language">{{ content.locale === 'ja' ? 'EN' : '日本語' }}</NuxtLink>
    </nav>
  </header>
</template>
