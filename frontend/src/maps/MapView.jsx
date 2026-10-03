import 'leaflet/dist/leaflet.css'           // without this the map renders as scattered tiles
import { MapContainer, TileLayer } from 'react-leaflet'

/** Base map centred on Kraków. Put layers inside as children. onReady(map) gives you the Leaflet map. */
export default function MapView({ children, onReady, zoom = 12 }) {
  return (
    <MapContainer center={[50.0614, 19.9366]} zoom={zoom} preferCanvas zoomSnap={0.5}
      ref={(m) => { if (m) onReady?.(m) }} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        maxNativeZoom={16} maxZoom={19}
        attribution="Tiles &copy; Esri &middot; &copy; OpenStreetMap contributors, ZTP Krak&oacute;w, UMK, Kontur" />
      {children}
    </MapContainer>
  )
}
