/** Owner-local bounded process adapter; edge semantics belong to the public provider. */
import { validateEdgePins, edgeScriptDigest, originHtml } from '@zixcel/provider-cloudflare/edge-verification'
try {
  const [operation, raw] = process.argv.slice(2)
  if (!['pins', 'digest', 'html'].includes(operation) || raw === undefined || raw.length > 1024) throw Error('Invalid operation')
  const chunks = []; let size = 0
  for await (const chunk of process.stdin) { size += chunk.length; if (size > 8 * 1024 * 1024) throw Error('Input limit'); chunks.push(chunk) }
  const bytes = Buffer.concat(chunks)
  const value = JSON.parse(raw)
  if (operation === 'pins') process.stdout.write(JSON.stringify(validateEdgePins(value)))
  else if (operation === 'digest') process.stdout.write(JSON.stringify(edgeScriptDigest(bytes) ?? null))
  else process.stdout.write(originHtml(bytes, value))
} catch { console.error('Public edge adapter rejected input'); process.exitCode = 2 }
