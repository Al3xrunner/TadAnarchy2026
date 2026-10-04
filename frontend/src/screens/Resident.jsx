import { useState } from 'react'
import { useSnapshot } from '../api/useSnapshot'
import { postReport } from '../api/client'
import { CATEGORY, REPORTABLE } from '../api/categories'
import MapView from '../maps/MapView'
import HexLayer from '../maps/HexLayer'
import BuildingTiles from '../maps/BuildingTiles'
import IncidentLayer from '../maps/IncidentLayer'
import { DETAIL_ZOOM } from '../maps/useZoom'
import IncidentSheet from './IncidentSheet'
import AddressSearch from './AddressSearch'
import { useLocalStorage } from './useLocalStorage'
import './resident.css'

const REASONS = {
  duplicate: 'You already reported this here.', rate_limited: 'Slow down – too many reports.',
  outside_city: 'Only inside Kraków.', engine_busy: 'Server busy, try again.', network: 'No connection.',
}

export default function Resident() {
  const { snap, status } = useSnapshot()
  const [map, setMap] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [mode, setMode] = useState('browse')          
  const [message, setMessage] = useState('')
  const [home, setHome] = useLocalStorage('home', null)
  const [building, setBuilding] = useState(null)

  if (!snap) return <div className="phone center">Łączenie… / Connecting…</div>

  const selected = snap.incidents.find((i) => i.id === selectedId) ?? null   // select by id: updates live
  const related = selected ? snap.incidents.find((x) => x.id === selected.related_to) ?? null : null
  const mine = home ? snap.incidents.find((i) => i.footprint_cells10.includes(home.cell10)) : undefined

  async function send(category, kind = 'problem', at) {
    const where = at ?? map?.getCenter()
    if (!where) return
    const r = await postReport({ category, kind, lat: where.lat, lng: where.lng })
    setMessage(!r.accepted ? (REASONS[r.reason] ?? 'Could not send.')
      : kind === 'fine' ? 'Thanks – noted that it works for you.'
      : `You and ${Math.max(0, (r.nearby_devices ?? 1) - 1)} others nearby report: ${CATEGORY[category].en}.`)
    setMode('done')
  }

  function focus(i) {
    setSelectedId(i.id)
    if (!map) return
    const z = Math.max(map.getZoom(), DETAIL_ZOOM)
    const target = map.unproject(map.project([i.center.lat, i.center.lng], z).add([0, map.getSize().y * 0.28]), z)
    map.flyTo(target, z, { duration: 0.8 })
  }

  const meTooAt = (i) => (home && i.footprint_cells10.includes(home.cell10) ? home : i.center)

  return (
    <div className="phone">
      <header>
        <b>Kraków Live</b>
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
          <HexLayer cells={snap.cells} category="all" />
          <BuildingTiles incidents={snap.incidents} onPick={setBuilding} />
          <IncidentLayer incidents={snap.incidents} notices={snap.notices} selectedId={selectedId} onSelect={focus} />
        </MapView>
        {mode === 'pick' && <div className="crosshair" />}
        {building && mode === 'browse' && !selected && (
          <div className="toast" onClick={() => setBuilding(null)}>
            {building.address ?? 'Building'} · {building.type ?? ''}
            {building.residential ? ` · ~${building.residents_est} residents` : ''}
          </div>
        )}
      </div>

      {mode === 'browse' && !selected && (
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
                onClick={() => (c === 'danger' ? setMode('danger') : send(c))}>
                <b>{CATEGORY[c].pl}</b><small>{CATEGORY[c].en}</small>
              </button>
            ))}
          </div>
          <button className="wide" onClick={() => setMode('browse')}>Anuluj · Cancel</button>
        </div>
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
          onClose={() => setSelectedId(null)}
          onMeToo={() => send(selected.cat, 'problem', meTooAt(selected))}
          onFine={() => send(selected.cat, 'fine', meTooAt(selected))} />
      )}
    </div>
  )
}
