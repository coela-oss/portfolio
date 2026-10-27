<script setup lang="ts">
// SPDX-License-Identifier: MIT
import { computed } from 'vue'
import english from '../work.en.json'
import japanese from '../work.ja.json'
import captures from '../captures.json'
import stories from '../case-stories.json'
import type { CaseStory } from '../case-types'
import CaseDiagram from './CaseDiagram.vue'
import CaseDecisions from './CaseDecisions.vue'
import type { Locale } from '../types'
import type { Work } from '../work-types'
const props = defineProps<{ path: string; locale: Locale }>()
const work = computed<Work | undefined>(() => (props.locale === 'ja' ? japanese : english).find(w => w.path === props.path))
const capture = computed(() => captures.find(item => item.id === work.value?.id))
const story = computed(() => work.value ? (stories[props.locale] as Record<string, CaseStory>)[work.value.id] : undefined)
</script>
<template>
  <section v-if="work && capture" class="case-evidence" :aria-label="locale === 'ja' ? '画面と構成' : 'Interface and architecture'">
    <dl v-if="story" class="case-overview">
      <div><dt>{{ locale === 'ja' ? '何をつくったか' : 'The purpose' }}</dt><dd>{{ story.purpose }}</dd></div>
      <div><dt>{{ locale === 'ja' ? '設計の焦点' : 'The contribution' }}</dt><dd>{{ story.contribution }}</dd></div>
      <div><dt>{{ locale === 'ja' ? '使う人にとって' : 'For the visitor' }}</dt><dd>{{ story.result }}</dd></div>
    </dl>
    <ul class="work-stack"><li v-for="item in work.stack" :key="item">{{ item }}</li></ul>
    <CaseDiagram v-if="story" :story="story" />
    <figure><a :href="work.image" :aria-label="locale === 'ja' ? '画面キャプチャを原寸で開く' : 'Open the full-size screenshot'"><img :src="work.image" :alt="work.alt" width="1440" height="1100" fetchpriority="high"></a><figcaption>{{ work.title }} · {{ capture.kind === 'cli-output-view' ? (locale === 'ja' ? 'CLI実行結果の整形表示' : 'Formatted CLI execution output') : (locale === 'ja' ? '日本語UI・動作画面' : 'Live Japanese interface') }} · {{ capture.capturedOn }} · v{{ capture.version }}</figcaption></figure>
    <CaseDecisions v-if="story" :story="story" :locale="locale" />
  </section>
</template>

<style src="./portfolio/cases.css"></style>
