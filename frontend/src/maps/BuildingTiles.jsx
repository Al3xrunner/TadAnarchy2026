import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { useMap } from 'react-leaflet'
import { staticJson } from '../api/client'
import { CATEGORY } from '../api/categories'
import { DETAIL_ZOOM } from './useZoom'

function styleFor(p, colors) {
  const c = colors.get(p.h3_10)
  if (c) return { color: '#333333', weight: 0.5, fillColor: c, fillOpacity: p.residential ? 0.85 : 0.35 }
  return { color: '#8a97a5', weight: 0.4, fillColor: p.residential ? '#aab5c0' : '#dde2e7', fillOpacity: 0.7 }
}

/**
 * Building footprints, one file per res-8 hexagon (data/buildings/<cell>.geojson),
 * loaded only at zoom >= 15 and only for the visible area. Buildings inside an incident
 * footprint are coloured with the incident's colour. onPick(properties) on click.
 */
export default function BuildingTiles({ incidents, onPick }) {
  const map = useMap()
  const group = useRef(L.layerGroup())
  const tiles = useRef(new Map())        // cell -> L.GeoJSON | 'loading'
  const colors = useRef(new Map())       // res-10 cell -> colour
  const pick = useRef(onPick)
  pick.current = onPick                  // Leaflet handlers always call the latest callback

  useEffect(() => {                      // recolour when footprints change
    const m = new Map()
    for (const i of incidents) for (const c of i.footprint_cells10) m.set(c, CATEGORY[i.cat].color)
    const changed = m.size !== colors.current.size || [...m].some(([k, v]) => colors.current.get(k) !== v)
    colors.current = m
    if (changed) tiles.current.forEach((t) => { if (t !== 'loading') t.setStyle((f) => styleFor(f.properties, m)) })
  }, [incidents])

  useEffect(() => {
    const g = group.current
    let alive = true
    const update = async () => {
      if (map.getZoom() < DETAIL_ZOOM) { g.remove(); return }
      g.addTo(map)
      const idx = await staticJson('buildings/index.json')
      const b = map.getBounds()
      for (const [cell, t] of Object.entries(idx.tiles)) {
        const [w, s, e, n] = t.bbox
        if (e < b.getWest() || w > b.getEast() || n < b.getSouth() || s > b.getNorth() || tiles.current.has(cell)) continue
        tiles.current.set(cell, 'loading')
        try {
          const gj = await staticJson(`buildings/${cell}.geojson`)
          if (!alive) return
          const layer = L.geoJSON(gj, {
            style: (f) => styleFor(f.properties, colors.current),
            onEachFeature: (f, l) => l.on('click', () => pick.current?.(f.properties)),
          })
          tiles.current.set(cell, layer)
          g.addLayer(layer)
        } catch {
          tiles.current.delete(cell)     // retry on the next move
        }
      }
    }
    update()
    map.on('moveend', update)            // fires after pans and zooms
    return () => { alive = false; map.off('moveend', update); g.remove() }
  }, [map])

  return null
}
