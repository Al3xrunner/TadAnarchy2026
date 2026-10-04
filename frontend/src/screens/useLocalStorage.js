import { useState } from 'react'

export function useLocalStorage(key, initial) {
  const [value, setValue] = useState(() => {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : initial } catch { return initial }
  })
  const set = (v) => { setValue(v); localStorage.setItem(key, JSON.stringify(v)) }
  return [value, set]
}
