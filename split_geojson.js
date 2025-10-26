const fs = require('fs');

console.log('Loading large GeoJSON file...');
const data = JSON.parse(fs.readFileSync('./public/data/california-transmission-lines.geojson', 'utf8'));

console.log(`Total features: ${data.features.length}`);

// Define region bounding boxes
const regions = {
  'paradise': {
    minLat: 39.5, maxLat: 40.0,
    minLon: -121.8, maxLon: -121.0
  },
  'san-francisco': {
    minLat: 37.3, maxLat: 38.0,
    minLon: -123.0, maxLon: -121.8
  },
  'los-angeles': {
    minLat: 33.8, maxLat: 34.2,
    minLon: -118.4, maxLon: -117.9
  }
};

// Split features by region
Object.entries(regions).forEach(([region, bbox]) => {
  const filtered = data.features.filter(feature => {
    if (!feature.geometry) return false;
    
    if (feature.geometry.type === 'LineString') {
      // Check if any coordinate is within bbox
      return feature.geometry.coordinates.some(coord => {
        const [lon, lat] = coord;
        return lat >= bbox.minLat && lat <= bbox.maxLat && 
               lon >= bbox.minLon && lon <= bbox.maxLon;
      });
    } else if (feature.geometry.type === 'Point') {
      const [lon, lat] = feature.geometry.coordinates;
      return lat >= bbox.minLat && lat <= bbox.maxLat && 
             lon >= bbox.minLon && lon <= bbox.maxLon;
    }
    return false;
  });

  const geojson = {
    type: 'FeatureCollection',
    features: filtered,
    metadata: {
      region,
      source: 'California Energy Commission GIS',
      bbox
    }
  };

  const filename = `./public/data/transmission-${region}.geojson`;
  fs.writeFileSync(filename, JSON.stringify(geojson));
  console.log(`✅ Created ${filename} with ${filtered.length} features`);
});

console.log('Done!');
