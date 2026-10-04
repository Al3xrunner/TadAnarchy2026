import { useState } from 'react'
import { useSnapshot } from '../api/useSnapshot'
import { CATEGORY } from '../api/categories'
import MapView from '../maps/MapView'
import HexLayer from '../maps/HexLayer'
import BuildingTiles from '../maps/BuildingTiles'
import IncidentLayer from '../maps/IncidentLayer'
import LineIncidentLayer from '../maps/LineIncidentLayer'
import LineIncidentSheet from './LineIncidentSheet'
import { DETAIL_ZOOM } from '../maps/useZoom'
import IncidentSheet from './IncidentSheet'
import { useCommunityIdentity } from './useCommunityIdentity'
import './dashboard.css'


export default function Dashboard() {
  const { snap, status } = useSnapshot()
  const [filter, setFilter] = useState('all')
  const [selectedId, setSelectedId] = useState(null)
  const [sidebarTab, setSidebarTab] = useState('official')
  const [map, setMap] = useState(null)
  const communityUser = useCommunityIdentity()

  if (!snap) return <div className="dashboard center">Connecting…</div>

  const list = snap.incidents
    .filter((i) => filter === 'all' || i.cat === filter)
    .sort((a, b) => Number(!!a.related_to) - Number(!!b.related_to))      
  const selected = snap.incidents.find((i) => i.id === selectedId) ?? null
  const selectedLine = (snap.line_incidents ?? []).find((i) => i.id === selectedId) ?? null
  const related = selected ? snap.incidents.find((x) => x.id === selected.related_to) ?? null : null
  const red = snap.incidents.filter((i) => i.level === 2 && !i.related_to)  
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
            comments={snap.recent_comments ?? []} user={communityUser}
              onClose={() => setSelectedId(null)} />
          )}

        {selectedLine && <LineIncidentSheet docked incident={selectedLine} simT={snap.sim_t} onClose={() => setSelectedId(null)} />}

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

        {(snap.line_incidents ?? []).length > 0 && <h3>Public transport</h3>}
        {(snap.line_incidents ?? []).map((i) => (
          <div key={i.id} className={`card level${i.level} ${i.id === selectedId ? 'sel' : ''}`} onClick={() => focus(i)}>
            <span className="line-badge" style={{ background: i.color }}>{i.line}</span>
            <span className={`chip ${i.confidence}`}>{i.label}</span>
            <div className="muted">{i.devices} passengers · since {i.first_clock}</div>
          </div>
        ))}

        <div className="sidebar-tabs" role="tablist" aria-label="Sidebar updates">
          <button
            aria-selected={sidebarTab === 'official'}
            className={sidebarTab === 'official' ? 'active' : ''}
            onClick={() => setSidebarTab('official')}
            role="tab"
          >Official notices</button>
          <button
            aria-selected={sidebarTab === 'community'}
            className={sidebarTab === 'community' ? 'active' : ''}
            onClick={() => setSidebarTab('community')}
            role="tab"
          >Community updates</button>
        </div>
        {sidebarTab === 'official' ? (
          <section role="tabpanel" aria-label="Official notices">
            {snap.notices.length === 0 && <p className="muted">No official notices.</p>}
            {snap.notices.map((n) => <div key={n.id} className="notice"><b>{n.source}</b> · {n.title}</div>)}
          </section>
        ) : (
          <section role="tabpanel" aria-label="Community updates">
            <h3>Live City Feed</h3>
            {(snap.recent_comments ?? []).slice().reverse().map((comment) => (
              <button
                className="feed-comment"
                key={comment.id}
                onClick={() => {
                  const incident = snap.incidents.find((item) => item.id === comment.incident_id)
                  if (incident) focus(incident)
                }}
              >
                <span><time>{comment.timestamp}</time> · {comment.user} ({comment.district})</span>
                <b>{comment.text}</b>
              </button>
            ))}
            {(snap.recent_comments ?? []).length === 0 && (
              <p className="muted">No community updates yet. Open an incident to post one.</p>
            )}
          </section>
        )}
      </aside>

      <main>
        <MapView onReady={setMap}>
          <HexLayer cells={snap.cells} category={filter} minDevices={3}
            onSelectCell={(cellId) => {
              const incident = list.find((item) => item.cells8?.includes(cellId))
              if (incident) focus(incident)
            }} />
          <BuildingTiles incidents={snap.incidents} onPick={() => {}} />
          <LineIncidentLayer incidents={snap.line_incidents ?? []} selectedId={selectedId} onSelect={focus} />
          <IncidentLayer incidents={list} notices={snap.notices} selectedId={selectedId} onSelect={focus} />
        </MapView>
      </main>
    </div>
  )
}
