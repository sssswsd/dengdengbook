import { create } from 'zustand'
import type { LearnState, Segment } from './api'

type Store = {
  sid: string | null
  page: Segment | null
  history: Segment[]
  action: string
  reason: string
  state: LearnState | null
  set: (p: Partial<Store>) => void
}

export const useStore = create<Store>((set) => ({
  sid: null,
  page: null,
  history: [],
  action: 'continue',
  reason: '',
  state: null,
  set: (p) => set(p),
}))
