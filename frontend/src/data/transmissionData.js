/**
 * Transmission Line Data Utilities
 * Uses local pre-processed GeoJSON files from California Energy Commission (CEC) data
 */

import { generateTiles, cacheTile, getCachedTile, mergeTiles, simplifyCoordinates } from '../utils/tileManager';

/**
 * Fetch transmission lines from California Energy Commission ArcGIS API
 * More reliable than Overpass API for California transmission infrastructure
 * Data source: https://cecgis-caenergy.opendata.arcgis.com/
 *
 * @param {Object} bbox - Bounding box {minLat, maxLat, minLon, maxLon}
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
const fetchFromCECGIS = async (bbox) => {
  const { minLat, maxLat, minLon, maxLon } = bbox;

  try {
    const baseUrl = 'https://services.arcgis.com/P3ePLMYPQeEJK6KU/arcgis/rest/services';

    // Build extent filter for bounding box (xmin, ymin, xmax, ymax)
    const where = `1=1`; // Get all features, we'll filter client-side
    const geometry = `{"xmin":${minLon},"ymin":${minLat},"xmax":${maxLon},"ymax":${maxLat},"spatialReference":{"wkid":4326}}`;

    const url = new URL(`${baseUrl}/California_Transmission_Lines_60e06d4aed004acbb97e3c0f6cf97e10/FeatureServer/0/query`);
    url.searchParams.set('geometry', geometry);
    url.searchParams.set('geometryType', 'esriGeometryEnvelope');
    url.searchParams.set('spatialRel', 'esriSpatialRelIntersects');
    url.searchParams.set('where', where);
    url.searchParams.set('outFields', '*');
    url.searchParams.set('returnGeometry', 'true');
    url.searchParams.set('f', 'json');
    url.searchParams.set('token', ''); // CEC API is public, no token needed

    console.log(`🔗 Fetching from CEC GIS API for bbox: ${minLat},${minLon},${maxLat},${maxLon}`);

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`CEC GIS API error: ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`✅ Received ${data.features?.length || 0} features from CEC GIS API`);

    // Convert ArcGIS features to GeoJSON
    const geojson = convertArcGIStoGeoJSON(data);
    return geojson;
  } catch (error) {
    console.warn('CEC GIS API fetch failed:', error.message);
    throw error;
  }
};

/**
 * Convert ArcGIS FeatureSet to GeoJSON FeatureCollection
 * @param {Object} arcgisData - ArcGIS response data
 * @returns {Object} GeoJSON FeatureCollection
 */
const convertArcGIStoGeoJSON = (arcgisData) => {
  const features = [];

  if (!arcgisData.features) {
    return { type: 'FeatureCollection', features: [] };
  }

  arcgisData.features.forEach((feature) => {
    if (!feature.geometry) return;

    // ArcGIS returns paths (polylines) and x/y (points)
    let geometry = null;

    if (feature.geometry.paths) {
      // This is a polyline (transmission line)
      geometry = {
        type: 'LineString',
        coordinates: feature.geometry.paths[0]?.map(([lon, lat]) => [lon, lat]) || []
      };
    } else if (feature.geometry.x !== undefined && feature.geometry.y !== undefined) {
      // This is a point (tower/substation)
      geometry = {
        type: 'Point',
        coordinates: [feature.geometry.x, feature.geometry.y]
      };
    }

    if (geometry && ((geometry.type === 'LineString' && geometry.coordinates.length >= 2) || geometry.type === 'Point')) {
      features.push({
        type: 'Feature',
        properties: {
          id: feature.attributes?.OBJECTID || feature.attributes?.FID,
          name: feature.attributes?.NAME || 'Unnamed',
          powerType: geometry.type === 'LineString' ? 'line' : 'tower',
          voltage: feature.attributes?.VOLTAGE || 'Unknown',
          operator: feature.attributes?.OPERATOR || 'Unknown',
          source: 'CEC GIS'
        },
        geometry: geometry
      });
    }
  });

  return {
    type: 'FeatureCollection',
    features: features,
    metadata: {
      source: 'California Energy Commission GIS',
      license: 'Public',
      attribution: '© California Energy Commission'
    }
  };
};

/**
 * Cache for regional transmission lines GeoJSON (loaded once per region)
 */
const regionCache = new Map();

/**
 * Map region keys to filenames in public/data/
 */
const regionFileMap = {
  'PARADISE': 'transmission-paradise.geojson',
  'SAN_FRANCISCO': 'transmission-san-francisco.geojson',
  'LOS_ANGELES': 'transmission-los-angeles.geojson'
};

