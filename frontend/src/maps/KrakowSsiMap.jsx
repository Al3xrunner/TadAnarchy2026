import { useEffect, useRef, useState } from 'react';

const LEAFLET_CSS =
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css';
const LEAFLET_JS =
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js';
const H3_JS = 'https://unpkg.com/h3-js@4.2.1/dist/h3-js.umd.js';

let leafletPromise;
let h3Promise;

function loadStylesheet(url, id) {
  const existing = document.getElementById(id);
  if (existing) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.id = id;
    link.rel = 'stylesheet';
    link.href = url;
    link.onload = resolve;
    link.onerror = () => reject(new Error(`Could not load stylesheet: ${url}`));
    document.head.appendChild(link);
  });
}

function loadGlobalScript(url, globalName) {
  const globalObject = globalThis[globalName];
  if (globalObject) {
    return Promise.resolve(globalObject);
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.async = true;
    script.onload = () => {
      const loadedGlobal = globalThis[globalName];
      if (!loadedGlobal) {
        reject(new Error(`Script loaded without exposing ${globalName}: ${url}`));
        return;
      }
      resolve(loadedGlobal);
    };
    script.onerror = () => reject(new Error(`Could not load script: ${url}`));
    document.head.appendChild(script);
  });
}

function loadLeaflet() {
  leafletPromise ??= Promise.all([
    loadStylesheet(LEAFLET_CSS, 'krakow-ssi-leaflet-css'),
    loadGlobalScript(LEAFLET_JS, 'L'),
  ]).then(([, leaflet]) => leaflet);
  return leafletPromise;
}

function loadH3() {
  h3Promise ??= loadGlobalScript(H3_JS, 'h3');
  return h3Promise;
}

function makeCellIndex(snapshot) {
  const cells = Array.isArray(snapshot?.cells) ? snapshot.cells : [];
  const index = new Map();

  for (const cell of cells) {
    if (!cell?.h3) {
      continue;
    }

    const summary = index.get(cell.h3) ?? {
      level: 0,
      devices: 0,
      fine: 0,
      categories: [],
    };
    summary.level = Math.max(summary.level, Number(cell.level) || 0);
    summary.devices += Number(cell.devices) || 0;
    summary.fine += Number(cell.fine) || 0;
    if (cell.cat && !summary.categories.includes(cell.cat)) {
      summary.categories.push(cell.cat);
    }
    index.set(cell.h3, summary);
  }

  return index;
}

function cellColor(level) {
  if (level >= 2) {
    return '#ef4444';
  }
  if (level === 1) {
    return '#facc15';
  }
  return '#ffffff';
}

function popupContent(cellId, summary) {
  const content = document.createElement('div');
  const title = document.createElement('strong');
  title.textContent = cellId;
  content.appendChild(title);

  const details = summary
    ? [
        ['SSI level', String(summary.level)],
        ['Devices', String(summary.devices)],
        ['Fine reports', String(summary.fine)],
        ['Categories', summary.categories.join(', ') || '—'],
      ]
    : [['SSI level', 'No active reports']];

  for (const [label, value] of details) {
    const row = document.createElement('div');
    row.textContent = `${label}: ${value}`;
    content.appendChild(row);
  }
  return content;
}

/**
 * Render the Kraków H3 resolution-8 cells and color them from an SSI snapshot.
 * Pass each new stream snapshot as the `snapshot` prop to update the map.
 */
