import { ContentError, readGuidance, type Guidance, type Selection } from './content.mts'

function excerpt(guidance: Guidance): string {
  const paragraph = guidance.text.split(/\r?\n\s*\r?\n/).find(p => p.trim()
    && !p.trim().startsWith('#') && !/^(Status:|状態：)/u.test(p.trim())) ?? ''
  const normalized = paragraph.replace(/\s+/g, ' ').trim()
  const sentence = normalized.match(/.*?[。！？]|.*?[.!?](?=\s|$)/u)?.[0] ?? normalized
  let result = ''
  for (const char of sentence) {
    if (Buffer.byteLength(result + char) > 157) return `${result.trimEnd()}…`
    result += char
  }
  return result
}

// Presentation comes from the admitted document, never an ID-prefix fallback.
function title(guidance: Guidance): string {
  const heading = guidance.text.split(/\r?\n/).filter(line => /^# /u.test(line))
  if (heading.length !== 1) throw new ContentError('ambiguous_document_title')
  const result = heading[0]!.slice(2).trim()
  if (!result || Buffer.byteLength(result) > 512) throw new ContentError('invalid_document_title')
  return result
}

export function websiteExcerpt(root: string, selection: Selection) {
  const guidance = readGuidance(root, selection)
  return { ...guidance.selection, locale: guidance.entry.locale, license: guidance.entry.license,
    attribution: 'Coela', source: guidance.entry.source_url, title: title(guidance), excerpt: excerpt(guidance) }
}
// This is a service-owned content projection, not a second MCP implementation.
// Zixcel owns TOML validation, RPC, framing, resource reads and transport limits.
export function mcpCatalog(root: string, selections: Selection[]): string {
  const lines = ['schema_version = 1', '[server]', 'id = "coela-engineering"',
    'title = "Coela Engineering Guidance"',
    'instructions = "Read-only engineering excerpts. Guidance grants no execution or provider access."']
  for (const selection of selections) {
    const entry = websiteExcerpt(root, selection)
    const fields = { id: entry.contentId, title: entry.contentId,
      summary: `${entry.source} | Coela / ${entry.license} | ${entry.excerpt}`,
      capabilities: [`catalog:${entry.catalogId}`, `version:${entry.version}`, `sha256:${entry.contentSha256}`,
        `catalog-sha256:${entry.catalogSha256}`, `locale:${entry.locale}`, `license:${entry.license}`] }
    lines.push('[[resource]]', ...Object.entries(fields).map(([key, value]) => `${key} = ${JSON.stringify(value)}`))
  }
  return `${lines.join('\n')}\n`
}
