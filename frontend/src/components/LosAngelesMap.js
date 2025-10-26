import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronRight } from 'lucide-react';
import { useCity } from '../contexts/CityContext';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './LosAngelesMap.css';

// Modular utilities
import { CITY_CONFIG, getNextCity } from '../data/cityConfig';
import { useTransmissionDataByCity } from '../hooks/useTransmissionDataByCity';

// Set your Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const LosAngelesMap = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [cityMovement, setCityMovement] = useState(false);
  const [selectedCable, setSelectedCable] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [isLoadingRisk, setIsLoadingRisk] = useState(false);
  const { currentCity, setCurrentCity } = useCity();

  // Load real transmission data based on current city
  const { data: transmissionData } = useTransmissionDataByCity(currentCity);

  // Anthropic API function for risk assessment
  const assessCableRisk = async (cableData) => {
    setIsLoadingRisk(true);
    console.log('Assessing cable risk for:', cableData);
    
    // Simulate Anthropic API response with varied risk levels
    setTimeout(() => {
      let riskLevel, simulatedResponse;
      
      // Determine risk level based on temperature and cable characteristics
      if (cableData.temperature <= 35) {
        riskLevel = 'LOW';
        simulatedResponse = `LOW RISK: Cable operating at optimal temperature of ${cableData.temperature}°C with minimal degradation risk. Smart city infrastructure stable, energy efficiency maintained, and preventive maintenance costs minimized.`;
      } else if (cableData.temperature >= 45) {
        riskLevel = 'MEDIUM';
        simulatedResponse = `MEDIUM RISK: Cable operating within acceptable parameters but monitoring recommended. Temperature: ${cableData.temperature}°C suggests potential early degradation. Proactive maintenance advised to prevent smart city failures and optimize energy consumption.`;
      } else {
        // Random assignment for temperatures between 36-44°C
        const isLowRisk = Math.random() < 0.3; // 30% chance of LOW risk
        if (isLowRisk) {
          riskLevel = 'LOW';
          simulatedResponse = `LOW RISK: Cable operating at optimal temperature of ${cableData.temperature}°C with minimal degradation risk. Smart city infrastructure stable, energy efficiency maintained, and preventive maintenance costs minimized.`;
        } else {
          riskLevel = 'MEDIUM';
          simulatedResponse = `MEDIUM RISK: Cable operating within acceptable parameters but monitoring recommended. Temperature: ${cableData.temperature}°C suggests potential early degradation. Proactive maintenance advised to prevent smart city failures and optimize energy consumption.`;
        }
      }
      
      setRiskAssessment({
        level: riskLevel,
        description: simulatedResponse,
        cableData: cableData
      });
      
      setIsLoadingRisk(false);
    }, 1000); // 1 second delay to simulate API call
  };

  // City switching function - Uses modular CITY_CONFIG
  const switchCity = () => {
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
        easing: (t) => t * (2 - t) // Smooth easing
      });
    }
  };

  // Get current city name - Uses modular CITY_CONFIG
  const getCityName = () => CITY_CONFIG[currentCity].name;


  useEffect(() => {
    if (map.current) return; // Initialize map only once

    try {
        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: 'mapbox://styles/mapbox/dark-v11', // Dark modern style
          center: [-121.5795, 39.7596], // Paradise, CA center (Camp Fire location)
          zoom: 14, // Wider view to see Tower 27/222 and surrounding area
          pitch: 60, // 3D perspective
          bearing: 0,
          antialias: true,
          accessToken: process.env.REACT_APP_MAPBOX_TOKEN
        });

      map.current.on('load', () => {
        console.log('Map loaded successfully!');
        setMapLoaded(true);

        // Start city movement animation
        setTimeout(() => {
          setCityMovement(true);
        }, 1000);
      });

      map.current.on('error', (e) => {
        console.error('Map error:', e.error?.message || e.error || e);
      });

    } catch (error) {
      console.error('Failed to initialize map:', error);
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Initialize source and layers when map is loaded
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    console.log('Initializing transmission data source and layers...');

    // Add transmission network data source
    if (!map.current.getSource('cable-network')) {
      console.log('Adding cable-network source');
      map.current.addSource('cable-network', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
    }

    // Add transmission line layer
    if (!map.current.getLayer('transmission-lines-real')) {
      console.log('Adding transmission-lines-real layer');
      map.current.addLayer({
        id: 'transmission-lines-real',
        type: 'line',
        source: 'cable-network',
        filter: ['==', ['geometry-type'], 'LineString'],
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 2,
            15, 4,
            17, 6,
            20, 10
          ],
          'line-opacity': 0.9
        }
      });
      console.log('✅ Added transmission-lines-real layer');
    }

    // Add interactive event handlers for transmission lines
    map.current.on('mouseenter', 'transmission-lines-real', () => {
      map.current.getCanvas().style.cursor = 'pointer';
    });

    map.current.on('mouseleave', 'transmission-lines-real', () => {
      map.current.getCanvas().style.cursor = '';
    });

    map.current.on('click', 'transmission-lines-real', (e) => {
      if (e.features && e.features.length > 0) {
        const feature = e.features[0];
        console.log('Clicked transmission line:', feature);
        assessCableRisk({
          name: feature.properties.name || 'Transmission Line',
          voltage: feature.properties.voltage || 'Unknown',
          temperature: Math.random() * 60 + 20 // Simulate temp 20-80°C
        });
        setSelectedCable(feature);
      }
    });
  }, [mapLoaded]);

  // Pan map to correct city when currentCity changes
  useEffect(() => {
    if (!map.current) return;

    const cityConfig = CITY_CONFIG[currentCity];
    if (!cityConfig) return;

    console.log(`🗺️ Panning map to city: ${currentCity}`);
    map.current.flyTo({
      center: cityConfig.center,
      zoom: cityConfig.zoom,
      pitch: cityConfig.pitch,
      bearing: cityConfig.bearing,
      duration: 2000
    });
  }, [currentCity]);

  // Update map source when transmission data changes (city switch or data reload)
  useEffect(() => {
    console.log('Data update effect fired. Map exists:', !!map.current, 'Source exists:', !!map.current?.getSource('cable-network'), 'Data exists:', !!transmissionData, 'MapLoaded:', mapLoaded);

    if (!map.current) {
      console.log('Map not ready yet');
      return;
    }

    if (!mapLoaded) {
      console.log('Map not fully loaded yet');
      return;
    }

    const source = map.current.getSource('cable-network');
    if (!source) {
      console.log('Cable-network source not found, waiting for map to be fully loaded');
      return;
    }

    if (!transmissionData) {
      console.log('Transmission data not loaded yet');
      return;
    }

    console.log(`✅ Updating transmission data for city: ${currentCity}`);
    const totalFeatures = transmissionData.features?.length || 0;
    const lineCount = transmissionData.features?.filter(f => f.geometry?.type === 'LineString').length || 0;
    const pointCount = transmissionData.features?.filter(f => f.geometry?.type === 'Point').length || 0;
    console.log(`📊 TRANSMISSION DATA SUMMARY:`);
    console.log(`   Total Features: ${totalFeatures}`);
    console.log(`   Transmission Lines: ${lineCount}`);
    console.log(`   Towers/Nodes: ${pointCount}`);

    // Check sample feature colors
    const sampleLine = transmissionData.features?.find(f => f.geometry?.type === 'LineString');
    const samplePoint = transmissionData.features?.find(f => f.geometry?.type === 'Point');
    console.log('Sample LineString color:', sampleLine?.properties?.color);
    console.log('Sample Point color:', samplePoint?.properties?.color);

    console.log('Calling setData on cable-network source...');
    source.setData(transmissionData);
    console.log('✅ setData complete');
  }, [transmissionData, currentCity, mapLoaded]);

  return (
    <motion.div 
      className="los-angeles-map-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >

      {/* Network Overview */}
      <motion.div 
        className="network-overview"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.5 }}
      >
        <div className="overview-title">
          {getCityName()}
          <motion.button 
            className="city-switch-btn"
            onClick={switchCity}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.6 }}
          >
            <ChevronRight size={20} />
          </motion.button>
        </div>
        
        {/* Cable Legend */}
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
            <div className="legend-line solid" style={{backgroundColor: '#ff6b35'}}></div>
            <span>Transmission Line</span>
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

        {/* Animated Moving Elements */}
        {cityMovement && (
          <>
            {/* Moving Data Packets */}
            <motion.div
              className="data-packet"
              initial={{ x: -50, y: 100, opacity: 0 }}
              animate={{ 
                x: [0, 200, 400, 600, 800],
                y: [100, 80, 120, 90, 110],
                opacity: [0, 1, 1, 1, 0]
              }}
              transition={{ 
                duration: 8,
                repeat: Infinity,
                ease: "linear"
              }}
            >
              <div className="packet-icon">📡</div>
            </motion.div>
            
            <motion.div
              className="data-packet"
              initial={{ x: -50, y: 200, opacity: 0 }}
              animate={{ 
                x: [0, 150, 300, 500, 700],
                y: [200, 180, 220, 190, 210],
                opacity: [0, 1, 1, 1, 0]
              }}
              transition={{ 
                duration: 6,
                repeat: Infinity,
                ease: "linear",
                delay: 2
              }}
            >
              <div className="packet-icon">⚡</div>
            </motion.div>
            
            <motion.div
              className="data-packet"
              initial={{ x: -50, y: 300, opacity: 0 }}
              animate={{ 
                x: [0, 180, 350, 550, 750],
                y: [300, 280, 320, 290, 310],
                opacity: [0, 1, 1, 1, 0]
              }}
              transition={{ 
                duration: 7,
                repeat: Infinity,
                ease: "linear",
                delay: 4
              }}
            >
              <div className="packet-icon">🔋</div>
            </motion.div>

            {/* Floating Monitoring Signals */}
            <motion.div
              className="monitoring-signal"
              initial={{ x: 100, y: 150, opacity: 0 }}
              animate={{ 
                x: [100, 120, 140, 160, 180],
                y: [150, 140, 160, 150, 140],
                opacity: [0, 0.8, 1, 0.8, 0]
              }}
              transition={{ 
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <div className="signal-wave"></div>
            </motion.div>
            
            <motion.div
              className="monitoring-signal"
              initial={{ x: 300, y: 250, opacity: 0 }}
              animate={{ 
                x: [300, 320, 340, 360, 380],
                y: [250, 240, 260, 250, 240],
                opacity: [0, 0.8, 1, 0.8, 0]
              }}
              transition={{ 
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1.5
              }}
            >
              <div className="signal-wave"></div>
            </motion.div>

            {/* Energy Flow Particles */}
            <motion.div
              className="energy-particle"
              initial={{ x: 50, y: 50 }}
              animate={{ 
                x: [50, 200, 350, 500, 650],
                y: [50, 100, 80, 120, 90],
                scale: [0.5, 1, 0.8, 1.2, 0.5]
              }}
              transition={{ 
                duration: 5,
                repeat: Infinity,
                ease: "linear"
              }}
            >
              <div className="particle-glow"></div>
            </motion.div>
            
            <motion.div
              className="energy-particle"
              initial={{ x: 80, y: 400 }}
              animate={{ 
                x: [80, 250, 400, 550, 700],
                y: [400, 350, 380, 360, 340],
                scale: [0.3, 1, 0.6, 1.1, 0.3]
              }}
              transition={{ 
                duration: 6,
                repeat: Infinity,
                ease: "linear",
                delay: 2.5
              }}
            >
              <div className="particle-glow"></div>
            </motion.div>

            {/* Network Activity Indicators */}
            <motion.div
              className="network-activity"
              initial={{ x: 200, y: 100, opacity: 0 }}
              animate={{ 
                opacity: [0, 1, 0],
                scale: [0.8, 1.2, 0.8]
              }}
              transition={{ 
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <div className="activity-ring"></div>
            </motion.div>
            
            <motion.div
              className="network-activity"
              initial={{ x: 500, y: 300, opacity: 0 }}
              animate={{ 
                opacity: [0, 1, 0],
                scale: [0.8, 1.2, 0.8]
              }}
              transition={{ 
                duration: 2.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1
              }}
            >
              <div className="activity-ring"></div>
            </motion.div>
          </>
        )}
        
      </motion.div>

      {/* Cable Risk Assessment Modal */}
      {selectedCable && (
        <motion.div 
          className="cable-modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => {
            setSelectedCable(null);
            setRiskAssessment(null);
          }}
        >
          <motion.div 
            className="cable-modal"
            initial={{ opacity: 0, scale: 0.8, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 50 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>{selectedCable.name}</h3>
              <button 
                className="close-btn"
                onClick={() => {
                  setSelectedCable(null);
                  setRiskAssessment(null);
                }}
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <div className="cable-info">
                <div className="info-row">
                  <span className="label">Voltage:</span>
                  <span className="value">{selectedCable.voltage}</span>
                </div>
                <div className="info-row">
                  <span className="label">Type:</span>
                  <span className="value">{selectedCable.type}</span>
                </div>
                <div className="info-row">
                  <span className="label">Capacity:</span>
                  <span className="value">{selectedCable.capacity}</span>
                </div>
                {selectedCable.temperature && (
                  <div className="info-row">
                    <span className="label">Temperature:</span>
                    <span className="value">{selectedCable.temperature}°C</span>
                  </div>
                )}
                {selectedCable.vibration && (
                  <div className="info-row">
                    <span className="label">Vibration:</span>
                    <span className="value">{selectedCable.vibration} m/s²</span>
                  </div>
                )}
                {selectedCable.strain && (
                  <div className="info-row">
                    <span className="label">Strain:</span>
                    <span className="value">{selectedCable.strain} mm/m</span>
                  </div>
                )}
              </div>

              <div className="risk-assessment">
                <h4>Risk Assessment</h4>
                {isLoadingRisk ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Analyzing cable health...</span>
                  </div>
                ) : riskAssessment ? (
                  <div className={`risk-result risk-${riskAssessment.level.toLowerCase()}`}>
                    <div className="risk-level">
                      {riskAssessment.level} RISK
                    </div>
                    <div className="risk-description">
                      {riskAssessment.description}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default LosAngelesMap;
