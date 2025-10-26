import { useEffect } from 'react';

/**
 * SensorPointLayer
 * Renders a live sensor point on a transmission line using Mapbox layers.
 * Sensor positioned at real coordinates along SF transmission lines.
 *
 * Features:
 * - Real-time color updates based on RUL health status
 * - Green (>72h), Yellow (24-72h), Red (<24h)
 * - Smooth pulsing animation for active monitoring
 * - Click to open sensor details panel
 */

// Real coordinates from SF transmission line data - positioned along actual transmission line
// Using transmission line in far west SF, further north
const SENSOR_LOCATION = {
  lon: -122.4149,   // Far west transmission line in SF
  lat: 37.7837,     // Further north on this transmission line
};

// Risk zone to color mapping
const RISK_ZONE_COLORS = {
  green: '#00ff88',    // Healthy (>72 hours)
  yellow: '#ffaa00',   // Warning (24-72 hours)
  orange: '#ff6600',   // High Risk (14-24 hours)
  red: '#ff3333',      // Critical (<14 hours)
};

export const useSensorPointLayer = (map, onSensorClick, riskZone = 'green') => {
  useEffect(() => {
    if (!map?.current) return;

    const mapRef = map.current;

    // Add sensor source if it doesn't exist
    if (!mapRef.getSource('live-sensor-point')) {
      mapRef.addSource('live-sensor-point', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [SENSOR_LOCATION.lon, SENSOR_LOCATION.lat],
          },
          properties: {
            id: 'sf-sensor-1',
            type: 'sensor',
            name: 'SF Transmission Sensor #1',
            status: 'active',
            riskZone: riskZone,
          },
        },
      });
    }

    // Add main sensor marker layer (responds to RUL changes)
    if (!mapRef.getLayer('live-sensor-marker')) {
      mapRef.addLayer({
        id: 'live-sensor-marker',
        type: 'circle',
        source: 'live-sensor-point',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            12,
            8,
            16,
            14,
            18,
            20,
          ],
          'circle-color': RISK_ZONE_COLORS[riskZone] || RISK_ZONE_COLORS.green,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 2.5,
          'circle-opacity': 0.95,
        },
      });
    } else {
      // Update color if component already exists
      const color = RISK_ZONE_COLORS[riskZone] || RISK_ZONE_COLORS.green;
      mapRef.setPaintProperty('live-sensor-marker', 'circle-color', color);
    }

    // Add subtle outer glow
    if (!mapRef.getLayer('live-sensor-glow')) {
      mapRef.addLayer({
        id: 'live-sensor-glow',
        type: 'circle',
        source: 'live-sensor-point',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            12,
            20,
            16,
            32,
            18,
            48,
          ],
          'circle-color': RISK_ZONE_COLORS[riskZone] || RISK_ZONE_COLORS.green,
          'circle-opacity': [
            'interpolate',
            ['linear'],
            ['zoom'],
            12,
            0.15,
            16,
            0.1,
            18,
            0.05,
          ],
          'circle-blur': 1.5,
        },
      });
    } else {
      // Update glow color
      const color = RISK_ZONE_COLORS[riskZone] || RISK_ZONE_COLORS.green;
      mapRef.setPaintProperty('live-sensor-glow', 'circle-color', color);
    }

    // Add pulsing animation layer
    if (!mapRef.getLayer('live-sensor-pulse')) {
      mapRef.addLayer({
        id: 'live-sensor-pulse',
        type: 'circle',
        source: 'live-sensor-point',
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            12,
            12,
            16,
            20,
            18,
            28,
          ],
          'circle-color': RISK_ZONE_COLORS[riskZone] || RISK_ZONE_COLORS.green,
          'circle-opacity': 0.3,
          'circle-blur': 2,
        },
      });
    } else {
      // Update pulse color
      const color = RISK_ZONE_COLORS[riskZone] || RISK_ZONE_COLORS.green;
      mapRef.setPaintProperty('live-sensor-pulse', 'circle-color', color);
    }

    // Add click handler
    const handleClick = (e) => {
      if (onSensorClick && e.features && e.features.length > 0) {
        const feature = e.features[0];
        onSensorClick({
          coordinates: feature.geometry.coordinates,
          properties: feature.properties,
        });
      }
    };

    const handleMouseEnter = () => {
      mapRef.getCanvas().style.cursor = 'pointer';
    };

    const handleMouseLeave = () => {
      mapRef.getCanvas().style.cursor = '';
    };

    mapRef.on('click', 'live-sensor-marker', handleClick);
    mapRef.on('mouseenter', 'live-sensor-marker', handleMouseEnter);
    mapRef.on('mouseleave', 'live-sensor-marker', handleMouseLeave);

    return () => {
      mapRef.off('click', 'live-sensor-marker', handleClick);
      mapRef.off('mouseenter', 'live-sensor-marker', handleMouseEnter);
      mapRef.off('mouseleave', 'live-sensor-marker', handleMouseLeave);
    };
  }, [map, onSensorClick, riskZone]);
};

/**
 * Get sensor location coordinates
 */
export const getSensorLocation = () => SENSOR_LOCATION;

/**
 * Update sensor status color dynamically (for RUL health status)
 * This function updates the sensor point color based on RUL zone
 *
 * @param {Object} map - Mapbox map reference
 * @param {string} healthStatus - Risk zone: 'green', 'yellow', 'orange', 'red'
 */
export const updateSensorStatusColor = (map, healthStatus) => {
  if (!map?.current || !map.current.getLayer('live-sensor-marker')) return;

  const color = RISK_ZONE_COLORS[healthStatus?.toLowerCase()] || RISK_ZONE_COLORS.green;

  if (map.current.getLayer('live-sensor-marker')) {
    map.current.setPaintProperty('live-sensor-marker', 'circle-color', color);
  }
  if (map.current.getLayer('live-sensor-glow')) {
    map.current.setPaintProperty('live-sensor-glow', 'circle-color', color);
  }
  if (map.current.getLayer('live-sensor-pulse')) {
    map.current.setPaintProperty('live-sensor-pulse', 'circle-color', color);
  }
};
