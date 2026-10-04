import { useEffect, useState } from 'react'
import { CircleMarker, GeoJSON, Tooltip } from 'react-leaflet'
import { LEVEL_COLOR } from '../api/categories'
import { loadLines } from '../api/transit'

export default function LineIncidentLayer({ incidents, selectedId, onSelect }) {
  const [lines, setLines] = useState(null)
  useEffect(() => { loadLines().then(setLines) }, [])
  if (!lines) return null
  return (
    <>
      {incidents.map((i) => {
        const shape = lines.shapes.get(i.line)?.[0]
        if (!shape) return null
        const color = LEVEL_COLOR[i.level] === 'transparent' ? '#9aa6b2' : LEVEL_COLOR[i.level]
        return (
          <GeoJSON key={`${i.id}-${i.level}-${i.id === selectedId}`} data={shape}
            style={{ color, weight: i.id === selectedId ? 9 : 6, opacity: i.status === 'resolving' ? 0.35 : 0.75 }}
            eventHandlers={{ click: () => onSelect(i) }} />
        )
      })}
      {incidents.flatMap((i) => i.stops.map((s) => (
        <CircleMarker key={`${i.id}-${s.stop_id}`} center={[s.lat, s.lng]} radius={5 + Math.min(6, s.devices * 2)}
          pathOptions={{ color: '#ffffff', weight: 2, fillColor: i.color, fillOpacity: 1 }}
          eventHandlers={{ click: () => onSelect(i) }}>
          <Tooltip>Line {i.line} · {s.name} · {s.devices} reports</Tooltip>
        </CircleMarker>
      )))}
    </>
  )
}
