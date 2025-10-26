/**
 * Custom hook for Mapbox click handlers
 * Encapsulates common click/hover behavior patterns
 */

import { useCallback } from 'react';

export const useMapClickHandlers = (map, setSelectedCable, assessCableRisk) => {
  // Handler for underground cables
  const handleUndergroundCableClick = useCallback(
    (e) => {
      if (!map.current) return;

      const features = map.current.queryRenderedFeatures(e.point, {
        layers: ['underground-cables']
      });

      if (features.length > 0) {
        const cableData = features[0].properties;
        setSelectedCable(cableData);
        assessCableRisk(cableData);
      }
    },
    [map, setSelectedCable, assessCableRisk]
  );

  // Handler for overhead cables
  const handleOverheadCableClick = useCallback(
    (e) => {
      if (!map.current) return;

      const features = map.current.queryRenderedFeatures(e.point, {
        layers: ['overhead-cables']
      });

      if (features.length > 0) {
        const cableData = features[0].properties;
        setSelectedCable(cableData);
        assessCableRisk(cableData);
      }
    },
    [map, setSelectedCable, assessCableRisk]
  );

  // Handler for transmission towers (Tower 27/222)
  const handleTransmissionTowerClick = useCallback(
    (e) => {
      if (!map.current) return;

      const features = map.current.queryRenderedFeatures(e.point, {
        layers: ['transmission-towers']
      });

      if (features.length > 0) {
        const towerData = features[0].properties;
        setSelectedCable(towerData);

        alert(
          `${towerData.name} - ${towerData.location}\n\n` +
          `Status: ${towerData.status}\n` +
          `CCI: ${towerData.cci || 'N/A'}\n\n` +
          `Click "Camp Fire Analysis" tab for time-slider simulation.`
        );
      }
    },
    [map, setSelectedCable]
  );

  return {
    handleUndergroundCableClick,
    handleOverheadCableClick,
    handleTransmissionTowerClick
  };
};
