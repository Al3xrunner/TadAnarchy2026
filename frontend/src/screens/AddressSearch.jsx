import { useEffect, useState } from 'react'
import { geocode } from '../api/client'

export default function AddressSearch({ home, onPick }) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState([])

  useEffect(() => {
    if (q.trim().length < 3) return
    const t = setTimeout(() => { geocode(q).then(setHits) }, 300)  
    return () => clearTimeout(t)
  }, [q])

  if (home) {
    return <p className="home">Mój adres: <b>{home.label}</b> <button className="link" onClick={() => onPick(null)}>zmień</button></p>
  }
  return (
    <div className="search">
      <input placeholder="Mój adres, np. Stachiewicza 21" value={q}
        onChange={(e) => { setQ(e.target.value); if (e.target.value.trim().length < 3) setHits([]) }} />
      {hits.length > 0 && (
        <div className="hits">
          {hits.map((h) => (
            <button key={`${h.label}-${h.lat}`} onClick={() => { onPick(h); setQ(''); setHits([]) }}>{h.label}</button>
          ))}
        </div>
      )}
    </div>
  )
}
