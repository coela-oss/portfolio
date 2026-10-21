import type { Link } from './types'

export type PreviewKind = 'workspace' | 'directory' | 'meaning' | 'code' | 'portfolio' | 'business' | 'trust' | 'plan' | 'environment'
export interface Experience {
  category: string
  primary: Link
  secondary: Link
  pathsTitle: string
  paths: Link[]
  preview: {
    kind: PreviewKind
    label: string
    title: string
    rows: { label: string; detail: string }[]
    outcome: string
  }
}
