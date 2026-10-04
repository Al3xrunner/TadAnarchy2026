import { createContext, useContext, useEffect, useState } from 'react'

const Ctx = createContext({ snap: null, status: 'connecting' })

export function SnapshotProvider({ children }) {
  const [state, setState] = useState({ snap: null, status: 'connecting' })
  useEffect(() => {
    const es = new EventSource('/api/stream')
    es.onmessage = (e) => setState({ snap: JSON.parse(e.data), status: 'live' })
    es.onerror = () => setState((s) => ({ ...s, status: 'lost' }))   
    return () => es.close()
  }, [])
  return <Ctx.Provider value={state}>{children}</Ctx.Provider>
}

export const useSnapshot = () => useContext(Ctx)
