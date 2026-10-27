import contactConfig from './contact-form.config.json'
import consentConfig from './consent.config.json'
import type { ModuleOptions as ContactOptions } from '@nuxtjp/contact-form'
import siteBranding from './branding'
import sitePages from './site/module'
import content from './site/content.json'
import { organizationSite } from '@nuxtjp/localized-site/organization'
const requestedSite = process.env.SITE_ID
if (requestedSite !== content.siteId) throw new Error('This repository builds only the Coela portfolio')
const shared = organizationSite(import.meta.url, requestedSite, { theme: 'coela', scope: 'portfolio' })
export default defineNuxtConfig({ ...shared, modules: [...shared.modules, siteBranding, sitePages, ['@nuxtjp/localized-site/consent', { ...consentConfig, defaultLocale: content.defaultLocale }], '@nuxtjp/contact-form'], contactForm: contactConfig as ContactOptions })
