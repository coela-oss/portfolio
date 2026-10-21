// SPDX-License-Identifier: MIT
export interface WorkSection { title: string; text: string }
export interface Work {
  id: string; path: string; title: string; headline: string; summary: string
  image: string; alt: string; category: string; stack: string[]
  live: string; source: string; sections: WorkSection[]
}
