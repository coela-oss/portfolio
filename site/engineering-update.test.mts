// SPDX-License-Identifier: MIT
import test from 'node:test'
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import provenance from '../third-party/engineering/provenance.json' with { type: 'json' }
const root = fileURLToPath(new URL('..', import.meta.url))
const hash = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex')

test('release updater refuses stale receipts, altered archives and inconsistent rows before changing caller files', () => {
  const temp = mkdtempSync(join(tmpdir(), 'engineering-update-test-'))
  const paths = ['site/guidance.json', 'third-party/engineering/provenance.json',
    ...Object.keys(provenance.files).map(path => `third-party/engineering/${path}`)]
  const before = paths.map(path => readFileSync(join(root, path)))
  try {
    const name = 'coela-engineering-web-0.1.0.tar', archive = join(temp, name)
    execFileSync('tar', ['-cf', archive, '-C', join(root, 'third-party/engineering'), ...Object.keys(provenance.files)], { timeout: 5000 })
    const original = readFileSync(archive), sha = hash(original)
    const receipt = { kind: 'coela-engineering-web', version: '0.1.0', repository: provenance.repository,
      source: provenance.source, archive: { name, sha256: sha }, files: provenance.files,
      selections: JSON.parse(readFileSync(join(root, 'third-party/engineering/datasets/selections.json'), 'utf8')),
      rows: JSON.parse(readFileSync(join(root, 'site/guidance.json'), 'utf8')) }
    for (const kind of ['receipt', 'archive', 'rows']) {
      const candidate = structuredClone(receipt)
      if (kind === 'rows') candidate.rows[0].title = 'A separately edited title'
      const bytes = Buffer.from(JSON.stringify(candidate))
      writeFileSync(join(temp, 'release.json'), bytes)
      writeFileSync(archive, kind === 'archive' ? Buffer.concat([original, Buffer.from('changed')]) : original)
      assert.throws(() => execFileSync(process.execPath, [join(root, 'scripts/update-engineering.mts'), temp, sha,
        kind === 'receipt' ? '0'.repeat(64) : hash(bytes)], { timeout: 5000, maxBuffer: 65536, stdio: 'pipe' }))
      paths.forEach((path, index) => assert.deepEqual(readFileSync(join(root, path)), before[index], `${kind}: ${path}`))
    }
  } finally { rmSync(temp, { recursive: true, force: true }) }
})
