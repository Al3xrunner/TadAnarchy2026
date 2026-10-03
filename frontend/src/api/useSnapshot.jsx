import { createContext, useContext, useEffect, useState } from 'react'

const Ctx = createContext({ snap: null, status: 'connecting' })

/** One EventSource per browser tab. Wrap the app in <SnapshotProvider>, read with useSnapshot(). */
export function SnapshotProvider({ children }) {
  const [state, setState] = useState({ snap: null, status: 'connecting' })
  useEffect(() => {
    const es = new EventSource('/api/stream')
    es.onmessage = (e) => setState({ snap: JSON.parse(e.data), status: 'live' })
    es.onerror = () => setState((s) => ({ ...s, status: 'lost' }))   // EventSource reconnects by itself
    return () => es.close()
  }, [])
  return <Ctx.Provider value={state}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useSnapshot = () => useContext(Ctx)
