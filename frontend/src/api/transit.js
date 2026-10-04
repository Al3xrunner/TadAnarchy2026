import { staticJson } from './client'

export async function loadStops() {
  const gj = await staticJson('transit_stops.geojson')
  const groups = new Map()
  for (const f of gj.features) {
    const p = f.properties
    const [lng, lat] = f.geometry.coordinates
    const key = p.name
    if (!groups.has(key)) groups.set(key, { name: p.name, platforms: [] })
    groups.get(key).platforms.push({ stop_id: p.stop_id, lat, lng, lines: p.lines, mode: p.mode })
  }
  return [...groups.values()].map((g) => ({
    ...g,
    lat: g.platforms.reduce((s, x) => s + x.lat, 0) / g.platforms.length,
    lng: g.platforms.reduce((s, x) => s + x.lng, 0) / g.platforms.length,
    lines: [...new Set(g.platforms.flatMap((x) => x.lines))].sort((a, b) => a.length - b.length || a.localeCompare(b)),
  }))
}

export function distanceM(a, b) {
  const dx = (a.lng - b.lng) * 71500, dy = (a.lat - b.lat) * 111320
  return Math.round(Math.hypot(dx, dy))
}

export function platformFor(group, line, at) {
  const serving = group.platforms.filter((p) => p.lines.includes(line))
  return serving.sort((a, b) => distanceM(a, at) - distanceM(b, at))[0] ?? group.platforms[0]
}

export async function loadLines() {
  const [tram, bus] = await Promise.all([staticJson('tram_lines.geojson'), staticJson('bus_lines.geojson')])
  const shapes = new Map(), colors = new Map(), modes = new Map()
  for (const [gj, mode] of [[tram, 'tram'], [bus, 'bus']]) {
    for (const f of gj.features) {
      const l = f.properties.line
      if (!shapes.has(l)) shapes.set(l, [])
      shapes.get(l).push(f)
      colors.set(l, mode === 'tram' ? f.properties.color : '#5c6b7a')
      modes.set(l, mode)
    }
  }
  return { shapes, colors, modes, tram }
}

export async function fetchLive() {
  try {
    const r = await fetch('/api/transit/live')
    return r.ok ? await r.json() : { status: 'error', vehicles: [], alerts: [] }
  } catch {
    return { status: 'error', vehicles: [], alerts: [] }
  }
}
