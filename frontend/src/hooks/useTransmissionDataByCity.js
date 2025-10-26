import { useState, useEffect } from 'react';
import { fetchTransmissionDataCached } from '../data/transmissionData';
import { CITY_CONFIG } from '../data/cityConfig';

/**
 * Hook to load real transmission data for a specific city
 * @param {string} cityKey - The city key from CITY_CONFIG (e.g., 'paradise', 'los-angeles', 'san-francisco')
 * @returns {Object} - { data, loading, error, cityName, loadingPercent }
 */
export const useTransmissionDataByCity = (cityKey) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingPercent, setLoadingPercent] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setLoadingPercent(0);
      setError(null);

      try {
        if (!cityKey || !CITY_CONFIG[cityKey]) {
          throw new Error(`Invalid city key: ${cityKey}`);
        }

        const cityConfig = CITY_CONFIG[cityKey];
        const regionKey = cityConfig.region;

        if (!regionKey) {
          throw new Error(`No transmission data region configured for city: ${cityKey}`);
        }

        console.log(`Loading transmission data for ${cityConfig.name} (${regionKey})`);

        // Add staggered delay to prevent all cities from hammering Overpass API simultaneously
        // This helps avoid rate limiting and API timeouts
        const cityIndex = Object.keys(CITY_CONFIG).indexOf(cityKey);
        const delayMs = cityIndex * 500; // 0ms, 500ms, 1000ms for first, second, third city

        if (delayMs > 0) {
          console.log(`Staggering request by ${delayMs}ms to avoid API rate limits...`);
          await new Promise(resolve => setTimeout(resolve, delayMs));
        }

        // Use simple caching approach
        const transmissionData = await fetchTransmissionDataCached(regionKey);

        // Convert transmission data to cable network format for compatibility
        // with existing LosAngelesMap layers
        const convertedData = convertTransmissionToCableFormat(transmissionData, cityConfig);

        setData(convertedData);
        setLoadingPercent(100);
      } catch (err) {
        console.error(`Error loading transmission data for ${cityKey}:`, err);
        setError(err.message);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [cityKey]);

  const cityConfig = CITY_CONFIG[cityKey] || {};

  return {
    data,
    loading,
    error,
    loadingPercent,
    cityName: cityConfig.name || cityKey
  };
};

/**
 * Convert real transmission data to cable network format for layer rendering
 * This allows us to reuse the existing layer styles with real OSM data
 */
const convertTransmissionToCableFormat = (transmissionData, cityConfig) => {
  if (!transmissionData || !transmissionData.features) {
    return { type: 'FeatureCollection', features: [] };
  }

  // Color coding for different cities
  const cityColors = {
    'paradise': '#00ff88',      // Bright green for Paradise
    'los-angeles': '#ff6b35',   // Orange for LA
    'san-francisco': '#9370db'  // Purple for SF
  };

  const cityColor = cityColors[cityConfig.key] || '#00ff88';

  const convertedFeatures = transmissionData.features
    .filter(feature => feature.geometry?.type === 'LineString') // Only keep lines, skip towers
    .map(feature => {
      return {
        type: 'Feature',
        properties: {
          ...feature.properties,
          // Add cable network format properties for layer compatibility
          color: cityColor,
          type: 'transmission-line',
          voltage: feature.properties.voltage || 'Unknown',
          operator: feature.properties.operator || 'Unknown',
          source: 'OpenStreetMap'
        },
        geometry: feature.geometry
      };
    });

  return {
    type: 'FeatureCollection',
    features: convertedFeatures,
    metadata: {
      city: cityConfig.name,
      cityKey: cityConfig.key,
      source: 'OpenStreetMap via Overpass API',
      license: 'ODbL 1.0'
    }
  };
};

export default useTransmissionDataByCity;
