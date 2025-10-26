/**
 * Custom hook for Mapbox hover effects
 * Encapsulates hover styling and cursor changes
 */

import { useCallback } from 'react';

const DEFAULT_LINE_STYLE = {
  width: [
    'interpolate',
    ['linear'],
    ['zoom'],
    10, 3,
    15, 6,
    20, 12
  ],
  opacity: 0.9
};

const HOVER_LINE_STYLE = {
  width: [
    'interpolate',
    ['linear'],
    ['zoom'],
    10, 5,
    15, 10,
    20, 20
  ],
  opacity: 1
};

export const useMapHoverEffects = (map) => {
  // Set up hover effect for a line layer
  const attachLineHoverEffect = useCallback(
    (layerId) => {
      if (!map.current) return;

      map.current.on('mouseenter', layerId, () => {
        map.current.getCanvas().style.cursor = 'pointer';
        map.current.setPaintProperty(
          layerId,
          'line-width',
          HOVER_LINE_STYLE.width
        );
        map.current.setPaintProperty(
          layerId,
          'line-opacity',
          HOVER_LINE_STYLE.opacity
        );
      });

      map.current.on('mouseleave', layerId, () => {
        map.current.getCanvas().style.cursor = '';
        map.current.setPaintProperty(
          layerId,
          'line-width',
          DEFAULT_LINE_STYLE.width
        );
        map.current.setPaintProperty(
          layerId,
          'line-opacity',
          DEFAULT_LINE_STYLE.opacity
        );
      });
    },
    [map]
  );

  // Set up hover effect for a circle layer
  const attachCircleHoverEffect = useCallback(
    (layerId) => {
      if (!map.current) return;

      map.current.on('mouseenter', layerId, () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', layerId, () => {
        map.current.getCanvas().style.cursor = '';
      });
    },
    [map]
  );

  return {
    attachLineHoverEffect,
    attachCircleHoverEffect
  };
};
