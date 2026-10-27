import documentContent from './content.mjs'
import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'
import { validateExperience } from './experience.mts'
import type { Experience } from './experience-types'
import type { Locale, SiteContent } from './types'

const data = documentContent
const experiences = JSON.parse(readFileSync(new URL('./experience.json', import.meta.url), 'utf8')) as Record<Locale, Experience>
for (const locale of ['ja', 'en'] as const) {
  const experience = experiences[locale]
  const content = data.locales[locale] as SiteContent
  test(`${locale}: every visitor action has a published destination`, () => validateExperience(experience, content))
  test(`${locale}: missing destination is rejected before publication`, () => {
    const changed = structuredClone(experience)
    changed.primary.href = '/missing-visitor-destination'
    assert.throws(() => validateExperience(changed, content), /unavailable journey/)
  })
  test(`${locale}: duplicate and misleading homepage exits are refused`, () => {
    const changed = structuredClone(experience)
    changed.paths[1]!.href = changed.paths[0]!.href
    assert.throws(() => validateExperience(changed, content), /distinct/)
    changed.paths[1]!.href = '/'
    assert.throws(() => validateExperience(changed, content), /beyond the homepage/)
  })
}
test('language changes preserve task and product identity', () => {
  assert.equal(experiences.ja.primary.href, experiences.en.primary.href)
  assert.equal(experiences.ja.secondary.href, experiences.en.secondary.href)
  assert.equal(experiences.ja.preview.kind, experiences.en.preview.kind)
  assert.deepEqual(experiences.ja.paths.map(item => item.href), experiences.en.paths.map(item => item.href))
})
