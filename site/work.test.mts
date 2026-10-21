// SPDX-License-Identifier: MIT
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import english from './work.en.json' with { type: 'json' }
import japanese from './work.ja.json' with { type: 'json' }
import captures from './captures.json' with { type: 'json' }
import redirects from './redirects.json' with { type: 'json' }
import pages from './content.json' with { type: 'json' }
test('each case has the same localized identity, actual evidence and distinct exits', () => {
  assert.deepEqual(english.map(w => w.path), japanese.map(w => w.path))
  for (const [locale, works] of [['en', english], ['ja', japanese]] as const) {
    const routes = new Set(pages.locales[locale].pages.map(p => p.path))
    for (const work of works) {
      assert.ok(routes.has(work.path));assert.equal(work.sections.length, 2)
      assert.ok(work.stack.length >= 3)
      const capture = captures.find(c => c.id === work.id)
      assert.ok(capture);assert.equal(capture.image, work.image)
      assert.equal(capture.repository, work.source);assert.equal(capture.origin, work.live)
      assert.notEqual(work.source, work.live)
      assert.match(capture.source, /^[a-f0-9]{40}$/)
      assert.match(capture.capturedOn, /^\d{4}-\d{2}-\d{2}$/)
      const bytes = readFileSync(new URL(`../sites/coela/public${capture.image}`, import.meta.url))
      assert.equal(createHash('sha256').update(bytes).digest('hex'), capture.sha256)
      for (const url of [work.source, work.live]) assert.equal(new URL(url).protocol, 'https:')
    }
  }
})
test('open-source grouping leads to public implementations, not a homepage cycle', () => {
  for (const content of Object.values(pages.locales)) {
    for (const page of content.pages.filter(p => p.path.startsWith('/oss/'))) {
      assert.ok(page.sections.some(s => s.links?.some(l => l.href.startsWith('https://github.com/'))))
    }
  }
})
test('case pages keep their problem, technical decisions and verification in both locales', () => {
  for (const [locale, works] of [['en', english], ['ja', japanese]] as const) {
    for (const work of works) {
      const page = pages.locales[locale].pages.find(p => p.path === work.path)
      assert.ok(page)
      for (const section of work.sections) assert.ok(page.sections.some(s => s.text === section.text))
    }
  }
})

test('legacy entry points reach a live page or independent product, without alias loops', () => {
  const paths = new Set(pages.locales.en.pages.map(p => p.path))
  for (const [from, to] of Object.entries(redirects)) {
    assert.ok(!paths.has(from));assert.notEqual(from, to)
    if (to.startsWith('/')) { assert.ok(paths.has(to));assert.ok(!Object.hasOwn(redirects, to)) }
    else assert.equal(new URL(to).protocol, 'https:')
  }
})
