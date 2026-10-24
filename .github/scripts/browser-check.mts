// SPDX-License-Identifier: MIT
import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdirSync, writeFileSync } from 'node:fs'
import { createServer } from 'node:net'
import { resolve } from 'node:path'
import { browserSession, object } from './browser-session.mts'
import data from '../../site/content.json' with { type: 'json' }
import guidance from '../../site/guidance.json' with { type: 'json' }
if (process.env.GITHUB_ACTIONS !== 'true') throw Error('Rendered checks are restricted to hosted CI')
const probe = createServer(); probe.listen(0, '127.0.0.1'); await once(probe, 'listening')
const address = probe.address()
if (!address || typeof address === 'string') throw Error('No local port')
const port = address.port; await new Promise<void>(resolve => probe.close(() => resolve()))
const origin = `http://127.0.0.1:${port}`
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1', '--directory', resolve('.output/coela/public')], { stdio: 'ignore' })
let browser: Awaited<ReturnType<typeof browserSession>> | undefined
const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms))
const results: Record<string, unknown>[] = []
try {
  for (let n = 0; n < 50; n++) {
    if (await fetch(origin, { signal: AbortSignal.timeout(500) }).then(r => r.ok).catch(() => false)) break
    await sleep(100)
  }
  browser = await browserSession()
  mkdirSync('browser-results', { recursive: true })
  for (const locale of ['en', 'ja'] as const) for (const width of [360, 768, 1440]) {
    await browser.call('Emulation.setDeviceMetricsOverride', { width, height: 1100, deviceScaleFactor: 1, mobile: false })
    for (const page of data.locales[locale].pages) {
      const path = (locale === 'en' ? '' : '/ja') + page.path
      console.log(`Render ${locale} ${width}px ${page.path}`)
      await browser.call('Page.navigate', { url: origin + path })
      let ready = false
      for (let n = 0; n < 100; n++) {
        ready = await browser.evaluate(`location.pathname.replace(new RegExp('/$'),'')===${JSON.stringify(path.replace(new RegExp('/$'), ''))} && document.readyState==='complete' && !!document.querySelector('main h1')`) === true
        if (ready) break
        await sleep(100)
      }
      if (!ready) throw Error(`Page not ready: ${path}`)
      const images = await browser.evaluate(`Promise.race([
        Promise.all([...document.images].map(image=>{image.loading='eager';return image.decode().then(()=>true,()=>false)})),
        new Promise(resolve=>setTimeout(()=>resolve(null),7000))])`)
      if (!Array.isArray(images) || images.some(decoded => decoded !== true)) throw Error(`Image loading failed or exceeded its deadline: ${path}`)
      const result = object(await browser.evaluate(`(()=>({h1:document.querySelectorAll('h1').length,
        overflow:document.documentElement.scrollWidth>innerWidth+1,
        missing:[...document.images].some(image=>!image.naturalWidth),
        header:getComputedStyle(document.querySelector('.site-header')).position,
        selfExit:[...document.querySelectorAll('.page-next-steps a,.case-actions a')].some(a=>new URL(a.href).pathname.replace(new RegExp('/$'),'')===location.pathname.replace(new RegExp('/$'),'') && new URL(a.href).origin===location.origin),
        flow:document.querySelectorAll('.case-flow li').length,
        decisions:document.querySelectorAll('.case-evidence tbody tr').length,
        exits:document.querySelectorAll('.case-actions .visitor-path').length
      }))()`))
      if (result.h1 !== 1 || result.overflow || result.missing || result.header !== 'sticky' || result.selfExit) throw Error(`${locale}/${width}${page.path}: ${JSON.stringify(result)}`)
      if (page.path.startsWith('/work/') && (result.flow !== 4 || result.decisions !== 3 || result.exits !== 3)) throw Error(`Incomplete case: ${path}`)
      if (page.path === '/about/principles') {
        const expected = guidance.filter(entry => entry.locale === locale)
        const shown = await browser.evaluate(`([...document.querySelectorAll('.guidance-card')].map(card => ({
          id:card.getAttribute('data-content-id'),version:card.getAttribute('data-content-version'),
          source:card.querySelector('.guidance-source')?.getAttribute('href'),
          title:card.querySelector('h2')?.textContent?.trim(),
          excerpt:card.querySelector('blockquote')?.textContent?.trim(),
          license:card.querySelector('.guidance-credit a')?.textContent?.trim()
        })))`)
        if (JSON.stringify(shown) !== JSON.stringify(expected.map(entry => ({ id: entry.contentId,
          version: entry.version, source: entry.source, title: entry.title, excerpt: entry.excerpt, license: entry.license })))) {
          throw Error(`Engineering source projection changed: ${path}`)
        }
        await browser.evaluate("document.querySelectorAll('.guidance-card details').forEach(detail=>detail.open=true)")
        if (await browser.evaluate('document.documentElement.scrollWidth>innerWidth+1') === true) throw Error('Engineering identity metadata overflows')
      }
      if (page.path === '/' && width === 360) {
        await browser.evaluate("document.querySelector('.site-menu').click()")
        if (await browser.evaluate("document.querySelector('.site-menu').getAttribute('aria-expanded')") !== 'true') throw Error('Menu did not open')
        await browser.evaluate("document.querySelector('.site-header').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")
        if (await browser.evaluate("document.querySelector('.site-menu').getAttribute('aria-expanded')") !== 'false') throw Error('Menu did not close')
      }
      if (['/', '/work', '/work/sem-lang', '/work/zix-cli', '/about/principles'].includes(page.path) && width !== 768) {
        const size = object((await browser.call('Page.getLayoutMetrics')).cssContentSize)
        if (typeof size.height !== 'number' || size.height < 1 || size.height > 12000) throw Error('Screenshot height exceeds the review budget')
        const shot = await browser.call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true,
          clip: { x: 0, y: 0, width, height: size.height, scale: 1 } })
        if (typeof shot.data !== 'string') throw Error('Missing screenshot')
        writeFileSync(`browser-results/${locale}-${width}-${page.path.replaceAll('/', '-') || 'home'}.png`, Buffer.from(shot.data, 'base64'))
      }
      results.push({ locale, width, path, ...result })
      writeFileSync('browser-results/progress.json', JSON.stringify(results, null, 2)+'\n')
    }
  }
  if (browser.errors.length) throw Error(browser.errors.join('; '))
  writeFileSync('browser-results/acceptance.json', JSON.stringify({ conditions: results.length, results }, null, 2)+'\n')
  console.log(`Rendered portfolio acceptance: ${results.length} conditions passed`)
} finally {
  await browser?.close()
  server.kill('SIGTERM'); await Promise.race([once(server, 'exit'), sleep(2000)])
  if (server.exitCode === null && server.signalCode === null) { server.kill('SIGKILL'); await once(server, 'exit') }
}
