// SPDX-License-Identifier: MIT
import test from 'node:test'
import assert from 'node:assert/strict'
import stories from './case-stories.json' with { type: 'json' }
import data from './content.mjs'
import works from './work.en.json' with { type: 'json' }
import { nextSteps } from './navigation.mts'
import type { Section } from './types.ts'
for (const locale of ['ja', 'en'] as const) {
  test(`${locale}: cases have explanatory diagrams, decision tables and distinct actionable exits`, () => {
    for (const work of works) {
      const story = stories[locale][work.id as keyof typeof stories.en]
      assert.ok(story.purpose && story.contribution && story.result)
      assert.equal(story.flow.length, 4)
      assert.equal(story.decisions.length, 3)
      assert.equal(new Set(story.actions.map(link => link.href)).size, 3)
      for (const step of story.flow) assert.ok(step.title && step.text)
      for (const row of story.decisions) assert.ok(row.choice && row.reason && row.scope)
      for (const action of story.actions) {
        assert.ok(action.title && action.summary)
        assert.equal(new URL(action.href).protocol, 'https:')
        assert.ok(!action.href.startsWith(data.origin), 'a case exit must not loop into the portfolio')
      }
    }
  })
  test(`${locale}: secondary journeys preserve context and reach published pages`, () => {
    const pages = data.locales[locale].pages
    for (const page of pages) {
      const links = nextSteps(page.path, locale)
      assert.equal(new Set(links.map(link => link.href)).size, links.length)
      for (const link of links) {
        assert.notEqual(link.href, page.path)
        assert.notEqual(link.href, '/')
        assert.ok(link.title?.trim())
        assert.ok(pages.some(target => target.path === link.href && target.status === 'published'))
      }
      if (page.path.startsWith('/work/')) assert.deepEqual(links, [], 'case actions own their concrete exits')
    }
  })
  test(`${locale}: OSS categories describe actual source destinations and related case studies`, () => {
    for (const page of data.locales[locale].pages.filter(page => page.path.startsWith('/oss/'))) {
      const sections: Section[] = page.sections
      const projects = sections[0]?.links
      assert.ok(projects?.length)
      for (const link of projects) {
        assert.ok(link.summary?.trim())
        assert.ok(link.href.startsWith('https://github.com/'))
      }
      assert.ok(sections[1]?.links?.some(link => link.href.startsWith('/work/')))
    }
  })
}
test('language and website source destinations stay distinct', () => {
  for (const locale of ['ja', 'en'] as const) {
    const links = stories[locale]['sem-lang'].actions.map(link => link.href)
    assert.ok(links.includes('https://github.com/semantic-language/sem-lang'))
    assert.ok(links.includes('https://github.com/semantic-language/semantic-language-site'))
  }
  for (const work of works) {
    const id = work.id as keyof typeof stories.en
    assert.deepEqual(stories.ja[id].actions.map(link => link.href), stories.en[id].actions.map(link => link.href))
  }
})
