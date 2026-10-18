import { useSyncExternalStore } from 'react'

export type Mode = 'light' | 'dark'
const listeners = new Set<() => void>()
const get = (): Mode => (document.documentElement.classList.contains('dark') ? 'dark' : 'light')

export function setMode(m: Mode) {
  document.documentElement.classList.toggle('dark', m === 'dark')
  try { localStorage.setItem('theme', m) } catch { /* storage blocked */ }
  listeners.forEach((l) => l())
}
export const toggleMode = () => setMode(get() === 'dark' ? 'light' : 'dark')
export const useMode = () => useSyncExternalStore((cb) => { listeners.add(cb); return () => { listeners.delete(cb) } }, get)
