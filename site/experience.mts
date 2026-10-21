import assert from 'node:assert/strict'
import type { Experience } from './experience-types'
import type { SiteContent } from './types'

export function validateExperience(experience: Experience, content: SiteContent) {
  const routes = new Set(content.pages.filter(page => page.status !== 'draft').map(page => page.path))
  assert.ok(experience.category.trim() && experience.pathsTitle.trim(), 'missing visitor context')
  assert.ok(experience.primary.href !== experience.secondary.href, 'primary and secondary destinations must differ')
  assert.equal(experience.paths.length, 3, 'provide three focused visitor journeys')
  for (const link of [experience.primary, experience.secondary, ...experience.paths]) {
    assert.ok(link.title.trim(), 'journey link needs an actionable label')
    if (link.href.startsWith('/')) assert.ok(routes.has(link.href), `unavailable journey: ${link.href}`)
    else {
      const url = new URL(link.href)
      assert.ok(url.protocol === 'https:' && !url.username && !url.password, 'unsafe external journey')
    }
    assert.notEqual(link.href, '/', 'journeys must lead beyond the homepage')
  }
  assert.equal(new Set(experience.paths.map(link => link.href)).size, 3, 'visitor journeys must be distinct')
  assert.ok(['workspace', 'directory', 'meaning', 'code', 'portfolio', 'business', 'trust', 'plan', 'environment'].includes(experience.preview.kind))
  assert.ok(experience.preview.label.trim() && experience.preview.title.trim() && experience.preview.outcome.trim())
  assert.ok(experience.preview.rows.length >= 2 && experience.preview.rows.length <= 4)
  for (const row of experience.preview.rows) assert.ok(row.label.trim() && row.detail.trim())
}
