import { useEffect, useState } from 'react'
import { distanceM, loadStops, platformFor } from '../api/transit'

export default function TransitReport({ at, onSend, onCancel }) {
  const [stops, setStops] = useState(null)
  const [stop, setStop] = useState(null)
  useEffect(() => { loadStops().then(setStops) }, [])

  if (!stops) return <div className="sheet"><p>Loading stops…</p></div>
  const near = stops.map((s) => ({ ...s, d: distanceM(s, at) })).sort((a, b) => a.d - b.d).slice(0, 6)

  if (!stop) {
    return (
      <div className="sheet">
        <p>Przystanek · Which stop are you at?</p>
        {near.map((s) => (
          <button key={s.name} className="stop" onClick={() => setStop(s)}>
            <b>{s.name}</b> <small>{s.d} m · {s.lines.slice(0, 8).join(', ')}{s.lines.length > 8 ? '…' : ''}</small>
          </button>
        ))}
        <button className="wide" onClick={onCancel}>Anuluj · Cancel</button>
      </div>
    )
  }
  return (
    <div className="sheet">
      <p><b>{stop.name}</b> – która linia nie przyjeżdża? · Which line isn't coming?</p>
      <div className="lines">
        {stop.lines.map((l) => (
          <button key={l} onClick={() => { const p = platformFor(stop, l, at); onSend({ line: l, stop_id: p.stop_id, lat: p.lat, lng: p.lng }) }}>{l}</button>
        ))}
      </div>
      <button className="wide" onClick={() => setStop(null)}>← Inny przystanek · Other stop</button>
    </div>
  )
}
