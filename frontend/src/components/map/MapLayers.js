/**
 * MapLayers Component
 * Handles all Mapbox layer setup and rendering
 * Decoupled from map initialization logic
 */

export const addMapLayers = (map, cableNetworkData) => {
  if (!map || !map.current) return;

  // Cable network source
  if (!map.current.getSource('cable-network')) {
    map.current.addSource('cable-network', {
      type: 'geojson',
      data: cableNetworkData
    });
  }

  // Cable bundles layer
  if (!map.current.getLayer('cable-bundles')) {
    map.current.addLayer({
      id: 'cable-bundles',
      type: 'line',
      source: 'cable-network',
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': '#333333',
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 2,
          15, 4,
          20, 8
        ]
      }
    });
  }

  // Underground cables layer
  if (!map.current.getLayer('underground-cables')) {
    map.current.addLayer({
      id: 'underground-cables',
      type: 'line',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'underground'],
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': ['get', 'color'],
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 3,
          15, 6,
          20, 12
        ],
        'line-opacity': 0.9
      }
    });
  }

  // Overhead cables layer
  if (!map.current.getLayer('overhead-cables')) {
    map.current.addLayer({
      id: 'overhead-cables',
      type: 'line',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'overhead'],
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': ['get', 'color'],
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 4,
          15, 8,
          20, 16
        ],
        'line-opacity': 0.9
      }
    });
  }

  // Cable glow effect
  if (!map.current.getLayer('cable-glow')) {
    map.current.addLayer({
      id: 'cable-glow',
      type: 'line',
      source: 'cable-network',
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': ['get', 'color'],
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 4,
          15, 8,
          20, 16
        ],
        'line-opacity': 0.2,
        'line-blur': 2
      }
    });
  }

  // Monitoring sensors layer
  if (!map.current.getLayer('cable-monitors')) {
    map.current.addLayer({
      id: 'cable-monitors',
      type: 'circle',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'sensor'],
      paint: {
        'circle-color': '#00ff88',
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 4,
          15, 8,
          20, 16
        ],
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 2,
        'circle-opacity': 0.9
      }
    });
  }

  // Sensor glow effect
  if (!map.current.getLayer('cable-monitors-glow')) {
    map.current.addLayer({
      id: 'cable-monitors-glow',
      type: 'circle',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'sensor'],
      paint: {
        'circle-color': '#00ff88',
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 8,
          15, 16,
          20, 32
        ],
        'circle-opacity': 0.3,
        'circle-blur': 2
      }
    });
  }

  // Substations layer
  if (!map.current.getLayer('cable-substations')) {
    map.current.addLayer({
      id: 'cable-substations',
      type: 'circle',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'substation'],
      paint: {
        'circle-color': '#ff6b35',
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 4,
          15, 8,
          20, 16
        ],
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 2,
        'circle-opacity': 0.9
      }
    });
  }

  // Transmission towers (Tower 27/222 - Camp Fire)
  if (!map.current.getLayer('transmission-towers')) {
    map.current.addLayer({
      id: 'transmission-towers',
      type: 'circle',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'transmission-tower'],
      paint: {
        'circle-color': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          '#ff00ff',
          '#00ff88'
        ],
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 6,
          15, 12,
          20, 20
        ],
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 3,
        'circle-opacity': 0.95
      }
    });
  }

  // Transmission tower glow
  if (!map.current.getLayer('transmission-towers-glow')) {
    map.current.addLayer({
      id: 'transmission-towers-glow',
      type: 'circle',
      source: 'cable-network',
      filter: ['==', ['get', 'type'], 'transmission-tower'],
      paint: {
        'circle-color': '#00ff88',
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10, 12,
          15, 24,
          20, 40
        ],
        'circle-opacity': 0.2,
        'circle-blur': 3
      }
    });
  }

  // Roads layer (for context)
  if (!map.current.getLayer('roads-major')) {
    try {
      map.current.addLayer({
        id: 'roads-major',
        type: 'line',
        source: 'composite',
        'source-layer': 'road',
        filter: ['in', 'class', 'primary', 'secondary'],
        paint: {
          'line-color': '#666666',
          'line-width': [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 1,
            15, 2,
            20, 4
          ],
          'line-opacity': 0.4
        }
      });
    } catch (e) {
      console.warn('Could not add roads layer:', e);
    }
  }

  // Street labels layer
  if (!map.current.getLayer('street-labels')) {
    try {
      map.current.addLayer({
        id: 'street-labels',
        type: 'symbol',
        source: 'composite',
        'source-layer': 'road',
        filter: ['in', 'class', 'primary'],
        layout: {
          'text-field': ['get', 'name'],
          'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular'],
          'text-size': 10,
          'text-transform': 'uppercase',
          'text-letter-spacing': 0.05
        },
        paint: {
          'text-color': '#888888',
          'text-halo-color': '#000000',
          'text-halo-width': 1,
          'text-opacity': 0.6
        }
      });
    } catch (e) {
      console.warn('Could not add street labels:', e);
    }
  }

  // 3D buildings layer
  if (!map.current.getLayer('3d-buildings')) {
    try {
      if (map.current.getSource('composite')) {
        map.current.addLayer({
          id: '3d-buildings',
          source: 'composite',
          'source-layer': 'building',
          filter: ['==', 'extrude', 'true'],
          type: 'fill-extrusion',
          minzoom: 15,
          paint: {
            'fill-extrusion-color': '#1a1a1a',
            'fill-extrusion-height': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15,
              0,
              15.05,
              ['get', 'height']
            ],
            'fill-extrusion-base': [
              'interpolate',
              ['linear'],
              ['zoom'],
              15,
              0,
              15.05,
              ['get', 'min_height']
            ],
            'fill-extrusion-opacity': 0.3
          }
        });
      }
    } catch (e) {
      console.warn('Could not add 3D buildings layer:', e);
    }
  }
};
