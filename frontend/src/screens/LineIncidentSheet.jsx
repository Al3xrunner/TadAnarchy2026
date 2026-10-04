export default function LineIncidentSheet({ incident: i, simT, docked, related, onClose, onMeToo, onFine }) {
  const minutes = Math.max(0, Math.round((simT - i.first_t) / 60))
  const official = i.sources.find((s) => s.kind === 'official')
  return (
    <div className={docked ? 'panel' : 'sheet'}>
      <button className="close" onClick={onClose} aria-label="Close">×</button>
      <h2><span className="line-badge" style={{ background: i.color }}>{i.line}</span>
        {i.mode === 'tram' ? 'Tramwaj' : 'Autobus'} {i.line} – utrudnienia</h2>
      <span className={`chip ${i.confidence}`}>{i.label}</span>
      {i.status === 'resolving' && <span className="chip">resolving</span>}
      <p><b>{i.devices}</b> passengers reported · first {i.first_clock} ({minutes} min ago)</p>
      {i.stops.length > 0 && <p className="muted">At stops: {i.stops.slice(0, 5).map((s) => `${s.name} (${s.devices})`).join(', ')}</p>}
      {i.cause && <p>Possible cause: {i.cause}</p>}
      {official && <p className="official">{official.source}: {official.title}</p>}
      {related && <p className="note">Probably caused by the nearby {related.cat} incident in {related.district}.</p>}
      {(onMeToo || onFine) && (
        <div className="row">
          {onMeToo && <button className="primary" onClick={onMeToo}>My {i.mode === 'tram' ? 'tram' : 'bus'} isn't coming either</button>}
          {onFine && <button onClick={onFine}>Running for me</button>}
        </div>
      )}
    </div>
  )
}
