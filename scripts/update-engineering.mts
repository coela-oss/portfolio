// SPDX-License-Identifier: MIT
import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { createReadStream, lstatSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
const repository = fileURLToPath(new URL('..', import.meta.url))
const [directory, archiveSha256, receiptSha256, ...extra] = process.argv.slice(2)
const digest = (value: string | undefined): value is string => !!value && /^[a-f0-9]{64}$/.test(value)
if (!directory || !digest(archiveSha256) || !digest(receiptSha256) || extra.length) {
  throw Error('Provide the admitted Web release directory, archive SHA256 and receipt SHA256')
}
const hash = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex')
const read = (path: string, limit: number) => {
  const info = lstatSync(path)
  if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1 || info.size > limit) throw Error('Invalid release file')
  return readFileSync(path)
}
const raw = read(resolve(directory, 'release.json'), 65536)
if (hash(raw) !== receiptSha256) throw Error('Release receipt digest differs')
interface Receipt { kind: string; version: string; source: string; repository: string;
  archive: { name: string; sha256: string }; files: Record<string, string>; rows: unknown; selections: unknown }
const release = JSON.parse(raw.toString('utf8')) as Receipt
if (release.kind !== 'coela-engineering-web' || release.version !== '0.1.0'
  || release.repository !== 'https://github.com/coela-oss/engineering' || !/^[a-f0-9]{40}$/.test(release.source)
  || release.archive.name !== 'coela-engineering-web-0.1.0.tar' || release.archive.sha256 !== archiveSha256) throw Error('Unexpected Web release')
const archive = resolve(directory, release.archive.name), info = lstatSync(archive)
if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1 || info.size > 1048576) throw Error('Invalid archive')
const streamedHash = createHash('sha256')
for await (const chunk of createReadStream(archive)) streamedHash.update(chunk)
if (streamedHash.digest('hex') !== archiveSha256) throw Error('Archive digest differs')
const files = ['src/content.mts', 'src/projections.mts', 'datasets/catalog.json', 'datasets/selections.json',
  'content/en/principles.md', 'content/ja/principles.md', 'content/en/rust-resource-safety.md',
  'content/ja/rust-resource-safety.md', 'LICENSE', 'LICENSES/MIT.txt', 'LICENSES/CC-BY-4.0.txt']
if (Object.keys(release.files).sort().join() !== [...files].sort().join()
  || Object.values(release.files).some(value => !digest(value))) throw Error('Unexpected release closure')
const tar = (args: string[]) => execFileSync('tar', args, { timeout: 5000, maxBuffer: 65536, env: { PATH: process.env.PATH, LANG: 'C.UTF-8' } })
const listed = tar(['-tf', archive]).toString('utf8').trim().split('\n')
const directories = new Set(files.flatMap(path => path.split('/').slice(0, -1).map((_, i, segments) => segments.slice(0, i + 1).join('/') + '/')))
if (new Set(listed).size !== listed.length || listed.some(path => !files.includes(path) && !directories.has(path))
  || files.some(path => !listed.includes(path))) throw Error('Unexpected archive entries')
const staged = mkdtempSync(join(tmpdir(), 'portfolio-engineering-'))
try {
  const accepted = new Map<string, Buffer>()
  for (const path of files) {
    // Stream only allowlisted entries to stdout; archive paths cannot write files.
    const bytes = tar(['-xOf', archive, path])
    if (hash(bytes) !== release.files[path]) throw Error('Release source digest differs')
    const target = join(staged, path); mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, bytes)
    accepted.set(path, bytes)
  }
  const { readSelections } = await import(pathToFileURL(join(staged, 'src/content.mts')).href)
  const { websiteExcerpt } = await import(pathToFileURL(join(staged, 'src/projections.mts')).href)
  const selections = readSelections(staged)
  const rows = selections.map((selection: unknown) => websiteExcerpt(staged, selection))
  if (JSON.stringify(rows) !== JSON.stringify(release.rows)
    || JSON.stringify(selections) !== JSON.stringify(release.selections)) throw Error('Released projection differs')
  // All release evidence is checked before updating the caller's vendored files.
  for (const [path, bytes] of accepted) {
    const target = resolve(repository, 'third-party/engineering', path)
    mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, bytes)
  }
  writeFileSync(resolve(repository, 'third-party/engineering/provenance.json'), JSON.stringify({
    repository: release.repository, source: release.source, files: release.files,
    webRelease: { version: release.version, archiveSha256, receiptSha256,
      url: 'https://github.com/coela-oss/engineering/releases/tag/web/v0.1.0' },
  }, null, 2) + '\n')
  writeFileSync(resolve(repository, 'site/guidance.json'), JSON.stringify(rows, null, 2) + '\n')
  console.log('Verified immutable Web release and regenerated canonical presentation; no network or publication performed.')
} finally { rmSync(staged, { recursive: true, force: true }) }
