import { CircleMarker, GeoJSON, Tooltip } from 'react-leaflet'
import { CATEGORY } from '../api/categories'
import { DETAIL_ZOOM, useZoom } from './useZoom'

export default function IncidentLayer({ incidents, notices, selectedId, onSelect }) {
  const detail = useZoom() >= DETAIL_ZOOM
  return (
    <>
      {notices.filter((n) => n.kind === 'official' && n.area).map((n) => (   
        <GeoJSON key={`notice-${n.id}`} data={n.area} interactive={false}
          style={{ color: '#1f4e79', weight: detail ? 3 : 2, dashArray: detail ? undefined : '4 4', fill: false }} />
      ))}
      {detail && incidents.filter((i) => i.footprint).map((i) => (
        <GeoJSON key={`${i.id}-${i.footprint_cells10.length}-${i.footprint_cells10[0]}`} data={i.footprint}
          style={{ color: CATEGORY[i.cat].color, weight: 2.5, dashArray: i.approximate ? '6 5' : undefined, fillOpacity: 0.06 }}
          eventHandlers={{ click: () => onSelect(i) }} />
      ))}
      {incidents.map((i) => (
        <CircleMarker key={i.id} center={[i.center.lat, i.center.lng]}
          radius={(detail ? 8 : 11) + (i.id === selectedId ? 3 : 0)}
          pathOptions={{ color: i.id === selectedId ? '#1d2a36' : '#ffffff', weight: 3, fillColor: CATEGORY[i.cat].color,
                         fillOpacity: i.status === 'resolving' ? 0.35 : i.level === 2 ? 1 : 0.7 }}
          eventHandlers={{ click: () => onSelect(i) }}>
          <Tooltip>{CATEGORY[i.cat].en} · {i.district} · {i.devices} reports</Tooltip>
        </CircleMarker>
      ))}
    </>
  )
}
