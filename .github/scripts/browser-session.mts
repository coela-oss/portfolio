// SPDX-License-Identifier: MIT
// Hosted-CI-only rendered checks: no local browser, developer credentials or external origin.
import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
export function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('Expected an object')
  return value as Record<string, unknown>
}
const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms))
export function browserStartupDiagnostic(stderr: string, exitCode: number | null, signal: NodeJS.Signals | null) {
  // Report fixed signals only; never expose profile paths or DevTools endpoints.
  return JSON.stringify({ exitCode, signal,
    sandboxMessage: /sandbox|namespace/i.test(stderr),
    dbusMessage: /D-Bus|dbus|connect to.*bus/i.test(stderr),
    fatalMessage: /FATAL|crashpad/i.test(stderr),
    stderrTruncated: Buffer.byteLength(stderr) > 65536 })
}
export async function browserSession() {
  if (process.env.GITHUB_ACTIONS !== 'true') throw Error('Browser acceptance runs only on the hosted CI runner')
  const profile = mkdtempSync(join(tmpdir(), 'portfolio-browser-'))
  const browser = spawn('/usr/bin/google-chrome', ['--headless=new', '--disable-gpu', '--disable-background-networking',
    '--disable-extensions', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], {
      stdio: ['ignore', 'ignore', 'pipe'], env: { PATH: process.env.PATH, HOME: profile, LANG: 'C.UTF-8', XDG_CACHE_HOME: profile }
    })
  let stderr = '', stderrBytes = 0, spawnError = false
  browser.stderr.on('data', (bytes: Buffer) => {
    stderrBytes += bytes.length
    if (Buffer.byteLength(stderr) < 65536) stderr += bytes.subarray(0, 65536 - Buffer.byteLength(stderr)).toString('utf8')
  })
  browser.on('error', () => { spawnError = true })
  const startupFailure = (reason: string) => Error(`${reason}: ${browserStartupDiagnostic(
    stderr + (stderrBytes > 65536 ? ' ' : ''), browser.exitCode, browser.signalCode)}`)
  const pending = new Map<number, { resolve: (value: Record<string, unknown>) => void; reject: (error: Error) => void; timer: NodeJS.Timeout }>()
  let socket: WebSocket | undefined, next = 0
  const errors: string[] = []
  async function close() {
    socket?.close()
    for (const item of pending.values()) { clearTimeout(item.timer); item.reject(Error('Browser closed')) }
    pending.clear()
    if (browser.exitCode === null) {
      browser.kill('SIGTERM')
      await Promise.race([once(browser, 'exit'), sleep(2000)])
      if (browser.exitCode === null && browser.signalCode === null) { browser.kill('SIGKILL'); await once(browser, 'exit') }
    }
    rmSync(profile, { recursive: true, force: true })
  }
  try {
    const active = join(profile, 'DevToolsActivePort')
    const startupDeadline = performance.now() + 30000
    while (!existsSync(active) && performance.now() < startupDeadline) {
      if (spawnError || browser.exitCode !== null) throw startupFailure('Browser exited before startup')
      await sleep(100)
    }
    if (!existsSync(active)) throw startupFailure('Browser startup deadline exceeded (30 seconds)')
    const port = readFileSync(active, 'utf8').split('\n')[0]!
    if (!/^\d+$/.test(port)) throw Error('Invalid browser port')
    const response: unknown = await (await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(5000) })).json()
    if (!Array.isArray(response)) throw Error('Missing browser target')
    const target = object(response.find(item => object(item).type === 'page'))
    if (typeof target.webSocketDebuggerUrl !== 'string' || !target.webSocketDebuggerUrl.startsWith(`ws://127.0.0.1:${port}/`)) throw Error('Unexpected browser origin')
    socket = new WebSocket(target.webSocketDebuggerUrl)
    await Promise.race([once(socket, 'open'), sleep(10000).then(() => { throw Error('Browser connection timed out') })])
    socket.addEventListener('message', event => {
      if (typeof event.data !== 'string' || event.data.length > 8 * 1024 * 1024) { errors.push('Invalid browser message'); return }
      const message = object(JSON.parse(event.data) as unknown)
      if (message.method === 'Runtime.exceptionThrown') errors.push('Uncaught browser exception')
      if (typeof message.id !== 'number') return
      const request = pending.get(message.id)
      if (!request) return
      clearTimeout(request.timer); pending.delete(message.id)
      if (message.error) request.reject(Error(JSON.stringify(message.error)))
      else request.resolve(object(message.result))
    })
    function call(method: string, params: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
      if (pending.size >= 8) throw Error('Browser command limit')
      const id = ++next
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { pending.delete(id); reject(Error(`Browser timeout: ${method}`)) }, 12000)
        pending.set(id, { resolve, reject, timer })
        socket!.send(JSON.stringify({ id, method, params }))
      })
    }
    async function evaluate(expression: string): Promise<unknown> {
      const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
      if (result.exceptionDetails) throw Error('Browser expression failed')
      return object(result.result).value
    }
    await call('Runtime.enable'); await call('Page.enable')
    return { call, evaluate, close, errors }
  } catch (error) { await close(); throw error }
}
