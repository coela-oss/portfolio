// SPDX-License-Identifier: MIT
import test from 'node:test'
import assert from 'node:assert/strict'
import { browserStartupDiagnostic } from '../.github/scripts/browser-session.mts'

test('hosted browser startup diagnostics retain failure signals without leaking raw endpoints or credentials', () => {
  const raw = 'Failed to connect to D-Bus; sandbox namespace unavailable; FATAL crashpad\n'
    + 'DevTools listening on ws://127.0.0.1:9222/devtools/browser/private-endpoint\n'
    + 'synthetic-secret-do-not-emit /tmp/private-profile'
  const value = browserStartupDiagnostic(raw, 1, null)
  assert.deepEqual(JSON.parse(value), { exitCode: 1, signal: null,
    sandboxMessage: true, dbusMessage: true, fatalMessage: true, stderrTruncated: false })
  for (const fragment of ['private-endpoint', 'synthetic-secret', '/tmp/private-profile', 'ws://']) assert.ok(!value.includes(fragment))
  assert.equal(JSON.parse(browserStartupDiagnostic('x'.repeat(65537), null, 'SIGKILL')).stderrTruncated, true)
})
