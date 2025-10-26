/**
 * Transmission Line Data Utilities
 * Fetches real transmission line data from OpenStreetMap (Overpass API)
 * Alternative: California Energy Commission (CEC) data
 */

/**
 * Fetch real transmission lines for a given bounding box using Overpass API
 * Data source: OpenStreetMap community-mapped power infrastructure
 * Falls back to demo data if API fails
 *
 * @param {Object} bbox - Bounding box {minLat, maxLat, minLon, maxLon}
 * @returns {Promise<Object>} GeoJSON FeatureCollection of transmission lines
 */
export const fetchTransmissionLines = async (bbox) => {
  const { minLat, maxLat, minLon, maxLon } = bbox;

  // Overpass API query for power transmission lines and towers
  const overpassQuery = `
    [out:json][timeout:30];
    (
      way["power"="line"](${minLat},${minLon},${maxLat},${maxLon});
      node["power"="tower"](${minLat},${minLon},${maxLat},${maxLon});
    );
    out geom;
  `;

  try {
    console.log(`Fetching from Overpass API for bbox: ${minLat},${minLon},${maxLat},${maxLon}`);
    const response = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      body: overpassQuery,
      timeout: 30000
    });

    if (!response.ok) {
      throw new Error(`Overpass API error: ${response.statusText}`);
    }

    const osmData = await response.json();
    console.log(`Received ${osmData.elements?.length || 0} elements from Overpass API`);

    // Convert OSM data to GeoJSON
    const geojson = convertOSMtoGeoJSON(osmData);
    console.log(`Converted to GeoJSON with ${geojson.features.length} features`);

    return geojson;
  } catch (error) {
    console.warn('Error fetching from Overpass API, using demo data:', error);
    // Fallback to demo data
    return generateDemoTransmissionData(bbox);
  }
};

/**
 * Generate demo transmission data for testing/development
 * Creates sample transmission lines and towers
 */
const generateDemoTransmissionData = (bbox) => {
  const { minLat, maxLat, minLon, maxLon } = bbox;
  const centerLat = (minLat + maxLat) / 2;
  const centerLon = (minLon + maxLon) / 2;
  const latRange = maxLat - minLat;
  const lonRange = maxLon - minLon;

  console.log('Generating demo transmission data');

  const features = [];

  // Create some demo transmission lines
  for (let i = 0; i < 5; i++) {
    const startLat = minLat + (Math.random() * latRange);
    const startLon = minLon + (Math.random() * lonRange);
    const endLat = minLat + (Math.random() * latRange);
    const endLon = minLon + (Math.random() * lonRange);

    features.push({
      type: 'Feature',
      properties: {
        id: `demo-line-${i}`,
        name: `Demo Transmission Line ${i + 1}`,
        powerType: 'line',
        voltage: ['110000', '230000', '500000'][i % 3],
        operator: 'Demo Operator',
        source: 'Demo Data'
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [startLon, startLat],
          [(startLon + endLon) / 2, (startLat + endLat) / 2],
          [endLon, endLat]
        ]
      }
    });
  }

  // Create some demo towers
  for (let i = 0; i < 10; i++) {
    const lat = minLat + (Math.random() * latRange);
    const lon = minLon + (Math.random() * lonRange);

    features.push({
      type: 'Feature',
      properties: {
        id: `demo-tower-${i}`,
        name: `Demo Tower ${i + 1}`,
        powerType: 'tower',
        ref: `T${i + 1}`,
        source: 'Demo Data'
      },
      geometry: {
        type: 'Point',
        coordinates: [lon, lat]
      }
    });
  }

  return {
    type: 'FeatureCollection',
    features: features,
    metadata: {
      source: 'Demo Data',
      note: 'Using demo data - Overpass API unavailable'
    }
  };
};

/**
 * Convert OpenStreetMap data to GeoJSON format
 * @param {Object} osmData - Raw OSM data from Overpass API
 * @returns {Object} GeoJSON FeatureCollection
 */
