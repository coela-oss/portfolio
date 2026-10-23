// SPDX-License-Identifier: MIT
import test from 'node:test'
import assert from 'node:assert/strict'
import { verifyEngineering } from './guidance.mts'
import pages from './content.json' with { type: 'json' }

test('portfolio consumes the exact admitted upstream source, excerpt and attribution', () => {
  const entries = verifyEngineering()
  for (const locale of ['en', 'ja'] as const) {
    const selected = entries.filter(item => item.locale === locale)
    assert.equal(selected.length, 2)
    for (const entry of selected) {
      assert.equal(entry.version, '0.2.4')
      assert.equal(entry.license, 'CC-BY-4.0')
      assert.equal(entry.attribution, 'Coela')
      assert.ok(entry.excerpt.length > 20)
      assert.match(entry.source, new RegExp(`/blob/[a-f0-9]{40}/content/${locale}/`))
    }
  }
})
test('the principles route has no separately edited guidance copy and retains both language routes', () => {
  for (const locale of ['en', 'ja'] as const) {
    const page = pages.locales[locale].pages.find(item => item.path === '/about/principles')
    assert.ok(page)
    assert.equal(page.status, 'published')
    assert.deepEqual(page.sections, [])
  }
})
