import { loadSiteDocuments } from '@nuxtjp/localized-site/documents'
export default await loadSiteDocuments(new URL('./', import.meta.url))