const convertOSMtoGeoJSON = (osmData) => {
  const features = [];
  const nodeMap = new Map();

  // Index all nodes by ID for quick lookup
  if (osmData.elements) {
    osmData.elements.forEach(element => {
      if (element.type === 'node') {
        nodeMap.set(element.id, { lat: element.lat, lon: element.lon });
      }
    });

    // Process ways (power lines)
    osmData.elements.forEach(element => {
      if (element.type === 'way' && element.tags && element.tags.power) {
        const coordinates = [];

        // Build coordinate list from nodes
        if (element.nodes) {
          element.nodes.forEach(nodeId => {
            const node = nodeMap.get(nodeId);
            if (node) {
              coordinates.push([node.lon, node.lat]);
            }
          });
        }

        if (coordinates.length >= 2) {
          features.push({
            type: 'Feature',
            properties: {
              id: element.id,
              name: element.tags.name || 'Unnamed',
              powerType: element.tags.power,
              voltage: element.tags.voltage || 'Unknown',
              frequency: element.tags.frequency || null,
              wires: element.tags.wires || null,
              ref: element.tags.ref || null,
              operator: element.tags.operator || null,
              source: 'OpenStreetMap'
            },
            geometry: {
              type: 'LineString',
              coordinates: coordinates
            }
          });
        }
      }

      // Process point towers
      if (element.type === 'node' && element.tags && element.tags.power === 'tower') {
        features.push({
          type: 'Feature',
          properties: {
            id: element.id,
            name: element.tags.name || 'Transmission Tower',
            powerType: 'tower',
            ref: element.tags.ref || null,
            source: 'OpenStreetMap'
          },
          geometry: {
            type: 'Point',
            coordinates: [element.lon, element.lat]
          }
        });
      }
    });
  }

  return {
    type: 'FeatureCollection',
    features: features,
    metadata: {
      source: 'OpenStreetMap via Overpass API',
      license: 'ODbL 1.0',
      attribution: '© OpenStreetMap contributors'
    }
  };
};

/**
 * Bounding boxes for different regions
 */
export const REGIONS = {
  // Paradise, CA (Camp Fire area) - Butte County
  PARADISE: {
    name: 'Paradise, CA (Camp Fire Region)',
    minLat: 39.5,
    maxLat: 40.0,
    minLon: -121.8,
    maxLon: -121.0
  },

  // Los Angeles area
  LOS_ANGELES: {
    name: 'Los Angeles, CA',
    minLat: 33.8,
    maxLat: 34.2,
    minLon: -118.4,
    maxLon: -117.9
  },

  // San Francisco area (expanded to include more Bay Area transmission lines)
  SAN_FRANCISCO: {
    name: 'San Francisco, CA',
    minLat: 37.3,
    maxLat: 38.0,
    minLon: -123.0,
    maxLon: -121.8
  },

  // New York City area
  NEW_YORK: {
    name: 'New York City, NY',
    minLat: 40.6,
    maxLat: 40.9,
    minLon: -74.1,
    maxLon: -73.7
  },

  // All of California
  CALIFORNIA: {
    name: 'California',
    minLat: 32.5,
    maxLat: 42.0,
    minLon: -124.5,
    maxLon: -114.0
  }
};

/**
 * Filter transmission lines by voltage
 * @param {Object} geojson - GeoJSON FeatureCollection
 * @param {number} minVoltage - Minimum voltage in kV
 * @param {number} maxVoltage - Maximum voltage in kV
 * @returns {Object} Filtered GeoJSON
 */
export const filterByVoltage = (geojson, minVoltage, maxVoltage) => {
  const features = geojson.features.filter(feature => {
    if (feature.properties.powerType === 'tower') return true; // Keep all towers

    const voltage = feature.properties.voltage;
    if (!voltage) return true; // Keep if voltage unknown

    // Parse voltage string (e.g., "115000" or "115 kV")
    const voltageNum = parseInt(voltage.replace(/[^\d]/g, '')) || 0;
    return voltageNum >= minVoltage && voltageNum <= maxVoltage;
  });

  return {
    ...geojson,
    features: features
  };
};

/**
 * Filter transmission lines by operator
 * @param {Object} geojson - GeoJSON FeatureCollection
 * @param {string} operator - Operator name (e.g., "PG&E")
 * @returns {Object} Filtered GeoJSON
 */
export const filterByOperator = (geojson, operator) => {
  const features = geojson.features.filter(feature => {
    if (feature.properties.powerType === 'tower') return true;
    return feature.properties.operator &&
           feature.properties.operator.includes(operator);
  });

  return {
    ...geojson,
    features: features
  };
};

/**
 * Cache for fetched transmission data (in-memory)
 */
const dataCache = new Map();

/**
 * Fetch transmission data with caching
 * @param {string} regionKey - Key from REGIONS object
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export const fetchTransmissionDataCached = async (regionKey) => {
  // Check cache first
  if (dataCache.has(regionKey)) {
    console.log(`Using cached data for ${regionKey}`);
    return dataCache.get(regionKey);
  }

  const region = REGIONS[regionKey];
  if (!region) {
    throw new Error(`Unknown region: ${regionKey}`);
  }

  console.log(`Fetching transmission data for ${region.name}...`);
  const data = await fetchTransmissionLines(region);

  if (data) {
    // Cache the data
    dataCache.set(regionKey, data);
  }

  return data;
};

/**
 * Clear cached data
 * @param {string} regionKey - Specific region, or 'all' to clear all
 */
export const clearCache = (regionKey = 'all') => {
  if (regionKey === 'all') {
    dataCache.clear();
  } else {
    dataCache.delete(regionKey);
  }
};
