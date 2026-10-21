<script setup lang="ts">
// SPDX-License-Identifier: MIT
import { computed } from 'vue'
import english from '../work.en.json'
import japanese from '../work.ja.json'
import captures from '../captures.json'
import type { Locale } from '../types'
import type { Work } from '../work-types'
const props = defineProps<{ path: string; locale: Locale }>()
const work = computed<Work | undefined>(() => (props.locale === 'ja' ? japanese : english).find(w => w.path === props.path))
const capture = computed(() => captures.find(item => item.id === work.value?.id))
</script>
<template>
  <section v-if="work && capture" class="case-evidence" :aria-label="locale === 'ja' ? '画面と構成' : 'Interface and architecture'">
    <div class="case-meta"><ul class="work-stack"><li v-for="item in work.stack" :key="item">{{ item }}</li></ul><a :href="work.live">{{ work.id === 'zix-cli' ? (locale === 'ja' ? '公開バイナリを入手' : 'Get the release') : (locale === 'ja' ? '動作サイトを開く' : 'Open the live interface') }} ↗</a><a :href="work.source">{{ locale === 'ja' ? 'ソースを見る' : 'View the source' }} ↗</a></div>
    <figure><a :href="work.image" :aria-label="locale === 'ja' ? '画面キャプチャを原寸で開く' : 'Open the full-size screenshot'"><img :src="work.image" :alt="work.alt" width="1440" height="1100" fetchpriority="high"></a><figcaption>{{ work.title }} · {{ capture.kind === 'cli-output-view' ? (locale === 'ja' ? 'CLI実行結果の整形表示' : 'Formatted CLI execution output') : (locale === 'ja' ? '日本語UI・動作画面' : 'Live Japanese interface') }} · {{ capture.capturedOn }} · v{{ capture.version }}</figcaption></figure>
    <div class="case-pipeline"><h2>{{ locale === 'ja' ? '構成をたどる' : 'Follow the architecture' }}</h2><ol><li v-for="step in work.pipeline" :key="step">{{ step }}</li></ol></div>
  </section>
</template>
