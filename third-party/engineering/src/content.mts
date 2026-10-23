import { createHash } from 'node:crypto'
import { closeSync, constants, fstatSync, lstatSync, openSync, readSync } from 'node:fs'
import { join, resolve } from 'node:path'

export interface CatalogEntry { id: string; locale: 'en' | 'ja'; path: string; source_url: string; license: 'CC-BY-4.0'; sha256: string }
export interface Catalog { schema_version: 1; id: string; version: string; entries: CatalogEntry[] }
export interface Selection { catalogId: string; version: string; catalogSha256: string; contentId: string; contentSha256: string }
export interface Guidance { selection: Selection; entry: CatalogEntry; text: string }
export class ContentError extends Error {
  readonly code: string
  constructor(code: string) { super(code); this.code = code; this.name = 'ContentError' }
}
function requireValue(condition: unknown, code: string): asserts condition {
  if (!condition) throw new ContentError(code)
}
function object(value: unknown, keys: string): Record<string, unknown> {
  requireValue(value && typeof value === 'object' && !Array.isArray(value), 'invalid_object')
  requireValue(Object.keys(value).sort().join(',') === keys, 'invalid_fields')
  return value as Record<string, unknown>
}
const id = (value: unknown): value is string => typeof value === 'string' && /^[a-z][a-z0-9-]{0,62}$/.test(value)
const digest = (value: unknown): value is string => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value)
const version = (value: unknown): value is string => typeof value === 'string' && /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(value)
export const sha256 = (value: Uint8Array): string => createHash('sha256').update(value).digest('hex')

// Only trusted local checkout roots are accepted. Content paths are derived from
// the closed schema, never from a resource URI or arbitrary browser input.
function bytes(root: string, segments: string[], limit: number): Buffer {
  let parent = resolve(root)
  for (const part of ['', ...segments.slice(0, -1)]) {
    parent = join(parent, part)
    const info = lstatSync(parent)
    requireValue(info.isDirectory() && !info.isSymbolicLink(), 'linked_directory')
  }
  const fd = openSync(join(parent, segments.at(-1)!), constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK)
  try {
    const info = fstatSync(fd)
    requireValue(info.isFile() && info.nlink === 1 && info.size <= limit, 'invalid_file')
    const result = Buffer.alloc(limit + 1)
    let size = 0
    while (size < result.length) {
      const count = readSync(fd, result, size, result.length - size, null)
      if (count === 0) break
      size += count
    }
    requireValue(size <= limit, 'file_limit')
    return result.subarray(0, size)
  } finally { closeSync(fd) }
}
function text(value: Uint8Array): string {
  try { return new TextDecoder('utf-8', { fatal: true }).decode(value) }
  catch { throw new ContentError('invalid_utf8') }
}
export function validateCatalog(value: unknown): Catalog {
  const catalog = object(value, 'entries,id,schema_version,version')
  requireValue(catalog.schema_version === 1, 'unsupported_schema')
  requireValue(catalog.id === 'coela-engineering-content' && version(catalog.version), 'invalid_catalog_identity')
  requireValue(Array.isArray(catalog.entries) && catalog.entries.length > 0 && catalog.entries.length <= 64, 'invalid_entries')
  const ids = new Set<string>(), paths = new Set<string>()
  for (const value of catalog.entries) {
    const entry = object(value, 'id,license,locale,path,sha256,source_url')
    requireValue(id(entry.id) && (entry.locale === 'en' || entry.locale === 'ja') && digest(entry.sha256)
      && entry.license === 'CC-BY-4.0', 'invalid_entry')
    requireValue(typeof entry.path === 'string' && /^content\/(en|ja)\/[a-z0-9-]+\.md$/.test(entry.path)
      && entry.path.startsWith(`content/${entry.locale}/`), 'invalid_path')
    requireValue(typeof entry.source_url === 'string'
      && /^https:\/\/github\.com\/coela-oss\/engineering\/blob\/[a-f0-9]{40}\//.test(entry.source_url)
      && entry.source_url.split('/').slice(7).join('/') === entry.path, 'unbound_source')
    requireValue(!ids.has(entry.id) && !paths.has(entry.path), 'duplicate_entry')
    ids.add(entry.id); paths.add(entry.path)
  }
  return catalog as unknown as Catalog
}
export function validateSelection(value: unknown): Selection {
  const selection = object(value, 'catalogId,catalogSha256,contentId,contentSha256,version')
  requireValue(selection.catalogId === 'coela-engineering-content' && version(selection.version)
    && id(selection.contentId) && digest(selection.catalogSha256) && digest(selection.contentSha256), 'invalid_selection')
  return selection as unknown as Selection
}
export function readGuidance(root: string, expected: Selection): Guidance {
  validateSelection(expected)
  const raw = bytes(root, ['datasets', 'catalog.json'], 65536)
  requireValue(sha256(raw) === expected.catalogSha256, 'stale_catalog')
  const catalog = validateCatalog(JSON.parse(text(raw)))
  requireValue(catalog.id === expected.catalogId && catalog.version === expected.version, 'stale_version')
  const entry = catalog.entries.find(item => item.id === expected.contentId)
  requireValue(entry, 'unknown_content')
  requireValue(entry.sha256 === expected.contentSha256, 'stale_content')
  // Validate the complete bounded snapshot, including entries not selected by this reader.
  let total = 0, selected = ''
  for (const item of catalog.entries) {
    const raw = bytes(root, item.path.split('/'), 65536)
    total += raw.length
    requireValue(total <= 1048576, 'snapshot_limit')
    requireValue(sha256(raw) === item.sha256, 'altered_content')
    const decoded = text(raw)
    if (item.id === entry.id) selected = decoded
  }
  return { selection: { ...expected }, entry: { ...entry }, text: selected }
}
export function readSelections(root: string): Selection[] {
  const value: unknown = JSON.parse(text(bytes(root, ['datasets', 'selections.json'], 65536)))
  requireValue(Array.isArray(value) && value.length > 0 && value.length <= 64, 'invalid_selections')
  const selections = value.map(validateSelection)
  requireValue(new Set(selections.map(item => item.contentId)).size === selections.length, 'duplicate_selection')
  return selections
}