/**
 * Load transmission data from regional GeoJSON files (as JS modules)
 * Uses dynamic imports to load data at runtime
 * @param {string} regionKey - Region key (PARADISE, SAN_FRANCISCO, LOS_ANGELES)
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
const loadRegionalTransmissionData = async (regionKey) => {
  // Check cache first
  if (regionCache.has(regionKey)) {
    console.log(`✅ Using cached data for ${regionKey}`);
    return regionCache.get(regionKey);
  }

  const filename = regionFileMap[regionKey];
  if (!filename) {
    console.warn(`⚠️ No data configured for region: ${regionKey}`);
    return { type: 'FeatureCollection', features: [] };
  }

  try {
    console.log(`📂 Loading ${filename} via dynamic import...`);

    // Import the JavaScript module that exports the GeoJSON data
    const jsFilename = filename.replace('.geojson', '.js');
    const geojsonData = await import(`./geojson/${jsFilename}`).then(module => module.default);

    console.log(`✅ Loaded ${geojsonData.features?.length || 0} transmission features for ${regionKey}`);

    // Cache the result
    regionCache.set(regionKey, geojsonData);

    return geojsonData;
  } catch (error) {
    console.error(`Error loading ${regionKey}:`, error);
    return { type: 'FeatureCollection', features: [] };
  }
};

/**
 * Fetch real transmission lines for a given bounding box
 * Uses local regional GeoJSON files from public/data folder
 *
 * @param {Object} bbox - Bounding box {minLat, maxLat, minLon, maxLon}
 * @param {string} regionKey - Optional: Region key to load specific regional file
 * @returns {Promise<Object>} GeoJSON FeatureCollection of transmission lines
 */
export const fetchTransmissionLines = async (bbox, regionKey = null) => {
  try {
    // If a specific region is provided, load that region's data
    if (regionKey) {
      const geojson = await loadRegionalTransmissionData(regionKey);
      return geojson;
    }

    // Otherwise try to determine region from bbox and load appropriate file
    console.warn('⚠️ No regionKey provided to fetchTransmissionLines');
    return generateDemoTransmissionData(bbox);
  } catch (error) {
    console.error('Error fetching transmission lines:', error);
    // Fallback to demo data if local file fails
    return generateDemoTransmissionData(bbox);
  }
};

/**
 * Fetch from Overpass API with retry logic
 * @private
 */
const fetchTransmissionLinesFromOverpass = async (bbox, retries = 2) => {
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

  let lastError = null;

  // Retry logic with exponential backoff
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      console.log(`Fetching from Overpass API (attempt ${attempt + 1}/${retries}) for bbox: ${minLat},${minLon},${maxLat},${maxLon}`);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        body: overpassQuery,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Overpass API error: ${response.statusText}`);
      }

      const osmData = await response.json();
      console.log(`Received ${osmData.elements?.length || 0} elements from Overpass API`);

      // Debug: Check structure of first way element
      if (osmData.elements) {
        const firstWay = osmData.elements.find(el => el.type === 'way' && el.tags?.power);
        if (firstWay) {
          console.log('🔍 Sample way structure:', {
            id: firstWay.id,
            hasGeometry: !!firstWay.geometry,
            geometryType: typeof firstWay.geometry,
            geometryLength: firstWay.geometry?.length,
            firstGeometryPoint: firstWay.geometry?.[0],
            hasNodes: !!firstWay.nodes,
            nodeCount: firstWay.nodes?.length
          });
        }
      }

      // Convert OSM data to GeoJSON
      const geojson = convertOSMtoGeoJSON(osmData);
      console.log(`Converted to GeoJSON with ${geojson.features.length} features`);

      // Debug: Check converted features
      const lineFeatures = geojson.features.filter(f => f.geometry.type === 'LineString');
      if (lineFeatures.length > 0) {
        console.log(`📊 Line features: ${lineFeatures.length}, first line has ${lineFeatures[0].geometry.coordinates.length} points`);
      }

      return geojson;
    } catch (error) {
      lastError = error;
      console.warn(`Attempt ${attempt + 1} failed:`, error.message);

      // If not last attempt, wait before retrying (exponential backoff: 1s, 2s, 4s)
      if (attempt < retries - 1) {
        const waitTime = Math.pow(2, attempt) * 1000;
        console.log(`Retrying in ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  // All retries exhausted, fall back to demo data
  console.warn('All Overpass API attempts failed, using demo data:', lastError?.message);
  return generateDemoTransmissionData(bbox);
};

/**
 * Fetch transmission lines using tiled approach for faster initial load
 * Progressively fetches coarse tiles first, then finer details
 * @param {Object} bbox - Bounding box {minLat, maxLat, minLon, maxLon}
 * @param {Function} onProgress - Callback with {loaded, total, percent}
 * @returns {Promise<Object>} GeoJSON FeatureCollection
 */
