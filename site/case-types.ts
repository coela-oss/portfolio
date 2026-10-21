// SPDX-License-Identifier: MIT
import type { Link } from './types'
export interface CaseStory {
  purpose: string
  contribution: string
  result: string
  flowTitle: string
  flow: { title: string; text: string }[]
  decisions: { choice: string; reason: string; scope: string }[]
  actions: Link[]
}
