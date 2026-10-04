import { CircleMarker, Tooltip } from 'react-leaflet'

export default function LiveVehiclesLayer({ vehicles, colors, filter }) {
  return (
    <>
      {vehicles.filter((v) => !filter || v.line === filter).map((v) => (
        <CircleMarker key={`${v.mode}-${v.id}`} center={[v.lat, v.lng]} radius={v.mode === 'tram' ? 5 : 4}
          pathOptions={{ color: '#ffffff', weight: 1.5, fillColor: colors?.get(v.line) ?? (v.mode === 'tram' ? '#d1495b' : '#5c6b7a'), fillOpacity: 1 }}>
          <Tooltip>{v.mode === 'tram' ? 'Tram' : 'Bus'} {v.line}</Tooltip>
        </CircleMarker>
      ))}
    </>
  )
}
