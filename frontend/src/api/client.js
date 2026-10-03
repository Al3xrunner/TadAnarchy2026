export function deviceId() {
  let id = localStorage.getItem('device_id')
  if (!id) {
    // crypto.randomUUID only exists on https:// or localhost; phones on http://192.168... need the fallback
    id = globalThis.crypto?.randomUUID?.() ?? `d-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem('device_id', id)
  }
  return id
}

/** POST /api/reports -> { accepted, reason, nearby_devices } */
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

/** GET /api/geocode?q= -> [{ label, lat, lng, cell10 }] */
export async function geocode(q) {
  try {
    const r = await fetch(`/api/geocode?q=${encodeURIComponent(q)}`)
    return r.ok ? await r.json() : []
  } catch {
    return []
  }
}

const cache = new Map()
/** Static files from the data pack (frontend/public/data), fetched once per page load. */
export function staticJson(path) {
  if (!cache.has(path)) {
    cache.set(path, fetch(`/data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`missing /data/${path}`)
      return r.json()
    }))
  }
  return cache.get(path)
}
