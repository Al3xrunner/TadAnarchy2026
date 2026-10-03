import { useState } from 'react'
import { useMap, useMapEvents } from 'react-leaflet'

export const DETAIL_ZOOM = 15     // >= 15: footprints + buildings, below: res-8 hexagons

/** Current zoom as React state, so components can switch between the two map levels. */
export function useZoom() {
  const map = useMap()
  const [zoom, setZoom] = useState(map.getZoom())
  useMapEvents({ zoomend: () => setZoom(map.getZoom()) })
  return zoom
}
