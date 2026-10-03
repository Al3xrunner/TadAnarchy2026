import { useState } from 'react'
import { useSnapshot } from '../api/useSnapshot'
import { CATEGORY } from '../api/categories'
import MapView from '../maps/MapView'
import HexLayer from '../maps/HexLayer'
import BuildingTiles from '../maps/BuildingTiles'
import IncidentLayer from '../maps/IncidentLayer'
import { DETAIL_ZOOM } from '../maps/useZoom'
import IncidentSheet from './IncidentSheet'
import './dashboard.css'

/** The city's view (laptop). Only aggregates: hexagons with >= 3 reporters, every incident, affected facilities. Route: /dashboard */
export default function Dashboard() {
  const { snap, status } = useSnapshot()
  const [filter, setFilter] = useState('all')
  const [selectedId, setSelectedId] = useState(null)
  const [map, setMap] = useState(null)

  if (!snap) return <div className="dashboard center">Connecting…</div>

  const list = snap.incidents
    .filter((i) => filter === 'all' || i.cat === filter)
    .sort((a, b) => Number(!!a.related_to) - Number(!!b.related_to))      // related ones last
  const selected = snap.incidents.find((i) => i.id === selectedId) ?? null
  const related = selected ? snap.incidents.find((x) => x.id === selected.related_to) ?? null : null
  const red = snap.incidents.filter((i) => i.level === 2 && !i.related_to)  // related ones are not double counted
  const facilities = red.reduce((n, i) => n + i.facilities_total, 0)
  const residents = red.reduce((n, i) => n + i.residents_at_least, 0)

  function focus(i) {
    setSelectedId(i.id)
    map?.flyTo([i.center.lat, i.center.lng], DETAIL_ZOOM, { duration: 0.8 })
  }

  return (
    <div className="dashboard">
      <aside>
        <h1>Kraków · crisis view <span className={`dot ${status}`} /></h1>
        <p className="muted">{snap.run.title} · sim {snap.sim_clock}</p>

        <div className="kpis">
          <div><b>{red.length}</b>confirmed incidents</div>
          <div><b>{residents.toLocaleString('pl-PL')}</b>residents affected (min.)</div>
          <div><b>{facilities}</b>vulnerable facilities</div>
          <div><b>{snap.metrics.reports_10min}</b>reports / 10 min</div>
        </div>

        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All categories</option>
          {Object.entries(CATEGORY).map(([k, v]) => <option key={k} value={k}>{v.en}</option>)}
        </select>

        {selected && (
          <IncidentSheet docked incident={selected} simT={snap.sim_t} home={null} related={related}
            onClose={() => setSelectedId(null)} />
        )}

        {list.length === 0 && <p className="muted">No incidents right now.</p>}
        {list.map((i) => (
          <div key={i.id} onClick={() => focus(i)}
            className={`card level${i.level} ${i.id === selectedId ? 'sel' : ''} ${i.related_to ? 'related' : ''}`}>
            <div>
              <b style={{ color: CATEGORY[i.cat].color }}>{CATEGORY[i.cat].en}</b> · {i.district}
              <span className={`chip ${i.confidence}`}>{i.label}</span>
            </div>
            <div className="muted">
              {i.devices} reports · ≥ {i.residents_at_least.toLocaleString('pl-PL')} residents · since {i.first_clock}
              {i.facilities_total > 0 && ` · ${i.facilities_total} facilities`}
            </div>
            {i.related_to && <div className="note">probably part of {i.related_to}</div>}
          </div>
        ))}

        {snap.notices.length > 0 && (
          <>
            <h3>Official notices</h3>
            {snap.notices.map((n) => <div key={n.id} className="notice"><b>{n.source}</b> · {n.title}</div>)}
          </>
        )}
      </aside>

      <main>
        <MapView onReady={setMap}>
          <HexLayer cells={snap.cells} category={filter} minDevices={3} />
          <BuildingTiles incidents={snap.incidents} onPick={() => {}} />
          <IncidentLayer incidents={list} notices={snap.notices} selectedId={selectedId} onSelect={focus} />
        </MapView>
      </main>
    </div>
  )
}
