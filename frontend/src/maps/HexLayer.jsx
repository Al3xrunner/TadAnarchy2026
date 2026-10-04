import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { useMap } from 'react-leaflet'
import { staticJson } from '../api/client'
import { LEVEL_COLOR } from '../api/categories'
import { DETAIL_ZOOM, useZoom } from './useZoom'

export default function HexLayer({ cells, category = 'all', minDevices = 0 }) {
  const map = useMap()
  const zoom = useZoom()
  const byId = useRef(new Map())
  const [ready, setReady] = useState(false)

  useEffect(() => {                                 
    let layer = null
    let alive = true
    staticJson('cells_res8.geojson').then((gj) => {
      if (!alive) return
      layer = L.geoJSON(gj, { style: { color: '#ffffff', weight: 0.5, fillOpacity: 0, opacity: 0.4 }, interactive: false })
      layer.eachLayer((l) => byId.current.set(l.feature.id, l))
      layer.addTo(map)
      setReady(true)
    })
    return () => { alive = false; layer?.remove(); byId.current.clear() }
  }, [map])

  useEffect(() => {                                  
    const worst = new Map()
    for (const c of cells) {
      if ((category === 'all' || c.cat === category) && c.devices >= minDevices) {
        worst.set(c.h3, Math.max(worst.get(c.h3) ?? 0, c.level))
      }
    }
    const detail = zoom >= DETAIL_ZOOM
    byId.current.forEach((path, id) => {
      const lvl = worst.get(id) ?? 0
      path.setStyle(detail || lvl === 0
        ? { fillOpacity: 0, opacity: detail ? 0 : 0.4, color: '#ffffff' }
        : { color: LEVEL_COLOR[lvl], opacity: 0.9, weight: 1.5, fillColor: LEVEL_COLOR[lvl], fillOpacity: lvl === 2 ? 0.45 : 0.3 })
    })
  }, [cells, category, zoom, minDevices, ready])

  return null
}
