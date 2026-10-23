// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { readSelections } from '../third-party/engineering/src/content.mts'
import { websiteExcerpt } from '../third-party/engineering/src/projections.mts'
import provenance from '../third-party/engineering/provenance.json' with { type: 'json' }
import excerpts from './guidance.json' with { type: 'json' }
const root = fileURLToPath(new URL('../third-party/engineering/', import.meta.url))

export function verifyEngineering() {
  assert.equal(provenance.repository, 'https://github.com/coela-oss/engineering')
  assert.match(provenance.source, /^[a-f0-9]{40}$/)
  const files = Object.entries(provenance.files)
  assert.equal(files.length, 11)
  for (const [path, digest] of files) {
    assert.match(path, /^(src\/[a-z-]+\.mts|datasets\/[a-z]+\.json|content\/(en|ja)\/[a-z-]+\.md|LICENSE|LICENSES\/(MIT|CC-BY-4\.0)\.txt)$/)
    const file = new URL(path, new URL('../third-party/engineering/', import.meta.url))
    const info = lstatSync(file)
    assert.ok(info.isFile() && !info.isSymbolicLink() && info.size <= 65536)
    assert.equal(createHash('sha256').update(readFileSync(file)).digest('hex'), digest)
  }
  const selected = readSelections(root)
  assert.deepEqual(excerpts, selected.map(selection => websiteExcerpt(root, selection)))
  assert.equal(excerpts.length, 4)
  return excerpts
}
