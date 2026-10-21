import { fileURLToPath } from 'node:url'
import type { NuxtModule } from 'nuxt/schema'

const siteBranding: NuxtModule = (_options, nuxt) => {
  if (process.env.SITE_ID !== 'coela') return
  nuxt.options.app.head.link ??= []
  nuxt.options.app.head.link.push(
    { rel: 'icon', type: 'image/png', href: '/brand/icon.png' },
    { rel: 'apple-touch-icon', href: '/brand/icon.png' }
  )
  nuxt.options.app.head.meta ??= []
  nuxt.options.app.head.meta.push({ name: 'theme-color', content: '#007e78' })
}

export default siteBranding
