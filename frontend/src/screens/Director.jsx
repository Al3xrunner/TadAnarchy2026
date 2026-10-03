import { useEffect, useState } from 'react'
import { director, getJson } from '../api/client'
import { useSnapshot } from '../api/useSnapshot'
import './director.css'

/** Runs the demo: load scenarios, change users and speed, watch detection times. Hidden during the pitch. Route: /director */
export default function Director() {
  const { snap } = useSnapshot()
  const [scenarios, setScenarios] = useState([])
  const [scenario, setScenario] = useState('heating_azory')
  const [users, setUsers] = useState(20000)
  const [seed, setSeed] = useState(42)
  const [token, setToken] = useState(localStorage.getItem('director_token') ?? '')
  const [msg, setMsg] = useState('')
  const [runs, setRuns] = useState([])

  useEffect(() => {
    director('scenarios').then(setScenarios).catch((e) => setMsg(String(e)))
    const loadRuns = () => getJson('/api/history/runs').then(setRuns).catch(() => {})
    loadRuns()
    const t = setInterval(loadRuns, 5000)
    return () => clearInterval(t)
  }, [])

  const run = (promise, ok) => promise.then(() => setMsg(ok)).catch((e) => setMsg(String(e)))

  function pick(id) {
    setScenario(id)
    const s = scenarios.find((x) => x.id === id)
    if (s) setUsers(s.recommended_users)
  }

  return (
    <div className="director">
      <h1>Director</h1>

      <div className="form">
        <label>Token
          <input type="password" value={token}
            onChange={(e) => { setToken(e.target.value); localStorage.setItem('director_token', e.target.value) }} />
        </label>
        <label>Scenario
          <select value={scenario} onChange={(e) => pick(e.target.value)}>
            {scenarios.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
          </select>
        </label>
        <label>Users: <b>{users.toLocaleString('pl-PL')}</b>
          <input type="range" min={1000} max={50000} step={1000} value={users} onChange={(e) => setUsers(+e.target.value)} />
        </label>
        <label>Seed <input type="number" value={seed} onChange={(e) => setSeed(+e.target.value)} /></label>
        <button className="primary" onClick={() => run(director('load', { scenario, users, seed }), `Loaded ${scenario}`)}>
          Load scenario
        </button>
        <div className="row">
          {[0, 1, 10, 60, 300].map((s) => (
            <button key={s} className={snap?.speed === s ? 'on' : ''}
              onClick={() => run(director('speed', { speed: s }), `Speed ${s}×`)}>
              {s === 0 ? 'Pause' : `${s}×`}
            </button>
          ))}
        </div>
        {msg && <p className="muted">{msg}</p>}
        <p><a href="/app" target="_blank">Open resident app</a> · <a href="/dashboard" target="_blank">Open dashboard</a></p>
      </div>

      {snap && (
        <div className="status">
          <p>
            <b>{snap.run.title}</b><br />
            {snap.run.users.toLocaleString('pl-PL')} users · seed {snap.run.seed} · sim {snap.sim_clock} · speed {snap.speed}× · tick {snap.metrics.tick_ms} ms
          </p>
          <table>
            <thead><tr><th>True incident</th><th>Category</th><th>Yellow after</th><th>Red after</th></tr></thead>
            <tbody>
              {Object.entries(snap.metrics.detect).map(([id, d]) => (
                <tr key={id}><td>{id}</td><td>{d.category}</td><td>{d.yellow_min ?? '–'} min</td><td>{d.red_min ?? '–'} min</td></tr>
              ))}
            </tbody>
          </table>
          <p className="muted">
            Active reports {snap.metrics.active_reports} · rejected {snap.metrics.rejected} · red false alarms {snap.metrics.false_alarms} · incidents {snap.incidents.length}
          </p>
        </div>
      )}

      <h3>Runs in the database</h3>
      <table>
        <thead><tr><th>Started</th><th>Scenario</th><th>Users</th><th>Reports stored</th></tr></thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.started_at).toLocaleTimeString()}</td><td>{r.scenario}</td>
              <td>{r.users.toLocaleString('pl-PL')}</td><td>{r.reports}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