export const fetchTransmissionLinesTiled = async (bbox, onProgress = null) => {
  console.log('🔲 Starting tiled transmission data fetch...');

  // Start with coarse tiles (zoom 10) for quick initial view
  const coarseTiles = generateTiles(bbox, 10);
  let loadedCount = 0;

  const updateProgress = (loaded, total) => {
    if (onProgress) {
      onProgress({
        loaded,
        total,
        percent: Math.round((loaded / total) * 100)
      });
    }
  };

  // Fetch coarse tiles first (4-16 tiles depending on region size)
  console.log(`📍 Fetching ${coarseTiles.length} coarse tiles at zoom 10...`);
  const coarseData = await Promise.all(
    coarseTiles.map(async (tile) => {
      // Check cache first
      const cached = getCachedTile(tile.id);
      if (cached) {
        console.log(`✅ Cache hit for tile ${tile.id}`);
        loadedCount++;
        updateProgress(loadedCount, coarseTiles.length * 2);
        return cached;
      }

      // Fetch from Overpass
      try {
        const data = await fetchTransmissionLines(tile);

        // Simplify coordinates for coarse zoom level
        if (data.features) {
          data.features = data.features.map(f => ({
            ...f,
            geometry: {
              ...f.geometry,
              coordinates: f.geometry.type === 'LineString'
                ? simplifyCoordinates(f.geometry.coordinates, 3)
                : f.geometry.coordinates
            }
          }));
        }

        cacheTile(tile.id, data);
        loadedCount++;
        updateProgress(loadedCount, coarseTiles.length * 2);
        return data;
      } catch (error) {
        console.warn(`Failed to fetch tile ${tile.id}:`, error);
        loadedCount++;
        updateProgress(loadedCount, coarseTiles.length * 2);
        return null;
      }
    })
  );

  // Merge coarse tiles
  const mergedCoarse = mergeTiles(coarseData);
  console.log(`✅ Coarse load complete: ${mergedCoarse.features.length} features`);

  // Now fetch finer detail tiles in the background (don't wait for them)
  const fineTiles = generateTiles(bbox, 12);
  console.log(`📍 Queuing ${fineTiles.length} fine tiles at zoom 12 (loading in background)...`);

  // Fetch fine tiles asynchronously without blocking
  Promise.all(
    fineTiles.map(async (tile) => {
      const cached = getCachedTile(tile.id);
      if (cached) {
        console.log(`✅ Cache hit for fine tile ${tile.id}`);
        return cached;
      }

      try {
        const data = await fetchTransmissionLines(tile);
        cacheTile(tile.id, data);
        console.log(`✅ Fine tile ${tile.id} fetched and cached`);
        return data;
      } catch (error) {
        console.warn(`Failed to fetch fine tile ${tile.id}:`, error);
        return null;
      }
    })
  ).catch(err => console.warn('Background tile fetch error:', err));

  return mergedCoarse;
};

/**
 * Generate demo transmission data for testing/development
 * Creates sample transmission lines and towers
 */
const generateDemoTransmissionData = (bbox) => {
  const { minLat, maxLat, minLon, maxLon } = bbox;
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

  if (!osmData.elements) {
    return {
      type: 'FeatureCollection',
      features: [],
      metadata: {
        source: 'OpenStreetMap via Overpass API',
        error: 'No elements in OSM response'
      }
    };
  }

  // First pass: Build a complete node map with all available coordinates
  // This is essential because 'out geom' returns node coordinates inline
  const nodeMap = new Map();
  osmData.elements.forEach(element => {
    if (element.type === 'node' && element.lat !== undefined && element.lon !== undefined) {
      nodeMap.set(element.id, {
        lat: element.lat,
        lon: element.lon
      });
    }
  });

  console.log(`🗺️ Built nodeMap with ${nodeMap.size} nodes`);

  // Process ways (power lines)
  osmData.elements.forEach(element => {
    if (element.type === 'way' && element.tags && element.tags.power) {
      let coordinates = [];

      // Method 1: Use geometry array if available (some Overpass formats)
      if (element.geometry && Array.isArray(element.geometry) && element.geometry.length > 0) {
        console.log(`✓ Way ${element.id} has inline geometry with ${element.geometry.length} points`);
        coordinates = element.geometry.map(point => [point.lon, point.lat]);
      }
      // Method 2: Reconstruct from node IDs using the nodeMap we built
      else if (element.nodes && element.nodes.length > 0) {
        console.log(`✓ Way ${element.id} has ${element.nodes.length} node references`);
        const resolvedCount = element.nodes.reduce((count, nodeId) => {
          const node = nodeMap.get(nodeId);
          if (node) {
            coordinates.push([node.lon, node.lat]);
            return count + 1;
          }
          return count;
        }, 0);

        if (resolvedCount < element.nodes.length) {
          console.warn(`⚠️ Way ${element.id}: Resolved only ${resolvedCount}/${element.nodes.length} nodes`);
        }
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
      } else {
        console.warn(`⚠️ Way ${element.id}: Skipped - only ${coordinates.length} coordinates`);
      }
    }

    // Process point towers
    if (element.type === 'node' && element.tags && element.tags.power === 'tower') {
      if (element.lat !== undefined && element.lon !== undefined) {
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
    }
  });

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
  const data = await fetchTransmissionLines(region, regionKey);

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
