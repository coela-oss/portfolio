<script setup lang="ts">
import excerpts from '../guidance.json'
import type { Locale } from '../types'
const props = defineProps<{ locale: Locale }>()
</script>
<template>
  <section class="engineering-guidance" :aria-label="locale === 'ja' ? '設計指針の原文' : 'Engineering guidance sources'">
    <p>{{ locale === 'ja' ? '独立したEngineeringリポジトリの原文から引用しています。詳しい考え方は、それぞれの指針へ。' : 'Excerpts from the independent Engineering repository. Follow each source to read the full guidance.' }}</p>
    <div class="guidance-grid">
      <article v-for="entry in excerpts.filter(item => item.locale === locale)" :key="entry.contentId" class="guidance-card" :data-content-id="entry.contentId" :data-content-version="entry.version">
        <p class="guidance-edition">{{ locale === 'ja' ? '原文の版' : 'Source edition' }} {{ entry.version }}</p>
        <h2>{{ entry.title }}</h2>
        <blockquote>{{ entry.excerpt }}</blockquote>
        <p class="guidance-credit">{{ entry.attribution }} · <a href="https://creativecommons.org/licenses/by/4.0/">{{ entry.license }}</a></p>
        <a class="guidance-source" :href="entry.source">{{ locale === 'ja' ? 'この版の原文を読む' : 'Read this source edition' }} <span aria-hidden="true">↗</span></a>
        <details><summary>{{ locale === 'ja' ? '出典と検証情報' : 'Source and verification' }}</summary><dl>
          <dt>{{ locale === 'ja' ? '文書ID' : 'Content ID' }}</dt><dd>{{ entry.contentId }}</dd>
          <dt>SHA-256</dt><dd><code>{{ entry.contentSha256 }}</code></dd>
          <dt>{{ locale === 'ja' ? 'カタログ' : 'Catalog' }}</dt><dd>{{ entry.catalogId }} / {{ entry.version }}</dd>
        </dl></details>
      </article>
    </div>
  </section>
</template>
<style scoped>
.engineering-guidance { margin-block: 1rem 3rem; }
.engineering-guidance > p { max-width: 48rem; color: var(--site-muted, #536477); line-height: 1.8; }
.guidance-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.25rem; margin-top: 1.5rem; }
.guidance-card { min-width: 0; padding: clamp(1.25rem, 3vw, 2rem); border: 1px solid #c8d7d9; border-radius: 1.25rem; background: linear-gradient(145deg, #f1f8f8, #fff); }
.guidance-edition { color: #326970; font-size: .85rem; font-weight: 650; }
.guidance-card h2 { font-size: 1.35rem; line-height: 1.5; margin-block: .7rem 1rem; }
.guidance-card blockquote { margin: 0; padding-inline-start: 1rem; border-inline-start: 3px solid #75a9ae; line-height: 1.9; }
.guidance-credit { font-size: .85rem; margin-top: 1.2rem; }
.guidance-source { display: inline-block; color: #205961; font-weight: 650; margin-block: .5rem 1.2rem; }
.guidance-card details { border-top: 1px solid #c8d7d9; padding-top: .8rem; font-size: .85rem; }
.guidance-card summary { cursor: pointer; }
.guidance-card dl { margin-bottom: 0; }
.guidance-card dt { font-weight: 650; margin-top: .8rem; }
.guidance-card dd { margin: .3rem 0 0; overflow-wrap: anywhere; }
@media (max-width: 700px) { .guidance-grid { grid-template-columns: 1fr; } }
</style>
