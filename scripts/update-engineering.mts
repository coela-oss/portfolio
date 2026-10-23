// SPDX-License-Identifier: MIT
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
const repository = fileURLToPath(new URL('..', import.meta.url))
const [source, commit, ...extra] = process.argv.slice(2)
if (!source || !commit || extra.length || !/^[a-f0-9]{40}$/.test(commit)) throw Error('Provide a reviewed local engineering checkout and full source commit')
const options = { cwd: resolve(source), maxBuffer: 65536, env: { LANG: 'C.UTF-8', PATH: process.env.PATH ?? '' } }
if (execFileSync('git', ['rev-parse', 'HEAD'], options).toString().trim() !== commit) throw Error('Engineering source commit differs')
execFileSync('git', ['diff', '--exit-code', 'HEAD', '--'], options)
const files = ['src/content.mts', 'src/projections.mts', 'datasets/catalog.json', 'datasets/selections.json',
  'content/en/principles.md', 'content/ja/principles.md', 'content/en/rust-resource-safety.md',
  'content/ja/rust-resource-safety.md', 'LICENSE', 'LICENSES/MIT.txt', 'LICENSES/CC-BY-4.0.txt']
const hashes: Record<string, string> = {}
for (const path of files) {
  const bytes = execFileSync('git', ['show', `${commit}:${path}`], options)
  hashes[path] = createHash('sha256').update(bytes).digest('hex')
  const target = resolve(repository, 'third-party/engineering', path)
  mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, bytes)
}
const excerpts = JSON.parse(execFileSync(process.execPath, ['scripts/project-guidance.mts', 'website'], options).toString()) as unknown
writeFileSync(resolve(repository, 'third-party/engineering/provenance.json'), JSON.stringify({
  repository: 'https://github.com/coela-oss/engineering', source: commit, files: hashes,
}, null, 2) + '\n')
writeFileSync(resolve(repository, 'site/guidance.json'), JSON.stringify(excerpts, null, 2) + '\n')
console.log('Updated reviewed engineering snapshot and generated excerpts; no network or publication performed.')
