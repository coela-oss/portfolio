// SPDX-License-Identifier: MIT
import type { Link, Locale } from './types.ts'
const routes = {
  '/work': ['/oss', '/about/principles'],
  '/oss': ['/work', '/docs'],
  '/oss/web': ['/work/nuxtjp', '/oss/tools'],
  '/oss/tools': ['/work/zix-cli', '/oss/systems'],
  '/oss/systems': ['/work/ihat', '/oss/language'],
  '/oss/language': ['/work/sem-lang', '/oss/web'],
  '/about': ['/about/principles', '/work'],
  '/about/principles': ['/work/zix-cli', '/journal/interface-and-authority'],
  '/journal': ['/work', '/about/principles'],
  '/journal/interface-and-authority': ['/work/ihat', '/about/principles'],
  '/docs': ['/oss', '/contact'],
  '/contact': ['/work', '/security']
} as const
const titles: Record<Locale, Record<string, string>> = {
  ja: { '/work': '作品の設計を読む', '/oss': '公開実装を分野から探す', '/docs': '資料と実装を調べる',
    '/about/principles': '設計指針を読む', '/work/nuxtjp': 'NuxtJPの情報設計', '/work/zix-cli': 'Zix CLIの責務分離',
    '/work/ihat': 'iHATの検索と配布導線', '/work/sem-lang': 'sem-langの概念を伝えるUI', '/oss/web': 'Web・UIの実装',
    '/oss/tools': '開発ツールの実装', '/oss/systems': '実行・信頼の実装', '/oss/language': '意味・データの実装',
    '/journal/interface-and-authority': '画面と権限の設計ノート', '/contact': '提案先を確認する', '/security': '公開情報の扱い' },
  en: { '/work': 'Read the case studies', '/oss': 'Find source by discipline', '/docs': 'Explore implementation references',
    '/about/principles': 'Read the engineering principles', '/work/nuxtjp': 'NuxtJP information design', '/work/zix-cli': 'Zix CLI boundaries',
    '/work/ihat': 'iHAT discovery and distribution', '/work/sem-lang': 'Introducing sem-lang through UI', '/oss/web': 'Web and UI source',
    '/oss/tools': 'Developer tool source', '/oss/systems': 'Execution and trust source', '/oss/language': 'Language and data source',
    '/journal/interface-and-authority': 'Notes on interfaces and authority', '/contact': 'Find a place for feedback', '/security': 'Public information boundaries' }
}
export function nextSteps(path: string, locale: Locale): Link[] {
  const destinations = routes[path as keyof typeof routes] ?? []
  return destinations.filter(href => href !== path).map(href => ({ href, title: titles[locale][href]! }))
}
