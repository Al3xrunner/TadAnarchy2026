import { useEffect, useState } from 'react'
import { GeoJSON } from 'react-leaflet'
import { useSnapshot } from '../api/useSnapshot'
import { fetchLive, loadLines } from '../api/transit'
import MapView from '../maps/MapView'
import LiveVehiclesLayer from '../maps/LiveVehiclesLayer'
import LineIncidentLayer from '../maps/LineIncidentLayer'
import LineIncidentSheet from './LineIncidentSheet'
import './transit.css'

const STATUS = { live: 'Live ZTP data', cache: 'Last saved ZTP data (offline)', offline: 'Recorded ZTP feed',
                 error: 'No live ZTP data', disabled: 'Live data off (TRANSIT_LIVE=0)', starting: 'Connecting to ZTP…' }

export default function Transit() {
  const { snap } = useSnapshot()
  const [live, setLive] = useState({ status: 'starting', vehicles: [], alerts: [] })
  const [lines, setLines] = useState(null)
  const [filter, setFilter] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [map, setMap] = useState(null)

  useEffect(() => { loadLines().then(setLines) }, [])
  useEffect(() => {
    const tick = () => fetchLive().then(setLive)
    tick()
    const t = setInterval(tick, 10000)            
    return () => clearInterval(t)
  }, [])

  const f = filter.trim()
  const crowd = (snap?.line_incidents ?? []).filter((i) => !f || i.line === f)
  const alerts = live.alerts.filter((a) => !f || a.lines.includes(f))
  const selected = crowd.find((i) => i.id === selectedId) ?? null
  const trams = live.vehicles.filter((v) => v.mode === 'tram').length

  function focus(i) {
    setSelectedId(i.id)
    map?.flyTo([i.center.lat, i.center.lng], 14, { duration: 0.8 })
  }

  return (
    <div className="transit">
      <aside>
        <h1>Komunikacja · Public transport</h1>
        <p><span className={`chip ${live.status}`}>{STATUS[live.status] ?? live.status}</span>
          {live.updated_at && <span className="muted"> {new Date(live.updated_at * 1000).toLocaleTimeString()}</span>}</p>
        <div className="kpis">
          <div><b>{trams}</b>trams live</div>
          <div><b>{live.vehicles.length - trams}</b>buses live</div>
          <div><b>{crowd.filter((i) => i.level === 2).length}</b>lines with problems</div>
          <div><b>{live.alerts.length}</b>ZTP alerts</div>
        </div>
        <input placeholder="Line, e.g. 52" value={filter} onChange={(e) => setFilter(e.target.value)} />

        {selected && <LineIncidentSheet docked incident={selected} simT={snap.sim_t} onClose={() => setSelectedId(null)} />}

        <h3>Reported by passengers</h3>
        {crowd.length === 0 && <p className="muted">No problems reported right now.</p>}
        {crowd.map((i) => (
          <div key={i.id} className={`card level${i.level} ${i.id === selectedId ? 'sel' : ''}`} onClick={() => focus(i)}>
            <span className="line-badge" style={{ background: i.color }}>{i.line}</span>
            <span className={`chip ${i.confidence}`}>{i.label}</span>
            <div className="muted">{i.devices} passengers · since {i.first_clock}
              {i.stops[0] && ` · ${i.stops.slice(0, 2).map((s) => s.name).join(', ')}`}</div>
          </div>
        ))}

        <h3>Official ZTP alerts</h3>
        {alerts.length === 0 && <p className="muted">None{live.status === 'error' ? ' (no connection)' : ''}.</p>}
        {alerts.slice(0, 30).map((a) => (
          <div key={`${a.mode}-${a.id}`} className="alert">
            <div>{a.lines.slice(0, 8).map((l) => <span key={l} className="line-badge small"
              style={{ background: lines?.colors.get(l) ?? '#5c6b7a' }}>{l}</span>)}</div>
            <b>{a.header}</b>
            {a.description && <div className="muted">{a.description.slice(0, 220)}{a.description.length > 220 ? '…' : ''}</div>}
          </div>
        ))}
      </aside>
      <main>
        <MapView onReady={setMap}>
          {lines && <GeoJSON key={`tram-${f}`} data={lines.tram} interactive={false}
            style={(ft) => ({ color: ft.properties.color, weight: 2, opacity: f && ft.properties.line !== f ? 0.12 : 0.55 })} />}
          <LineIncidentLayer incidents={crowd} selectedId={selectedId} onSelect={focus} />
          <LiveVehiclesLayer vehicles={live.vehicles} colors={lines?.colors} filter={f} />
        </MapView>
      </main>
    </div>
  )
}
