/**
 * CableNetworkMap Component (REFACTORED)
 *
 * A cleaner, more modular version of LosAngelesMap
 * Uses composition, custom hooks, and separated concerns
 *
 * Key improvements:
 * - Modular hook-based architecture
 * - Separated configuration from logic
 * - Reusable layer rendering
 * - Better code organization
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft } from 'lucide-react';
import { useCity } from '../../contexts/CityContext';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import '../LosAngelesMap.css';

// Import configuration and utilities
import { CITY_CONFIG, getNextCity, getPrevCity } from '../../data/cityConfig';
import { addMapLayers } from './MapLayers';
import { useMapClickHandlers } from '../../hooks/useMapClickHandlers';
import { useMapHoverEffects } from '../../hooks/useMapHoverEffects';

// Set your Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const CableNetworkMap = () => {
  // Refs
  const mapContainer = useRef(null);
  const map = useRef(null);

  // State from City Context
  const { currentCity, setCurrentCity } = useCity();

  // Local state
  const [cityMovement, setCityMovement] = useState(false);
  const [selectedCable, setSelectedCable] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [isLoadingRisk, setIsLoadingRisk] = useState(false);

  /**
   * Cable Risk Assessment
   * Simulate Anthropic API for risk evaluation
   */
  const assessCableRisk = useCallback((cableData) => {
    setIsLoadingRisk(true);

    setTimeout(() => {
      const tempThreshold = cableData.temperature || 40;
      let riskLevel, description;

      if (tempThreshold <= 35) {
        riskLevel = 'LOW';
        description = `LOW RISK: Cable operating at optimal temperature of ${tempThreshold}°C. Smart city infrastructure stable.`;
      } else if (tempThreshold >= 45) {
        riskLevel = 'MEDIUM';
        description = `MEDIUM RISK: Temperature ${tempThreshold}°C suggests potential degradation. Proactive maintenance advised.`;
      } else {
        riskLevel = Math.random() < 0.3 ? 'LOW' : 'MEDIUM';
        description = riskLevel === 'LOW'
          ? `LOW RISK: Cable operating at ${tempThreshold}°C with minimal risk.`
          : `MEDIUM RISK: Temperature ${tempThreshold}°C warrants monitoring.`;
      }

      setRiskAssessment({
        level: riskLevel,
        description,
        cableData
      });

      setIsLoadingRisk(false);
    }, 1000);
  }, []);

  // Custom hooks for interactions
  const clickHandlers = useMapClickHandlers(map, setSelectedCable, assessCableRisk);
  const hoverEffects = useMapHoverEffects(map);

  /**
   * Switch to next city
   */
  const handleCitySwitch = useCallback(() => {
    const nextCity = getNextCity(currentCity);
    setCurrentCity(nextCity);

    if (map.current) {
      const cityConfig = CITY_CONFIG[nextCity];
      map.current.flyTo({
        center: cityConfig.center,
        zoom: cityConfig.zoom,
        pitch: cityConfig.pitch,
        bearing: cityConfig.bearing,
        duration: 2500,
        easing: (t) => t * (2 - t)
      });
    }
  }, [currentCity, setCurrentCity]);

  /**
   * Switch to previous city
   */
  const handlePrevCitySwitch = useCallback(() => {
    const prevCity = getPrevCity(currentCity);
    setCurrentCity(prevCity);

    if (map.current) {
      const cityConfig = CITY_CONFIG[prevCity];
      map.current.flyTo({
        center: cityConfig.center,
        zoom: cityConfig.zoom,
        pitch: cityConfig.pitch,
        bearing: cityConfig.bearing,
        duration: 2500,
        easing: (t) => t * (2 - t)
      });
    }
  }, [currentCity, setCurrentCity]);

  /**
   * Initialize Mapbox
   */
  useEffect(() => {
    if (map.current) return;

    try {
      const cityConfig = CITY_CONFIG[currentCity];
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/dark-v11',
        center: cityConfig.center,
        zoom: cityConfig.zoom,
        pitch: cityConfig.pitch,
        bearing: cityConfig.bearing,
        antialias: true,
        accessToken: process.env.REACT_APP_MAPBOX_TOKEN
      });

      map.current.on('load', () => {
        console.log('Map loaded successfully!');

        // Start animations after load
        setTimeout(() => {
          setCableAnimations({ bundles: true, cables: true, sensors: true });
          setCityMovement(true);
        }, 1000);

        // Add all map layers
        addMapLayers(map, cableNetworkData);

        // Attach hover effects to layers
        hoverEffects.attachLineHoverEffect('underground-cables');
        hoverEffects.attachLineHoverEffect('overhead-cables');
        hoverEffects.attachCircleHoverEffect('transmission-towers');

        // Attach click handlers
        map.current.on('click', 'underground-cables', clickHandlers.handleUndergroundCableClick);
        map.current.on('click', 'overhead-cables', clickHandlers.handleOverheadCableClick);
        map.current.on('click', 'transmission-towers', clickHandlers.handleTransmissionTowerClick);
      });

      return () => {
        // Cleanup on unmount
        if (map.current) {
          map.current.remove();
          map.current = null;
        }
      };
    } catch (error) {
      console.error('Error initializing map:', error);
    }
  }, []);

  /**
   * ============================================================
   * CABLE NETWORK DATA
   * TODO: Extract this to a separate data file
   * ============================================================
   */
  const cableNetworkData = {
    type: 'FeatureCollection',
    features: [
      // Placeholder - Data copied from original LosAngelesMap.js
      // This large data structure should be extracted to src/data/cities/
    ]
  };

  // Temporarily return a message
  // In production, cableNetworkData would be properly populated
  return (
    <motion.div
      className="los-angeles-map-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <motion.div
        className="network-overview"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <div className="overview-title">
          {CITY_CONFIG[currentCity].name}
          <motion.button
            className="city-switch-btn"
            onClick={handleCitySwitch}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.6 }}
          >
            <ChevronRight size={20} />
          </motion.button>
        </div>

        {/* Legend - TODO: Extract to separate component */}
        <motion.div
          className="cable-legend"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
        >
          <motion.div
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.8 }}
          >
            <div className="legend-bundle" style={{backgroundColor: '#333333'}}></div>
            <span>Cable Bundle</span>
          </motion.div>
          <motion.div
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.9 }}
          >
            <div className="legend-line solid" style={{backgroundColor: '#ff4444'}}></div>
            <span>Phase A</span>
          </motion.div>
          <motion.div
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 1.0 }}
          >
            <div className="legend-line solid" style={{backgroundColor: '#00d4ff'}}></div>
            <span>Phase B</span>
          </motion.div>
          <motion.div
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 1.1 }}
          >
            <div className="legend-line solid" style={{backgroundColor: '#00ff88'}}></div>
            <span>Phase C</span>
          </motion.div>
          <motion.div
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 1.2 }}
          >
            <div className="legend-circle" style={{backgroundColor: '#00ff88'}}></div>
            <span>Monitor Sensor</span>
          </motion.div>
          <motion.div
            className="legend-item"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 1.3 }}
          >
            <div className="legend-circle" style={{backgroundColor: '#00ff88', border: '3px solid white'}}></div>
            <span>Tower 27/222</span>
          </motion.div>
        </motion.div>
      </motion.div>

      <motion.div
        className="map-wrapper"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.4 }}
      >
        <div ref={mapContainer} className="map-container" />
      </motion.div>
    </motion.div>
  );
};

export default CableNetworkMap;
