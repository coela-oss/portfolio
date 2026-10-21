export type Locale = 'ja' | 'en'
export interface Link { title: string; href: string; summary?: string; icon?: string }
export interface Section { title: string; text: string; links?: Link[]; code?: string }
export interface Page {
  path: string; title: string; summary: string; label?: string
  kind?: 'home' | 'catalog' | 'journal' | 'article' | 'page'
  sections: Section[]; category?: string; status?: 'draft' | 'published'
}
export interface Resource extends Link { category: string; license?: string }
export interface SiteContent {
  brand: string; caption: string; origin: string; locale: Locale; accent: string; icon: string
  navigation: Link[]; pages: Page[]; resources: Resource[]
  secondaryAction?: Link
}
