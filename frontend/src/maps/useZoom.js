import { useState } from 'react'
import { useMap, useMapEvents } from 'react-leaflet'

export const DETAIL_ZOOM = 15    

export function useZoom() {
  const map = useMap()
  const [zoom, setZoom] = useState(map.getZoom())
  useMapEvents({ zoomend: () => setZoom(map.getZoom()) })
  return zoom
}