export default function KrakowSsiMap({
  snapshot,
  cellsUrl = '/data/cells_res8.json',
  className,
  style,
}) {
  const mapElementRef = useRef(null);
  const mapRef = useRef(null);
  const cellsLayerRef = useRef(null);
  const snapshotRef = useRef(snapshot);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    let map;

    async function initializeMap() {
      try {
        const [leaflet, h3, response] = await Promise.all([
          loadLeaflet(),
          loadH3(),
          fetch(cellsUrl),
        ]);
        if (!response.ok) {
          throw new Error(
            `Could not load H3 cells (${response.status} ${response.statusText})`,
          );
        }
        const cellData = await response.json();
        if (!cellData?.cells || typeof cellData.cells !== 'object') {
          throw new Error('The H3 cell data has an invalid format.');
        }
        if (cancelled) {
          return;
        }

        map = leaflet.map(mapElementRef.current).setView([50.0647, 19.945], 11);
        mapRef.current = map;
        leaflet
          .tileLayer(
            'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            {
              attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
              maxZoom: 19,
              subdomains: 'abcd',
            },
          )
          .addTo(map);

        const features = Object.keys(cellData.cells).map((cellId) => {
          const boundary = h3
            .cellToBoundary(cellId)
            .map(([lat, lng]) => [lng, lat]);
          return {
            type: 'Feature',
            properties: { cellId },
            geometry: {
              type: 'Polygon',
              coordinates: [[...boundary, boundary[0]]],
            },
          };
        });
        const initialIndex = makeCellIndex(snapshotRef.current);
        const layer = leaflet.geoJSON(
          { type: 'FeatureCollection', features },
          {
            style: (feature) => {
              const summary = initialIndex.get(feature.properties.cellId);
              return {
                color: '#667085',
                weight: 0.8,
                opacity: 0.55,
                fillColor: cellColor(summary?.level ?? 0),
                fillOpacity: summary?.level ? 0.72 : 0.62,
              };
            },
            onEachFeature: (feature, cellLayer) => {
              cellLayer.on('click', () => {
                const currentIndex = makeCellIndex(snapshotRef.current);
                const cellId = feature.properties.cellId;
                cellLayer
                  .bindPopup(popupContent(cellId, currentIndex.get(cellId)))
                  .openPopup();
              });
            },
          },
        ).addTo(map);

        cellsLayerRef.current = layer;
        setError('');
      } catch (initializationError) {
        if (!cancelled) {
          setError(initializationError.message);
        }
      }
    }

    initializeMap();

    return () => {
      cancelled = true;
      cellsLayerRef.current = null;
      mapRef.current = null;
      map?.remove();
    };
  }, [cellsUrl]);

  useEffect(() => {
    snapshotRef.current = snapshot;
    const layer = cellsLayerRef.current;
    if (!layer) {
      return;
    }

    const index = makeCellIndex(snapshot);
    layer.setStyle((feature) => {
      const summary = index.get(feature.properties.cellId);
      return {
        fillColor: cellColor(summary?.level ?? 0),
        fillOpacity: summary?.level ? 0.72 : 0.62,
      };
    });
  }, [snapshot]);

  const activeCells = makeCellIndex(snapshot).size;

  return (
    <div
      className={className}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: 360,
        ...style,
      }}
    >
      <div
        ref={mapElementRef}
        aria-label="Kraków SSI map with H3 resolution-8 cells"
        role="application"
        style={{ position: 'absolute', inset: 0, background: '#eef2f5' }}
      />
      <div
        style={{
          position: 'absolute',
          zIndex: 1000,
          top: 12,
          right: 12,
          padding: '10px 12px',
          border: '1px solid #d0d5dd',
          borderRadius: 8,
          background: 'rgba(255,255,255,0.96)',
          color: '#1d2939',
          font: '13px/1.4 system-ui, sans-serif',
          boxShadow: '0 2px 8px rgba(16,24,40,0.12)',
        }}
      >
        <strong>Kraków · H3 resolution 8</strong>
        <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
          {[
            ['#ffffff', 'No alert'],
            ['#facc15', 'SSI level 1'],
            ['#ef4444', 'SSI level 2+'],
          ].map(([color, label]) => (
            <span
              key={label}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
              <span
                aria-hidden="true"
                style={{
                  width: 11,
                  height: 11,
                  border: '1px solid #667085',
                  borderRadius: 2,
                  background: color,
                }}
              />
              {label}
            </span>
          ))}
        </div>
        <div style={{ marginTop: 5, color: '#667085' }}>
          {snapshot ? `${activeCells} cells with SSI data` : 'Waiting for SSI snapshot'}
        </div>
      </div>
      {error && (
        <div
          role="alert"
          style={{
            position: 'absolute',
            zIndex: 1001,
            left: 12,
            bottom: 12,
            maxWidth: 'min(480px, calc(100% - 24px))',
            padding: '10px 12px',
            borderRadius: 6,
            background: '#fff1f0',
            color: '#b42318',
            font: '13px/1.4 system-ui, sans-serif',
          }}
        >
          Map unavailable: {error}
        </div>
      )}
    </div>
  );
}
