/**
 * Tile Manager - Handles subdividing large regions into smaller tiles for efficient data loading
 * Uses a quadtree-like approach to partition bounding boxes
 */

/**
 * Generate tiles for a bounding box at a given zoom level
 * @param {Object} bbox - {minLat, maxLat, minLon, maxLon}
 * @param {number} zoomLevel - Zoom level (10-16 typical)
 * @returns {Array} Array of tile objects with {minLat, maxLat, minLon, maxLon, id}
 */
export const generateTiles = (bbox, zoomLevel = 10) => {
  const { minLat, maxLat, minLon, maxLon } = bbox;
  const tiles = [];

  // Calculate number of subdivisions based on zoom level
  // zoom 10 = 2x2 = 4 tiles, zoom 12 = 4x4 = 16 tiles, zoom 14 = 8x8 = 64 tiles
  const divisionsPerSide = Math.pow(2, zoomLevel - 9);

  const latStep = (maxLat - minLat) / divisionsPerSide;
  const lonStep = (maxLon - minLon) / divisionsPerSide;

  let tileId = 0;
  for (let latIdx = 0; latIdx < divisionsPerSide; latIdx++) {
    for (let lonIdx = 0; lonIdx < divisionsPerSide; lonIdx++) {
      tiles.push({
        id: `${zoomLevel}_${tileId}`,
        zoomLevel,
        minLat: minLat + (latIdx * latStep),
        maxLat: minLat + ((latIdx + 1) * latStep),
        minLon: minLon + (lonIdx * lonStep),
        maxLon: minLon + ((lonIdx + 1) * lonStep),
        index: tileId
      });
      tileId++;
    }
  }

  return tiles;
};

/**
 * Cache tile data in localStorage with expiration
 */
export const cacheTile = (tileId, data, expirationHours = 24) => {
  try {
    const cacheEntry = {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + (expirationHours * 60 * 60 * 1000)
    };
    localStorage.setItem(`tile_${tileId}`, JSON.stringify(cacheEntry));
  } catch (error) {
    console.warn('Failed to cache tile:', error);
  }
};

/**
 * Retrieve cached tile data if not expired
 */
export const getCachedTile = (tileId) => {
  try {
    const cached = localStorage.getItem(`tile_${tileId}`);
    if (!cached) return null;

    const cacheEntry = JSON.parse(cached);

    // Check if expired
    if (Date.now() > cacheEntry.expiresAt) {
      localStorage.removeItem(`tile_${tileId}`);
      return null;
    }

    return cacheEntry.data;
  } catch (error) {
    console.warn('Failed to retrieve cached tile:', error);
    return null;
  }
};

/**
 * Clear all cached tiles
 */
export const clearAllTileCache = () => {
  try {
    const keys = Object.keys(localStorage).filter(k => k.startsWith('tile_'));
    keys.forEach(key => localStorage.removeItem(key));
    console.log(`Cleared ${keys.length} cached tiles`);
  } catch (error) {
    console.warn('Failed to clear tile cache:', error);
  }
};

/**
 * Simplify coordinate precision to reduce data size
 * Reduces from ~8 decimal places (1mm precision) to 4 decimal places (~11m precision)
 */
export const simplifyCoordinates = (coordinates, precision = 4) => {
  const factor = Math.pow(10, precision);
  return coordinates.map(coord => [
    Math.round(coord[0] * factor) / factor,
    Math.round(coord[1] * factor) / factor
  ]);
};

/**
 * Filter transmission features by voltage level (for lower zoom levels, show only major lines)
 */
export const filterByVoltage = (features, minVoltage = 0) => {
  return features.filter(feature => {
    if (feature.geometry.type !== 'LineString') return true; // Keep all towers/points

    const voltage = feature.properties.voltage;
    if (!voltage) return false;

    // Extract numeric voltage value
    const numericVoltage = parseInt(voltage);
    return numericVoltage >= minVoltage;
  });
};

/**
 * Merge multiple tile datasets into a single GeoJSON FeatureCollection
 */
export const mergeTiles = (tilesData) => {
  const allFeatures = [];

  tilesData.forEach(tileData => {
    if (tileData && tileData.features) {
      allFeatures.push(...tileData.features);
    }
  });

  return {
    type: 'FeatureCollection',
    features: allFeatures
  };
};

/**
 * Calculate zoom range for optimal performance
 * Lower zoom = coarser data, Higher zoom = finer detail
 */
export const getZoomStrategy = (currentZoom) => {
  return {
    coarseZoom: 10,           // Always fetch coarse overview at zoom 10
    mediumZoom: 12,           // Fetch medium detail at zoom 12+
    detailZoom: 14,           // Fetch detailed data at zoom 14+
    fetchCoarse: currentZoom >= 10,
    fetchMedium: currentZoom >= 12,
    fetchDetail: currentZoom >= 14,
    voltageFilter: currentZoom >= 14 ? 0 : 100000  // Show all lines when zoomed in, only high voltage when zoomed out
  };
};
