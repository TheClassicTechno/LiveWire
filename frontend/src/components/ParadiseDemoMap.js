import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './ParadiseDemoMap.css';
import TimeSlider from './TimeSlider';
import ComponentInfoPanel from './ComponentInfoPanel';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const ParadiseDemoMap = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date(2018, 9, 1)); // Oct 1, 2018
  const [componentData, setComponentData] = useState({});
  const [selectedComponent, setSelectedComponent] = useState('TOWER_27_222');
  const [loading, setLoading] = useState(false);
  const markersRef = useRef({});

  // Tower coordinates for Tower 27/222 (Camp Fire origin)
  const TOWER_27_222 = {
    id: 'TOWER_27_222',
    name: 'Tower 27/222 - C-Hook',
    lat: 39.8039,
    lon: -121.4487,
    location: 'Pulga, Feather River Canyon',
    built_year: 1919,
  };

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [TOWER_27_222.lon, TOWER_27_222.lat],
      zoom: 14,
      pitch: 45,
      bearing: 0,
    });

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  // Fetch data for selected date
  useEffect(() => {
    if (!mapLoaded) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        // For now, simulate data. In production, this would call your Flask API
        // fetch(`/api/snapshot/${selectedDate.toISOString().split('T')[0]}`)

        const simulatedData = generateSimulatedData(selectedDate);
        setComponentData(simulatedData);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
      setLoading(false);
    };

    fetchData();
  }, [selectedDate, mapLoaded]);

  // Update map markers when data changes
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Clear existing markers
    Object.values(markersRef.current).forEach(marker => marker.remove());
    markersRef.current = {};

    // Add new markers
    Object.values(componentData).forEach(component => {
      const el = document.createElement('div');
      el.className = `marker marker-${component.zone}`;
      el.innerHTML = `
        <div class="marker-dot"></div>
        <div class="marker-pulse"></div>
      `;

      el.addEventListener('click', () => {
        setSelectedComponent(component.component_id);
      });

      const marker = new mapboxgl.Marker(el)
        .setLngLat([component.lon, component.lat])
        .addTo(map.current);

      markersRef.current[component.component_id] = marker;
    });
  }, [componentData, mapLoaded]);

  // Generate simulated data based on date
  const generateSimulatedData = (date) => {
    const fireDate = new Date(2018, 10, 8); // Nov 8, 2018
    const daysUntilFire = Math.floor((fireDate - date) / (1000 * 60 * 60 * 24));

    // Critical alert date: 308 days before fire
    const criticalAlertDate = new Date(fireDate);
    criticalAlertDate.setDate(criticalAlertDate.getDate() - 308);

    let zone = 'green';
    let cci = 0.3;
    let progress = 0;

    if (date >= criticalAlertDate) {
      // After critical alert date, progressively get worse
      const daysSinceCritical = Math.floor((date - criticalAlertDate) / (1000 * 60 * 60 * 24));
      progress = Math.min(daysSinceCritical / 308, 1);

      if (progress < 0.3) {
        zone = 'yellow';
        cci = 0.6 + progress * 0.2;
      } else if (progress < 0.7) {
        zone = 'orange';
        cci = 0.8 + progress * 0.15;
      } else {
        zone = 'red';
        cci = 0.95;
      }
    }

    return {
      [TOWER_27_222.id]: {
        component_id: TOWER_27_222.id,
        name: TOWER_27_222.name,
        lat: TOWER_27_222.lat,
        lon: TOWER_27_222.lon,
        location: TOWER_27_222.location,
        built_year: TOWER_27_222.built_year,
        age_years: new Date().getFullYear() - TOWER_27_222.built_year,
        zone: zone,
        cci: cci,
        temperature: 65 + (Math.random() * 30),
        vibration: 0.15 + (cci * 0.5),
        strain: 120 + (cci * 200),
        wind_speed: 15 + (date >= criticalAlertDate ? (308 - daysUntilFire) / 308 * 40 : 0),
        daysUntilFire: daysUntilFire,
        criticalAlertDate: criticalAlertDate,
      }
    };
  };

  const selectedData = componentData[selectedComponent];

  return (
    <motion.div
      className="paradise-demo-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="demo-header">
        <h1>Camp Fire Prediction: Tower 27/222</h1>
        <p>Interactive 2016-2018 Analysis - How LiveWire Could Have Prevented the Disaster</p>
      </div>

      <TimeSlider
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
        minDate={new Date(2016, 0, 1)}
        maxDate={new Date(2018, 10, 8)}
      />

      <div className="map-and-info">
        <div className="map-section">
          <div ref={mapContainer} className="map-container" />
          {loading && <div className="loading-indicator">Loading data...</div>}
        </div>

        {selectedData && (
          <ComponentInfoPanel
            data={selectedData}
            fireDate={new Date(2018, 10, 8)}
          />
        )}
      </div>
    </motion.div>
  );
};

export default ParadiseDemoMap;
