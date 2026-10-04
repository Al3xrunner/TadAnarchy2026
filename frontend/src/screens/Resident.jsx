import { useEffect, useState } from 'react'
import { useSnapshot } from '../api/useSnapshot'
import { postReport } from '../api/client'
import { CATEGORY, REPORTABLE } from '../api/categories'
import MapView from '../maps/MapView'
import HexLayer from '../maps/HexLayer'
import BuildingTiles from '../maps/BuildingTiles'
import IncidentLayer from '../maps/IncidentLayer'
import LineIncidentLayer from '../maps/LineIncidentLayer'
import { DETAIL_ZOOM } from '../maps/useZoom'
import IncidentSheet from './IncidentSheet'
import LineIncidentSheet from './LineIncidentSheet'
import TransitReport from './TransitReport'
import AddressSearch from './AddressSearch'
import { useLocalStorage } from './useLocalStorage'
import { useCommunityIdentity } from './useCommunityIdentity'
import './resident.css'

const REASONS = {
  duplicate: 'You already reported this here.', rate_limited: 'Slow down – too many reports.',
  outside_city: 'Only inside Kraków.', engine_busy: 'Server busy, try again.', network: 'No connection.',
  line_required: 'Choose a line.',
}

export default function Resident() {
  const { snap, status } = useSnapshot()
  const [map, setMap] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [lineId, setLineId] = useState(null)
  const [mode, setMode] = useState('browse')          
  const [message, setMessage] = useState('')
  const [home, setHome] = useLocalStorage('home', null)
  const communityUser = useCommunityIdentity(home)
  const [building, setBuilding] = useState(null)
  const [dismissedHomeToastKey, setDismissedHomeToastKey] = useState(null)
  const homeIncident = snap && home
    ? snap.incidents.find((i) => i.level >= 2 && i.footprint_cells10.includes(home.cell10)) ?? null
    : null
  const homeToastKey = homeIncident ? `${home?.cell10}:${homeIncident.id}` : null

  useEffect(() => {
    if (!homeToastKey) {
      return
    }

    const timeout = window.setTimeout(() => setDismissedHomeToastKey(homeToastKey), 6000)
    return () => window.clearTimeout(timeout)
  }, [homeToastKey])

  if (!snap) return <div className="phone center">Łączenie… / Connecting…</div>

  const lineIncidents = snap.line_incidents ?? []
  const selected = snap.incidents.find((i) => i.id === selectedId) ?? null   
  const selectedLine = lineIncidents.find((i) => i.id === lineId) ?? null
  const related = selected ? snap.incidents.find((x) => x.id === selected.related_to) ?? null : null
  const lineRelated = selectedLine ? snap.incidents.find((x) => x.id === selectedLine.related_to) ?? null : null
  const mine = home ? snap.incidents.find((i) => i.footprint_cells10.includes(home.cell10)) : undefined
  const open = selected || selectedLine

  async function send(category, kind = 'problem', at, extra = {}) {
    const where = at ?? map?.getCenter()
    if (!where) return
    const r = await postReport({ category, kind, lat: where.lat, lng: where.lng, ...extra })
    const what = extra.line ? `line ${extra.line}` : CATEGORY[category].en
    setMessage(!r.accepted ? (REASONS[r.reason] ?? 'Could not send.')
      : kind === 'fine' ? 'Thanks – noted that it works for you.'
      : `You and ${Math.max(0, (r.nearby_devices ?? 1) - 1)} others nearby report: ${what}.`)
    setMode('done')
  }

  function flyTo(center, minZoom) {
    if (!map) return
    const z = Math.max(map.getZoom(), minZoom)
    const target = map.unproject(map.project([center.lat, center.lng], z).add([0, map.getSize().y * 0.28]), z)
    map.flyTo(target, z, { duration: 0.8 })
  }

  function focus(i) {
    setLineId(null)
    setSelectedId(i.id)
    flyTo(i.center, DETAIL_ZOOM)
  }

  function focusLine(i) {
    setSelectedId(null)
    setLineId(i.id)
    flyTo(i.center, 13)
  }

  const meTooAt = (i) => (home && i.footprint_cells10.includes(home.cell10) ? home : i.center)
  const lineExtra = (i) => ({ line: i.line, stop_id: i.stops[0]?.stop_id })
  const lineStop = (i) => i.stops[0] ?? i.center

  return (
    <div className="phone">
      <header>
        <b>Kraków Live</b>
        <a className="muted" href="/transit">Komunikacja</a>
        <span className="clock">{snap.sim_clock}</span>
        <span className={`dot ${status}`} title={status} />
      </header>

      {mine && (
        <button className="banner" onClick={() => focus(mine)}>
          Your address is inside: <b>{CATEGORY[mine.cat].en}</b> · {mine.label}
        </button>
      )}

      <div className="map-wrap">
        <MapView onReady={setMap}>
          <HexLayer
            cells={snap.cells}
            category="all"
            onSelectCell={(cellId) => {
              const incident = snap.incidents.find((item) => item.cells8?.includes(cellId))
              if (incident) focus(incident)
            }}
          />
          <BuildingTiles incidents={snap.incidents} onPick={setBuilding} />
          <LineIncidentLayer incidents={lineIncidents} selectedId={lineId} onSelect={focusLine} />
          <IncidentLayer incidents={snap.incidents} notices={snap.notices} selectedId={selectedId} onSelect={focus} />
        </MapView>
        {(mode === 'pick' || mode === 'transit') && <div className="crosshair" />}
        {homeToastKey && dismissedHomeToastKey !== homeToastKey && homeIncident && (
          <div className="address-toast" role="status" aria-live="polite">
            <span aria-hidden="true">!</span>
            <span className="copy">
              <b>Red alert near your address</b>
              <br />{CATEGORY[homeIncident.cat].en} · {home.label}
            </span>
            <button
              aria-label="Dismiss address alert"
              onClick={() => setDismissedHomeToastKey(homeToastKey)}
            >
              ×
            </button>
          </div>
        )}
        {building && mode === 'browse' && !open && (
          <div className="toast" onClick={() => setBuilding(null)}>
            {building.address ?? 'Building'} · {building.type ?? ''}
            {building.residential ? ` · ~${building.residents_est} residents` : ''}
          </div>
        )}
      </div>

      {mode === 'browse' && !open && (
        <div className="bottom">
          <AddressSearch home={home} onPick={setHome} />
          <button className="primary wide" onClick={() => { setMode('pick'); setBuilding(null) }}>Zgłoś problem · Report</button>
        </div>
      )}

      {mode === 'pick' && (
        <div className="sheet">
          <p>Przesuń mapę, aby krzyżyk wskazał miejsce · Move the map so the cross marks the place:</p>
          <div className="grid">
            {REPORTABLE.map((c) => (
              <button key={c} style={{ borderColor: CATEGORY[c].color }}
                onClick={() => (c === 'danger' ? setMode('danger') : c === 'transit' ? setMode('transit') : send(c))}>
                <b>{CATEGORY[c].pl}</b><small>{CATEGORY[c].en}</small>
              </button>
            ))}
          </div>
          <button className="wide" onClick={() => setMode('browse')}>Anuluj · Cancel</button>
        </div>
      )}

      {mode === 'transit' && map && (
        <TransitReport at={map.getCenter()} onCancel={() => setMode('browse')}
          onSend={({ line, stop_id, lat, lng }) => send('transit', 'problem', { lat, lng }, { line, stop_id })} />
      )}

      {mode === 'danger' && (
        <div className="sheet danger">
          <h2>Czy ktoś jest w niebezpieczeństwie? Dzwoń teraz.</h2>
          <a className="call" href="tel:112">112 – numer alarmowy</a>
          <a className="call" href="tel:992">992 – pogotowie gazowe</a>
          <button className="wide" onClick={() => send('danger')}>Also warn neighbours</button>
          <button className="wide" onClick={() => setMode('browse')}>Cancel</button>
        </div>
      )}

      {mode === 'done' && (
        <div className="sheet">
          <p className="big">{message}</p>
          <button className="primary wide" onClick={() => setMode('browse')}>OK</button>
        </div>
      )}

      {selected && mode === 'browse' && (
        <IncidentSheet incident={selected} simT={snap.sim_t} home={home} related={related}
          comments={snap.recent_comments ?? []} user={communityUser}
          onClose={() => setSelectedId(null)}
          onMeToo={() => send(selected.cat, 'problem', meTooAt(selected))}
          onFine={() => send(selected.cat, 'fine', meTooAt(selected))} />
      )}

      {selectedLine && mode === 'browse' && (
        <LineIncidentSheet incident={selectedLine} simT={snap.sim_t} related={lineRelated}
          onClose={() => setLineId(null)}
          onMeToo={() => send('transit', 'problem', lineStop(selectedLine), lineExtra(selectedLine))}
          onFine={() => send('transit', 'fine', lineStop(selectedLine), lineExtra(selectedLine))} />
      )}
    </div>
  )
}
