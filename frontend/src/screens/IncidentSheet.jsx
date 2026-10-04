import { useState } from 'react'
import { postComment } from '../api/client'
import { CATEGORY } from '../api/categories'

const FACILITY_PL = {
  nursery: 'żłobek', kindergarten: 'przedszkole', primary_school: 'szkoła', secondary_school: 'szkoła',
  school_other: 'szkoła', hospital: 'szpital', clinic: 'przychodnia', nursing_home: 'DPS',
}

const QUICK_UPDATES = ['🔥 Still down', '⚡ Power back', '🚚 Water truck spotted', '📞 Called 993']

function IncidentChat({ incident, comments, user }) {
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [posting, setPosting] = useState(false)
  const thread = comments.filter((comment) => comment.incident_id === incident.id)

  async function post(textToPost) {
    if (!textToPost.trim() || posting) return
    setPosting(true)
    setError('')
    try {
      await postComment({ incident_id: incident.id, user, text: textToPost.trim() })
      setText('')
    } catch (postError) {
      setError(postError.message)
    } finally {
      setPosting(false)
    }
  }

  return (
    <section className="incident-chat" aria-label="Incident community updates">
      <h3>Community updates</h3>
      <div className="incident-chat__comments" aria-live="polite">
        {thread.length === 0
          ? <p className="muted">No updates yet. Be the first to share what you see.</p>
          : thread.slice(-20).map((comment) => (
            <article className="incident-chat__comment" key={comment.id}>
              <b>{comment.user}</b><time>{comment.timestamp}</time>
              <p>{comment.text}</p>
            </article>
          ))}
      </div>
      <div className="incident-chat__quick">
        {QUICK_UPDATES.map((update) => (
          <button disabled={posting} key={update} onClick={() => post(update)}>{update}</button>
        ))}
      </div>
      <form onSubmit={(event) => { event.preventDefault(); post(text) }}>
        <input
          aria-label="Post an incident update"
          maxLength={500}
          onChange={(event) => setText(event.target.value)}
          placeholder="What are you seeing?"
          value={text}
        />
        <button disabled={posting || !text.trim()} type="submit">Post update</button>
      </form>
      {error && <p className="incident-chat__error" role="alert">{error}</p>}
    </section>
  )
}

export default function IncidentSheet({
  incident: i, simT, home, related, docked, comments = [], user, onClose, onMeToo, onFine,
}) {
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
      <IncidentChat incident={i} comments={comments} user={user} />
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
