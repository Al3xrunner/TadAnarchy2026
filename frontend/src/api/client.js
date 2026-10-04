export function deviceId() {
  let id = localStorage.getItem('device_id')
  if (!id) {
    id = globalThis.crypto?.randomUUID?.() ?? `d-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem('device_id', id)
  }
  return id
}

export async function postReport({ category, kind = 'problem', lat, lng, text }) {
  try {
    const r = await fetch('/api/reports', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, kind, lat, lng, text, device_id: deviceId() }),
    })
    return await r.json()
  } catch {
    return { accepted: false, reason: 'network' }
  }
}

export async function postComment({ incident_id, user, text }) {
  const response = await fetch('/api/comments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id, user, text }),
  })
  const result = await response.json()
  if (!response.ok) {
    throw new Error(result.error ?? `Could not post update (${response.status}).`)
  }
  return result
}

export async function geocode(q) {
  try {
    const r = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`)
    return r.ok ? await r.json() : []
  } catch {
    return []
  }
}

const cache = new Map()
export function staticJson(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(`/data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`missing /data/${path}`)
      return r.json()
    }))
  }
  return cache.get(path)
}
export async function director(path, body) {
  const r = await fetch(`/api/director/${path}`, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json', 'X-Director-Token': localStorage.getItem('director_token') ?? '' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json()
}

export async function getJson(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status} ${url}`)
  return r.json()
}