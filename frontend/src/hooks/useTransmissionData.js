/**
 * Custom Hook: useTransmissionData
 * Fetches and manages real transmission line data from OpenStreetMap
 * Usage: const { data, loading, error } = useTransmissionData('PARADISE');
 */

import { useState, useEffect } from 'react';
import {
  fetchTransmissionDataCached,
  filterByVoltage,
  REGIONS
} from '../data/transmissionData';

export const useTransmissionData = (regionKey = 'PARADISE', options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch transmission data for the region
        const result = await fetchTransmissionDataCached(regionKey);

        if (!result) {
          setError('Failed to fetch transmission data');
          setLoading(false);
          return;
        }

        // Apply voltage filtering if specified
        let filteredData = result;
        if (options.minVoltage || options.maxVoltage) {
          const minV = options.minVoltage || 0;
          const maxV = options.maxVoltage || 1000000;
          filteredData = filterByVoltage(result, minV, maxV);
        }

        setData(filteredData);
        setLoading(false);
      } catch (err) {
        console.error('Error loading transmission data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    loadData();
  }, [regionKey]);

  return {
    data,
    loading,
    error,
    regionName: REGIONS[regionKey]?.name || 'Unknown Region'
  };
};
