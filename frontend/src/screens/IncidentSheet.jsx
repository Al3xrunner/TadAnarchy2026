import { CATEGORY } from '../api/categories'

const FACILITY_PL = {
  nursery: 'żłobek', kindergarten: 'przedszkole', primary_school: 'szkoła', secondary_school: 'szkoła',
  school_other: 'szkoła', hospital: 'szpital', clinic: 'przychodnia', nursing_home: 'DPS',
}

/** Bottom sheet with everything about one incident. Pass the incident from the latest snapshot so it updates live. */
export default function IncidentSheet({ incident: i, simT, home, related, docked, onClose, onMeToo, onFine }) {
  const cat = CATEGORY[i.cat]
  const minutes = Math.max(0, Math.round((simT - i.first_t) / 60))
  const affected = home ? i.footprint_cells10.includes(home.cell10) : null
  const official = i.sources.find((s) => s.kind === 'official')

  return (
    <div className={docked ? 'panel' : 'sheet'}>
      <button className="close" onClick={onClose} aria-label="Close">×</button>
      <h2 style={{ color: cat.color }}>{cat.pl} · {i.district}</h2>
      <span className={`chip ${i.confidence}`}>{i.label}</span>
      {i.status === 'resolving' && <span className="chip">resolving</span>}

      <p><b>{i.devices}</b> neighbours reported · first {i.first_clock} ({minutes} min ago)</p>
      <p>Affects at least <b>{i.residents_at_least.toLocaleString('pl-PL')}</b> residents{i.approximate ? ' (approximate area)' : ''}</p>
      {i.streets.length > 0 && <p className="muted">Streets: {i.streets.slice(0, 4).join(', ')}</p>}
      {i.cause && <p>Possible cause: {i.cause}</p>}
      {official && (
        <p className="official">{official.source}: {official.title}
          {official.url && <> · <a href={official.url} target="_blank" rel="noreferrer">source</a></>}</p>
      )}
      {related && <p className="note">Probably part of the nearby {CATEGORY[related.cat].en.toLowerCase()} incident ({related.devices} reports).</p>}
      {i.wider_than_official && <p className="note">Residents report a wider area than the official notice.</p>}
      {i.facilities_total > 0 && (
        <p className="muted">Inside: {i.facilities.slice(0, 3).map((f) => `${f.name} (${FACILITY_PL[f.type] ?? f.type})`).join(', ')}
          {i.facilities_total > 3 ? ` +${i.facilities_total - 3}` : ''}</p>
      )}
      {affected != null && (
        <p className={affected ? 'warn' : 'ok'}>{affected ? 'Your address is inside this area.' : 'Your address is outside this area.'}</p>
      )}
      {cat.phone && <p className="muted">Not on the list? Call <a href={`tel:${cat.phone}`}>{cat.phone}</a> ({cat.phoneLabel})</p>}

      {(onMeToo || onFine) && (
        <div className="row">
          {onMeToo && <button className="primary" onClick={onMeToo}>Me too</button>}
          {onFine && <button onClick={onFine}>Works for me</button>}
        </div>
      )}
    </div>
  )
}
