import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronRight } from 'lucide-react';
import { useCity } from '../contexts/CityContext';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './LosAngelesMap.css';

// Set your Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const LosAngelesMap = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [cableAnimations, setCableAnimations] = useState({});
  const [cityMovement, setCityMovement] = useState(false);
  const [selectedCable, setSelectedCable] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [isLoadingRisk, setIsLoadingRisk] = useState(false);
  const { currentCity, setCurrentCity, getCurrentCityStats } = useCity();

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

  // City switching function
  const switchCity = () => {
    let newCity;
    if (currentCity === 'los-angeles') {
      newCity = 'san-francisco';
    } else if (currentCity === 'san-francisco') {
      newCity = 'paradise-city';
    } else if (currentCity === 'paradise-city') {
      newCity = 'new-york';
    } else {
      newCity = 'los-angeles';
    }
    
    setCurrentCity(newCity);
    
    if (map.current) {
      const cityData = {
        'los-angeles': {
          center: [-118.2500, 34.0500], // Downtown LA Financial District cables
          zoom: 17,
          pitch: 60,
          bearing: 0
        },
        'san-francisco': {
          center: [-122.4000, 37.7900], // SF Financial District cables
          zoom: 17,
          pitch: 60,
          bearing: 0
        },
        'paradise-city': {
          center: [-118.3000, 33.8000], // Paradise City center
          zoom: 17,
          pitch: 60,
          bearing: 0
        },
        'new-york': {
          center: [-74.0060, 40.7128], // NYC Financial District
          zoom: 17,
          pitch: 60,
          bearing: 0
        }
      };
      
      map.current.flyTo({
        center: cityData[newCity].center,
        zoom: cityData[newCity].zoom,
        pitch: cityData[newCity].pitch,
        bearing: cityData[newCity].bearing,
        duration: 2500,
        easing: (t) => t * (2 - t) // Smooth easing
      });
    }
  };

  const getCityName = () => {
    const cityNames = {
      'los-angeles': 'Los Angeles Cable Network',
      'san-francisco': 'San Francisco Cable Network',
      'paradise-city': 'Paradise City Cable Network',
      'new-york': 'New York City Cable Network'
    };
    return cityNames[currentCity];
  };

      // Los Angeles Cable Network Data - Multiple cables per route
  const cableNetworkData = {
    type: "FeatureCollection",
    features: [
      // Downtown LA Underground Cables - Phase A
      {
        type: "Feature",
        properties: {
          id: "cable-downtown-1a",
          name: "Downtown Underground Main - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#ff4444",
          type: "underground",
          phase: "A",
          temperature: 42,
          vibration: 0.15,
          strain: 0.08
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2500, 34.0500],
            [-118.2400, 34.0550],
            [-118.2300, 34.0600],
            [-118.2200, 34.0650]
          ]
        }
      },
      // Downtown LA Underground Cables - Phase B
      {
        type: "Feature",
        properties: {
          id: "cable-downtown-1b",
          name: "Downtown Underground Main - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#ffaa00",
          type: "underground",
          phase: "B",
          temperature: 38,
          vibration: 0.12,
          strain: 0.06
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2502, 34.0502],
            [-118.2402, 34.0552],
            [-118.2302, 34.0602],
            [-118.2202, 34.0652]
          ]
        }
      },
      // Downtown LA Underground Cables - Phase C
      {
        type: "Feature",
        properties: {
          id: "cable-downtown-1c",
          name: "Downtown Underground Main - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#00d4ff",
          type: "underground",
          phase: "C",
          temperature: 40,
          vibration: 0.18,
          strain: 0.09
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2498, 34.0498],
            [-118.2398, 34.0548],
            [-118.2298, 34.0598],
            [-118.2198, 34.0648]
          ]
        }
      },
      // Financial District Underground - Phase A
      {
        type: "Feature",
        properties: {
          id: "cable-downtown-2a",
          name: "Financial District Underground - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#ff4444",
          type: "underground",
          phase: "A",
          temperature: 48,
          vibration: 0.25,
          strain: 0.12
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2450, 34.0450],
            [-118.2350, 34.0500],
            [-118.2250, 34.0550]
          ]
        }
      },
      // Financial District Underground - Phase B
      {
        type: "Feature",
        properties: {
          id: "cable-downtown-2b",
          name: "Financial District Underground - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#ffaa00",
          type: "underground",
          phase: "B",
          temperature: 44,
          vibration: 0.22,
          strain: 0.10
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2452, 34.0452],
            [-118.2352, 34.0502],
            [-118.2252, 34.0552]
          ]
        }
      },
      // Financial District Underground - Phase C
      {
        type: "Feature",
        properties: {
          id: "cable-downtown-2c",
          name: "Financial District Underground - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#00d4ff",
          type: "underground",
          phase: "C",
          temperature: 41,
          vibration: 0.19,
          strain: 0.08
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2448, 34.0448],
            [-118.2348, 34.0498],
            [-118.2248, 34.0548]
          ]
        }
      },
      // Hollywood Overhead Transmission Lines - Phase A
      {
        type: "Feature",
        properties: {
          id: "cable-hollywood-1a",
          name: "Hollywood Hills Overhead - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ff4444",
          type: "overhead",
          phase: "A",
          temperature: 68,
          vibration: 1.2,
          strain: 0.45
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3000, 34.1000],
            [-118.2900, 34.1050],
            [-118.2800, 34.1100],
            [-118.2700, 34.1150]
          ]
        }
      },
      // Hollywood Overhead Transmission Lines - Phase B
      {
        type: "Feature",
        properties: {
          id: "cable-hollywood-1b",
          name: "Hollywood Hills Overhead - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ffaa00",
          type: "overhead",
          phase: "B",
          temperature: 65,
          vibration: 1.1,
          strain: 0.42
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3002, 34.1002],
            [-118.2902, 34.1052],
            [-118.2802, 34.1102],
            [-118.2702, 34.1152]
          ]
        }
      },
      // Hollywood Overhead Transmission Lines - Phase C
      {
        type: "Feature",
        properties: {
          id: "cable-hollywood-1c",
          name: "Hollywood Hills Overhead - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#00d4ff",
          type: "overhead",
          phase: "C",
          temperature: 62,
          vibration: 1.0,
          strain: 0.38
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2998, 34.0998],
            [-118.2898, 34.1048],
            [-118.2798, 34.1098],
            [-118.2698, 34.1148]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-hollywood-2",
          name: "Sunset Strip Underground",
          voltage: "69kV",
          status: "operational",
          capacity: "250MW",
          color: "#ffaa00",
          type: "underground",
          temperature: 52,
          vibration: 0.35,
          strain: 0.15
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2950, 34.0950],
            [-118.2850, 34.1000],
            [-118.2750, 34.1050]
          ]
        }
      },
      // Santa Monica Mixed Infrastructure
      {
        type: "Feature",
        properties: {
          id: "cable-santa-monica-1",
          name: "Coastal Overhead Line",
          voltage: "138kV",
          status: "operational",
          capacity: "350MW",
          color: "#00bfff",
          type: "overhead",
          temperature: 58,
          vibration: 0.8,
          strain: 0.25
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.1500, 34.0000],
            [-118.1400, 34.0050],
            [-118.1300, 34.0100],
            [-118.1200, 34.0150]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-santa-monica-2",
          name: "Beach District Underground",
          voltage: "69kV",
          status: "operational",
          capacity: "200MW",
          color: "#ff69b4",
          type: "underground",
          temperature: 46,
          vibration: 0.28,
          strain: 0.11
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.1450, 33.9950],
            [-118.1350, 34.0000],
            [-118.1250, 34.0050]
          ]
        }
      },
      // Burbank Cable Routes
      {
        type: "Feature",
        properties: {
          id: "cable-burbank-1",
          name: "Media District Line",
          voltage: "138kV",
          status: "operational",
          capacity: "450MW",
          color: "#9370db",
          type: "overhead",
          temperature: 61,
          vibration: 0.9,
          strain: 0.32
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.4000, 34.1500],
            [-118.3900, 34.1550],
            [-118.3800, 34.1600],
            [-118.3700, 34.1650]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-burbank-2",
          name: "Studio Feed",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#32cd32",
          type: "underground",
          temperature: 49,
          vibration: 0.31,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3950, 34.1450],
            [-118.3850, 34.1500],
            [-118.3750, 34.1550]
          ]
        }
      },
      // West LA Cable Routes
      {
        type: "Feature",
        properties: {
          id: "cable-west-la-1",
          name: "Westside Transmission",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ff1493",
          type: "overhead",
          temperature: 59,
          vibration: 0.85,
          strain: 0.28
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2000, 34.0500],
            [-118.1900, 34.0550],
            [-118.1800, 34.0600],
            [-118.1700, 34.0650]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-west-la-2",
          name: "Beverly Hills Feed",
          voltage: "69kV",
          status: "operational",
          capacity: "250MW",
          color: "#ffd700",
          type: "underground",
          temperature: 47,
          vibration: 0.29,
          strain: 0.12
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.1950, 34.0450],
            [-118.1850, 34.0500],
            [-118.1750, 34.0550]
          ]
        }
      },
      // East LA Cable Routes
      {
        type: "Feature",
        properties: {
          id: "cable-east-la-1",
          name: "Eastside Main Line",
          voltage: "138kV",
          status: "operational",
          capacity: "350MW",
          color: "#00ced1",
          type: "overhead",
          temperature: 57,
          vibration: 0.75,
          strain: 0.24
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.1000, 34.0500],
            [-118.0900, 34.0550],
            [-118.0800, 34.0600],
            [-118.0700, 34.0650]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-east-la-2",
          name: "Industrial Feed",
          voltage: "69kV",
          status: "operational",
          capacity: "200MW",
          color: "#ff6347",
          type: "underground",
          temperature: 51,
          vibration: 0.33,
          strain: 0.14
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.0950, 34.0450],
            [-118.0850, 34.0500],
            [-118.0750, 34.0550]
          ]
        }
      },
      // Cable Monitoring Sensors
      {
        type: "Feature",
        properties: {
          id: "sensor-downtown-1",
          name: "Downtown Bundle Monitor",
          bundleId: "downtown-main",
          cables: ["cable-downtown-1a", "cable-downtown-1b", "cable-downtown-1c"],
          status: "monitoring",
          temperature: 45,
          vibration: 0.2,
          strain: 0.1,
          type: "sensor"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.2350, 34.0575]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-hollywood-1",
          name: "Hollywood Bundle Monitor",
          bundleId: "hollywood-hills",
          cables: ["cable-hollywood-1a", "cable-hollywood-1b", "cable-hollywood-1c"],
          status: "monitoring",
          temperature: 52,
          vibration: 0.8,
          strain: 0.3,
          type: "sensor"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.2850, 34.1075]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-financial-1",
          name: "Financial Bundle Monitor",
          bundleId: "financial-district",
          cables: ["cable-downtown-2a", "cable-downtown-2b", "cable-downtown-2c"],
          status: "monitoring",
          temperature: 38,
          vibration: 0.1,
          strain: 0.05,
          type: "sensor"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.2400, 34.0500]
        }
      },
      // San Francisco Cable Network Data - Multiple cables per route
      {
        type: "Feature",
        properties: {
          id: "cable-sf-financial-1a",
          name: "Financial District Main - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#ff4444",
          type: "overhead",
          phase: "A",
          temperature: 41,
          vibration: 0.19,
          strain: 0.14
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4000, 37.7900],
            [-122.3900, 37.7850],
            [-122.3800, 37.7800]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-financial-1b",
          name: "Financial District Main - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#00d4ff",
          type: "overhead",
          phase: "B",
          temperature: 39,
          vibration: 0.21,
          strain: 0.16
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4005, 37.7905],
            [-122.3905, 37.7855],
            [-122.3805, 37.7805]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-financial-1c",
          name: "Financial District Main - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#00ff88",
          type: "overhead",
          phase: "C",
          temperature: 43,
          vibration: 0.24,
          strain: 0.17
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4010, 37.7910],
            [-122.3910, 37.7860],
            [-122.3810, 37.7810]
          ]
        }
      },
      // Market Street SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-market-1a",
          name: "Market Street Feed - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "550MW",
          color: "#ff6b35",
          type: "overhead",
          phase: "A",
          temperature: 45,
          vibration: 0.28,
          strain: 0.19
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4050, 37.7850],
            [-122.3950, 37.7800],
            [-122.3850, 37.7750]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-market-1b",
          name: "Market Street Feed - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "550MW",
          color: "#9370db",
          type: "overhead",
          phase: "B",
          temperature: 37,
          vibration: 0.15,
          strain: 0.11
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4055, 37.7855],
            [-122.3955, 37.7805],
            [-122.3855, 37.7755]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-market-1c",
          name: "Market Street Feed - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "550MW",
          color: "#ffd700",
          type: "overhead",
          phase: "C",
          temperature: 40,
          vibration: 0.22,
          strain: 0.15
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4060, 37.7860],
            [-122.3960, 37.7810],
            [-122.3860, 37.7760]
          ]
        }
      },
      // Embarcadero SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-embarcadero-1a",
          name: "Embarcadero Line - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#ff1493",
          type: "overhead",
          phase: "A",
          temperature: 38,
          vibration: 0.18,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4020, 37.7880],
            [-122.3920, 37.7830],
            [-122.3820, 37.7780]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-embarcadero-1b",
          name: "Embarcadero Line - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#32cd32",
          type: "overhead",
          phase: "B",
          temperature: 42,
          vibration: 0.25,
          strain: 0.18
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4025, 37.7885],
            [-122.3925, 37.7835],
            [-122.3825, 37.7785]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-embarcadero-1c",
          name: "Embarcadero Line - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#00ced1",
          type: "overhead",
          phase: "C",
          temperature: 44,
          vibration: 0.31,
          strain: 0.21
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4030, 37.7890],
            [-122.3930, 37.7840],
            [-122.3830, 37.7790]
          ]
        }
      },
      // Mission District SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-mission-1a",
          name: "Mission District Feed - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#ff8c00",
          type: "underground",
          phase: "A",
          temperature: 46,
          vibration: 0.33,
          strain: 0.23
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4200, 37.7600],
            [-122.4100, 37.7550],
            [-122.4000, 37.7500]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-mission-1b",
          name: "Mission District Feed - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#8a2be2",
          type: "underground",
          phase: "B",
          temperature: 35,
          vibration: 0.12,
          strain: 0.09
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4205, 37.7605],
            [-122.4105, 37.7555],
            [-122.4005, 37.7505]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-mission-1c",
          name: "Mission District Feed - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#20b2aa",
          type: "underground",
          phase: "C",
          temperature: 41,
          vibration: 0.26,
          strain: 0.17
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4210, 37.7610],
            [-122.4110, 37.7560],
            [-122.4010, 37.7510]
          ]
        }
      },
      // Castro District SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-castro-1a",
          name: "Castro District Line - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "250MW",
          color: "#dc143c",
          type: "overhead",
          phase: "A",
          temperature: 39,
          vibration: 0.20,
          strain: 0.14
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4350, 37.7600],
            [-122.4250, 37.7550],
            [-122.4150, 37.7500]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-castro-1b",
          name: "Castro District Line - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "250MW",
          color: "#4169e1",
          type: "overhead",
          phase: "B",
          temperature: 43,
          vibration: 0.29,
          strain: 0.20
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4355, 37.7605],
            [-122.4255, 37.7555],
            [-122.4155, 37.7505]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-castro-1c",
          name: "Castro District Line - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "250MW",
          color: "#228b22",
          type: "overhead",
          phase: "C",
          temperature: 37,
          vibration: 0.16,
          strain: 0.12
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4360, 37.7610],
            [-122.4260, 37.7560],
            [-122.4160, 37.7510]
          ]
        }
      },
      // SOMA District SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-soma-1a",
          name: "SOMA District Feed - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ff69b4",
          type: "underground",
          phase: "A",
          temperature: 48,
          vibration: 0.35,
          strain: 0.25
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4000, 37.7700],
            [-122.3900, 37.7650],
            [-122.3800, 37.7600]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-soma-1b",
          name: "SOMA District Feed - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#00fa9a",
          type: "underground",
          phase: "B",
          temperature: 36,
          vibration: 0.14,
          strain: 0.10
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4005, 37.7705],
            [-122.3905, 37.7655],
            [-122.3805, 37.7605]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-soma-1c",
          name: "SOMA District Feed - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ffa500",
          type: "underground",
          phase: "C",
          temperature: 42,
          vibration: 0.27,
          strain: 0.19
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4010, 37.7710],
            [-122.3910, 37.7660],
            [-122.3810, 37.7610]
          ]
        }
      },
      // Marina District SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-marina-1a",
          name: "Marina District Line - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "200MW",
          color: "#da70d6",
          type: "overhead",
          phase: "A",
          temperature: 40,
          vibration: 0.23,
          strain: 0.16
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4400, 37.8000],
            [-122.4300, 37.7950],
            [-122.4200, 37.7900]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-marina-1b",
          name: "Marina District Line - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "200MW",
          color: "#7fffd4",
          type: "overhead",
          phase: "B",
          temperature: 38,
          vibration: 0.17,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4405, 37.8005],
            [-122.4305, 37.7955],
            [-122.4205, 37.7905]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-marina-1c",
          name: "Marina District Line - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "200MW",
          color: "#f0e68c",
          type: "overhead",
          phase: "C",
          temperature: 45,
          vibration: 0.30,
          strain: 0.22
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4410, 37.8010],
            [-122.4310, 37.7960],
            [-122.4210, 37.7910]
          ]
        }
      },
      // Presidio SF Cables
      {
        type: "Feature",
        properties: {
          id: "cable-sf-presidio-1a",
          name: "Presidio Feed - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "150MW",
          color: "#cd5c5c",
          type: "underground",
          phase: "A",
          temperature: 34,
          vibration: 0.11,
          strain: 0.08
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4600, 37.8000],
            [-122.4500, 37.7950],
            [-122.4400, 37.7900]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-presidio-1b",
          name: "Presidio Feed - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "150MW",
          color: "#87ceeb",
          type: "underground",
          phase: "B",
          temperature: 47,
          vibration: 0.32,
          strain: 0.24
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4605, 37.8005],
            [-122.4505, 37.7955],
            [-122.4405, 37.7905]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-sf-presidio-1c",
          name: "Presidio Feed - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "150MW",
          color: "#98fb98",
          type: "underground",
          phase: "C",
          temperature: 41,
          vibration: 0.25,
          strain: 0.18
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-122.4610, 37.8010],
            [-122.4510, 37.7960],
            [-122.4410, 37.7910]
          ]
        }
      },
      // SF Cable Monitoring Sensors
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-financial",
          name: "Financial District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.3950, 37.7875]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-market",
          name: "Market Street Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.4000, 37.7825]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-embarcadero",
          name: "Embarcadero Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.3975, 37.7855]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-mission",
          name: "Mission District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.4150, 37.7550]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-castro",
          name: "Castro District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.4300, 37.7575]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-soma",
          name: "SOMA District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.3950, 37.7650]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-marina",
          name: "Marina District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.4350, 37.7975]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-sf-presidio",
          name: "Presidio Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-122.4500, 37.7975]
        }
      },
      // Paradise City Cable Network Data - Multiple cables per route
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-downtown-1a",
          name: "Paradise Downtown Main - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "700MW",
          color: "#ff4444",
          type: "overhead",
          phase: "A",
          temperature: 39,
          vibration: 0.16,
          strain: 0.11
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3000, 33.8000],
            [-118.2900, 33.7950],
            [-118.2800, 33.7900]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-downtown-1b",
          name: "Paradise Downtown Main - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "700MW",
          color: "#00d4ff",
          type: "overhead",
          phase: "B",
          temperature: 37,
          vibration: 0.18,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3005, 33.8005],
            [-118.2905, 33.7955],
            [-118.2805, 33.7905]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-downtown-1c",
          name: "Paradise Downtown Main - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "700MW",
          color: "#00ff88",
          type: "overhead",
          phase: "C",
          temperature: 41,
          vibration: 0.22,
          strain: 0.15
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3010, 33.8010],
            [-118.2910, 33.7960],
            [-118.2810, 33.7910]
          ]
        }
      },
      // Paradise City Beach District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-beach-1a",
          name: "Beach District Feed - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#ff6b35",
          type: "overhead",
          phase: "A",
          temperature: 43,
          vibration: 0.25,
          strain: 0.17
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3200, 33.7800],
            [-118.3100, 33.7750],
            [-118.3000, 33.7700]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-beach-1b",
          name: "Beach District Feed - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#9370db",
          type: "overhead",
          phase: "B",
          temperature: 35,
          vibration: 0.14,
          strain: 0.10
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3205, 33.7805],
            [-118.3105, 33.7755],
            [-118.3005, 33.7705]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-beach-1c",
          name: "Beach District Feed - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#ffd700",
          type: "overhead",
          phase: "C",
          temperature: 38,
          vibration: 0.19,
          strain: 0.14
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3210, 33.7810],
            [-118.3110, 33.7760],
            [-118.3010, 33.7710]
          ]
        }
      },
      // Paradise City Hills District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-hills-1a",
          name: "Hills District Line - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#ff1493",
          type: "overhead",
          phase: "A",
          temperature: 36,
          vibration: 0.17,
          strain: 0.12
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2800, 33.8200],
            [-118.2700, 33.8150],
            [-118.2600, 33.8100]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-hills-1b",
          name: "Hills District Line - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#32cd32",
          type: "overhead",
          phase: "B",
          temperature: 40,
          vibration: 0.23,
          strain: 0.16
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2805, 33.8205],
            [-118.2705, 33.8155],
            [-118.2605, 33.8105]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-hills-1c",
          name: "Hills District Line - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#00ced1",
          type: "overhead",
          phase: "C",
          temperature: 44,
          vibration: 0.28,
          strain: 0.19
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2810, 33.8210],
            [-118.2710, 33.8160],
            [-118.2610, 33.8110]
          ]
        }
      },
      // Paradise City Valley District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-valley-1a",
          name: "Valley District Feed - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "350MW",
          color: "#ff8c00",
          type: "underground",
          phase: "A",
          temperature: 45,
          vibration: 0.30,
          strain: 0.21
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3400, 33.7600],
            [-118.3300, 33.7550],
            [-118.3200, 33.7500]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-valley-1b",
          name: "Valley District Feed - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "350MW",
          color: "#8a2be2",
          type: "underground",
          phase: "B",
          temperature: 33,
          vibration: 0.11,
          strain: 0.08
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3405, 33.7605],
            [-118.3305, 33.7555],
            [-118.3205, 33.7505]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-valley-1c",
          name: "Valley District Feed - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "350MW",
          color: "#20b2aa",
          type: "underground",
          phase: "C",
          temperature: 39,
          vibration: 0.24,
          strain: 0.17
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3410, 33.7610],
            [-118.3310, 33.7560],
            [-118.3210, 33.7510]
          ]
        }
      },
      // Paradise City Harbor District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-harbor-1a",
          name: "Harbor District Line - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#dc143c",
          type: "overhead",
          phase: "A",
          temperature: 37,
          vibration: 0.19,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3500, 33.7400],
            [-118.3400, 33.7350],
            [-118.3300, 33.7300]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-harbor-1b",
          name: "Harbor District Line - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#4169e1",
          type: "overhead",
          phase: "B",
          temperature: 41,
          vibration: 0.26,
          strain: 0.18
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3505, 33.7405],
            [-118.3405, 33.7355],
            [-118.3305, 33.7305]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-harbor-1c",
          name: "Harbor District Line - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#228b22",
          type: "overhead",
          phase: "C",
          temperature: 35,
          vibration: 0.15,
          strain: 0.11
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.3510, 33.7410],
            [-118.3410, 33.7360],
            [-118.3310, 33.7310]
          ]
        }
      },
      // Paradise City Resort District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-resort-1a",
          name: "Resort District Feed - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ff69b4",
          type: "underground",
          phase: "A",
          temperature: 47,
          vibration: 0.32,
          strain: 0.23
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2600, 33.7800],
            [-118.2500, 33.7750],
            [-118.2400, 33.7700]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-resort-1b",
          name: "Resort District Feed - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#00fa9a",
          type: "underground",
          phase: "B",
          temperature: 34,
          vibration: 0.13,
          strain: 0.09
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2605, 33.7805],
            [-118.2505, 33.7755],
            [-118.2405, 33.7705]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-paradise-resort-1c",
          name: "Resort District Feed - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "400MW",
          color: "#ffa500",
          type: "underground",
          phase: "C",
          temperature: 40,
          vibration: 0.25,
          strain: 0.18
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-118.2610, 33.7810],
            [-118.2510, 33.7760],
            [-118.2410, 33.7710]
          ]
        }
      },
      // Paradise City Cable Monitoring Sensors
      {
        type: "Feature",
        properties: {
          id: "sensor-paradise-downtown",
          name: "Paradise Downtown Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.2950, 33.7975]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-paradise-beach",
          name: "Paradise Beach Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.3100, 33.7775]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-paradise-hills",
          name: "Paradise Hills Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.2700, 33.8175]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-paradise-valley",
          name: "Paradise Valley Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.3300, 33.7575]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-paradise-harbor",
          name: "Paradise Harbor Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.3400, 33.7375]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-paradise-resort",
          name: "Paradise Resort Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-118.2500, 33.7775]
        }
      },
      // New York City Cable Network Data - Multiple cables per route
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-manhattan-1a",
          name: "Manhattan Financial District - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "800MW",
          color: "#ff4444",
          type: "overhead",
          phase: "A",
          temperature: 42,
          vibration: 0.20,
          strain: 0.14
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-74.0100, 40.7100],
            [-74.0000, 40.7050],
            [-73.9900, 40.7000]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-manhattan-1b",
          name: "Manhattan Financial District - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "800MW",
          color: "#00d4ff",
          type: "overhead",
          phase: "B",
          temperature: 38,
          vibration: 0.22,
          strain: 0.16
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-74.0105, 40.7105],
            [-74.0005, 40.7055],
            [-73.9905, 40.7005]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-manhattan-1c",
          name: "Manhattan Financial District - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "800MW",
          color: "#00ff88",
          type: "overhead",
          phase: "C",
          temperature: 44,
          vibration: 0.26,
          strain: 0.18
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-74.0110, 40.7110],
            [-74.0010, 40.7060],
            [-73.9910, 40.7010]
          ]
        }
      },
      // NYC Brooklyn District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-brooklyn-1a",
          name: "Brooklyn Bridge District - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "700MW",
          color: "#ff6b35",
          type: "overhead",
          phase: "A",
          temperature: 46,
          vibration: 0.28,
          strain: 0.20
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9900, 40.6900],
            [-73.9800, 40.6850],
            [-73.9700, 40.6800]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-brooklyn-1b",
          name: "Brooklyn Bridge District - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "700MW",
          color: "#9370db",
          type: "overhead",
          phase: "B",
          temperature: 36,
          vibration: 0.16,
          strain: 0.12
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9905, 40.6905],
            [-73.9805, 40.6855],
            [-73.9705, 40.6805]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-brooklyn-1c",
          name: "Brooklyn Bridge District - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "700MW",
          color: "#ffd700",
          type: "overhead",
          phase: "C",
          temperature: 40,
          vibration: 0.24,
          strain: 0.17
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9910, 40.6910],
            [-73.9810, 40.6860],
            [-73.9710, 40.6810]
          ]
        }
      },
      // NYC Queens District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-queens-1a",
          name: "Queens District Line - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#ff1493",
          type: "overhead",
          phase: "A",
          temperature: 37,
          vibration: 0.19,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9500, 40.7500],
            [-73.9400, 40.7450],
            [-73.9300, 40.7400]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-queens-1b",
          name: "Queens District Line - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#32cd32",
          type: "overhead",
          phase: "B",
          temperature: 41,
          vibration: 0.25,
          strain: 0.18
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9505, 40.7505],
            [-73.9405, 40.7455],
            [-73.9305, 40.7405]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-queens-1c",
          name: "Queens District Line - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "600MW",
          color: "#00ced1",
          type: "overhead",
          phase: "C",
          temperature: 45,
          vibration: 0.30,
          strain: 0.21
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9510, 40.7510],
            [-73.9410, 40.7460],
            [-73.9310, 40.7410]
          ]
        }
      },
      // NYC Bronx District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-bronx-1a",
          name: "Bronx District Feed - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "400MW",
          color: "#ff8c00",
          type: "underground",
          phase: "A",
          temperature: 48,
          vibration: 0.33,
          strain: 0.24
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9200, 40.8500],
            [-73.9100, 40.8450],
            [-73.9000, 40.8400]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-bronx-1b",
          name: "Bronx District Feed - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "400MW",
          color: "#8a2be2",
          type: "underground",
          phase: "B",
          temperature: 34,
          vibration: 0.12,
          strain: 0.09
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9205, 40.8505],
            [-73.9105, 40.8455],
            [-73.9005, 40.8405]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-bronx-1c",
          name: "Bronx District Feed - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "400MW",
          color: "#20b2aa",
          type: "underground",
          phase: "C",
          temperature: 42,
          vibration: 0.27,
          strain: 0.19
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9210, 40.8510],
            [-73.9110, 40.8460],
            [-73.9010, 40.8410]
          ]
        }
      },
      // NYC Staten Island District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-staten-1a",
          name: "Staten Island Line - Phase A",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#dc143c",
          type: "overhead",
          phase: "A",
          temperature: 39,
          vibration: 0.21,
          strain: 0.15
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-74.1500, 40.5800],
            [-74.1400, 40.5750],
            [-74.1300, 40.5700]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-staten-1b",
          name: "Staten Island Line - Phase B",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#4169e1",
          type: "overhead",
          phase: "B",
          temperature: 43,
          vibration: 0.29,
          strain: 0.20
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-74.1505, 40.5805],
            [-74.1405, 40.5755],
            [-74.1305, 40.5705]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-staten-1c",
          name: "Staten Island Line - Phase C",
          voltage: "69kV",
          status: "operational",
          capacity: "300MW",
          color: "#228b22",
          type: "overhead",
          phase: "C",
          temperature: 37,
          vibration: 0.17,
          strain: 0.13
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-74.1510, 40.5810],
            [-74.1410, 40.5760],
            [-74.1310, 40.5710]
          ]
        }
      },
      // NYC Central Park District Cables
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-centralpark-1a",
          name: "Central Park District Feed - Phase A",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#ff69b4",
          type: "underground",
          phase: "A",
          temperature: 49,
          vibration: 0.34,
          strain: 0.25
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9700, 40.7800],
            [-73.9600, 40.7750],
            [-73.9500, 40.7700]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-centralpark-1b",
          name: "Central Park District Feed - Phase B",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#00fa9a",
          type: "underground",
          phase: "B",
          temperature: 35,
          vibration: 0.15,
          strain: 0.11
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9705, 40.7805],
            [-73.9605, 40.7755],
            [-73.9505, 40.7705]
          ]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "cable-nyc-centralpark-1c",
          name: "Central Park District Feed - Phase C",
          voltage: "138kV",
          status: "operational",
          capacity: "500MW",
          color: "#ffa500",
          type: "underground",
          phase: "C",
          temperature: 41,
          vibration: 0.26,
          strain: 0.19
        },
        geometry: {
          type: "LineString",
          coordinates: [
            [-73.9710, 40.7810],
            [-73.9610, 40.7760],
            [-73.9510, 40.7710]
          ]
        }
      },
      // NYC Cable Monitoring Sensors
      {
        type: "Feature",
        properties: {
          id: "sensor-nyc-manhattan",
          name: "Manhattan Financial Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-74.0050, 40.7075]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-nyc-brooklyn",
          name: "Brooklyn Bridge Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-73.9850, 40.6875]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-nyc-queens",
          name: "Queens District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-73.9450, 40.7475]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-nyc-bronx",
          name: "Bronx District Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-73.9150, 40.8475]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-nyc-staten",
          name: "Staten Island Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-74.1450, 40.5775]
        }
      },
      {
        type: "Feature",
        properties: {
          id: "sensor-nyc-centralpark",
          name: "Central Park Monitor",
          type: "sensor",
          status: "operational",
          color: "#00ff88"
        },
        geometry: {
          type: "Point",
          coordinates: [-73.9650, 40.7775]
        }
      }
    ]
  };

  useEffect(() => {
    if (map.current) return; // Initialize map only once

    try {
        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: 'mapbox://styles/mapbox/dark-v11', // Dark modern style
          center: [-118.2437, 34.0522], // Downtown Los Angeles center
          zoom: 16, // Much closer zoom to see buildings in detail
          pitch: 60, // 3D perspective
          bearing: 0,
          antialias: true,
          accessToken: process.env.REACT_APP_MAPBOX_TOKEN
        });

      map.current.on('load', () => {
        console.log('Map loaded successfully!');
        setMapLoaded(true);
        
        // Start cable animations
        setTimeout(() => {
          setCableAnimations({
            bundles: true,
            cables: true,
            sensors: true
          });
          setCityMovement(true);
        }, 1000);
        
        // Add cable network data source
        map.current.addSource('cable-network', {
          type: 'geojson',
          data: cableNetworkData
        });

        // Add cable bundle background (thick line representing the bundle)
        map.current.addLayer({
          id: 'cable-bundles',
          type: 'line',
          source: 'cable-network',
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': '#333333',
            'line-width': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 8,
              15, 16,
              20, 32
            ],
            'line-opacity': 0.6
          }
        });

        // Add individual underground cables (dashed style)
        map.current.addLayer({
          id: 'underground-cables',
          type: 'line',
          source: 'cable-network',
          filter: ['==', ['get', 'type'], 'underground'],
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
              10, 3,
              15, 6,
              20, 12
            ],
            'line-opacity': 0.9,
            'line-dasharray': [2, 2]
          }
        });

        // Add click handler for underground cables
        map.current.on('click', 'underground-cables', (e) => {
          console.log('Underground cable clicked!', e);
          const features = map.current.queryRenderedFeatures(e.point, {
            layers: ['underground-cables']
          });
          console.log('Features found:', features);
          if (features.length > 0) {
            const cableData = features[0].properties;
            console.log('Cable data:', cableData);
            setSelectedCable(cableData);
            assessCableRisk(cableData);
          }
        });

        // Change cursor on hover and add visual feedback
        map.current.on('mouseenter', 'underground-cables', () => {
          map.current.getCanvas().style.cursor = 'pointer';
          map.current.setPaintProperty('underground-cables', 'line-width', [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 5,
            15, 10,
            20, 20
          ]);
          map.current.setPaintProperty('underground-cables', 'line-opacity', 1);
        });

        map.current.on('mouseleave', 'underground-cables', () => {
          map.current.getCanvas().style.cursor = '';
          map.current.setPaintProperty('underground-cables', 'line-width', [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 3,
            15, 6,
            20, 12
          ]);
          map.current.setPaintProperty('underground-cables', 'line-opacity', 0.9);
        });

        // Add individual overhead cables (solid style)
        map.current.addLayer({
          id: 'overhead-cables',
          type: 'line',
          source: 'cable-network',
          filter: ['==', ['get', 'type'], 'overhead'],
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
              10, 4,
              15, 8,
              20, 16
            ],
            'line-opacity': 0.9
          }
        });

        // Add click handler for overhead cables
        map.current.on('click', 'overhead-cables', (e) => {
          console.log('Overhead cable clicked!', e);
          const features = map.current.queryRenderedFeatures(e.point, {
            layers: ['overhead-cables']
          });
          console.log('Features found:', features);
          if (features.length > 0) {
            const cableData = features[0].properties;
            console.log('Cable data:', cableData);
            setSelectedCable(cableData);
            assessCableRisk(cableData);
          }
        });

        // Change cursor on hover for overhead cables and add visual feedback
        map.current.on('mouseenter', 'overhead-cables', () => {
          map.current.getCanvas().style.cursor = 'pointer';
          map.current.setPaintProperty('overhead-cables', 'line-width', [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 6,
            15, 12,
            20, 24
          ]);
          map.current.setPaintProperty('overhead-cables', 'line-opacity', 1);
        });

        map.current.on('mouseleave', 'overhead-cables', () => {
          map.current.getCanvas().style.cursor = '';
          map.current.setPaintProperty('overhead-cables', 'line-width', [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 4,
            15, 8,
            20, 16
          ]);
          map.current.setPaintProperty('overhead-cables', 'line-opacity', 0.9);
        });
        
        // Add subtle cable glow effect for realism
        map.current.addLayer({
          id: 'cable-glow',
          type: 'line',
          source: 'cable-network',
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
              10, 4,
              15, 8,
              20, 16
            ],
            'line-opacity': 0.2,
            'line-blur': 2
          }
        });

        // Add subtle roads for context
        map.current.addLayer({
          id: 'roads-major',
          type: 'line',
          source: 'composite',
          'source-layer': 'road',
          filter: ['in', 'class', 'primary', 'secondary'],
          paint: {
            'line-color': '#666666',
            'line-width': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 1,
              15, 2,
              20, 4
            ],
            'line-opacity': 0.4
          }
        });

        // Add subtle street labels for major roads only
        map.current.addLayer({
          id: 'street-labels',
          type: 'symbol',
          source: 'composite',
          'source-layer': 'road',
          filter: ['in', 'class', 'primary'],
          layout: {
            'text-field': ['get', 'name'],
            'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular'],
            'text-size': 10,
            'text-transform': 'uppercase',
            'text-letter-spacing': 0.05
          },
          paint: {
            'text-color': '#888888',
            'text-halo-color': '#000000',
            'text-halo-width': 1,
            'text-opacity': 0.6
          }
        });

        // Add cable monitoring sensors
        map.current.addLayer({
          id: 'cable-monitors',
          type: 'circle',
          source: 'cable-network',
          filter: ['==', ['get', 'type'], 'sensor'],
          paint: {
            'circle-color': '#00ff88',
            'circle-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 4,
              15, 8,
              20, 16
            ],
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 2,
            'circle-opacity': 0.9
          }
        });

        // Add sensor glow effect
        map.current.addLayer({
          id: 'cable-monitors-glow',
          type: 'circle',
          source: 'cable-network',
          filter: ['==', ['get', 'type'], 'sensor'],
          paint: {
            'circle-color': '#00ff88',
            'circle-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 8,
              15, 16,
              20, 32
            ],
            'circle-opacity': 0.3,
            'circle-blur': 2
          }
        });

        // Add cable substations
        map.current.addLayer({
          id: 'cable-substations',
          type: 'circle',
          source: 'cable-network',
          filter: ['==', ['get', 'type'], 'substation'],
          paint: {
            'circle-color': '#ff6b35',
            'circle-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              10, 4,
              15, 8,
              20, 16
            ],
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 2,
            'circle-opacity': 0.9
          }
        });

        // Add 3D buildings layer
        if (map.current.getSource('composite')) {
          map.current.addLayer({
            'id': '3d-buildings',
            'source': 'composite',
            'source-layer': 'building',
            'filter': ['==', 'extrude', 'true'],
            'type': 'fill-extrusion',
            'minzoom': 15,
            'paint': {
              'fill-extrusion-color': '#1a1a1a',
              'fill-extrusion-height': [
                'interpolate',
                ['linear'],
                ['zoom'],
                15,
                0,
                15.05,
                ['get', 'height']
              ],
              'fill-extrusion-base': [
                'interpolate',
                ['linear'],
                ['zoom'],
                15,
                0,
                15.05,
                ['get', 'min_height']
              ],
              'fill-extrusion-opacity': 0.8
            }
          });
        }

        // Add general map click handler as fallback
        map.current.on('click', (e) => {
          console.log('Map clicked at:', e.lngLat);
          
          // Check for cable features with a larger radius to make clicking easier
          const undergroundFeatures = map.current.queryRenderedFeatures([
            [e.point.x - 10, e.point.y - 10],
            [e.point.x + 10, e.point.y + 10]
          ], {
            layers: ['underground-cables']
          });
          
          const overheadFeatures = map.current.queryRenderedFeatures([
            [e.point.x - 10, e.point.y - 10],
            [e.point.x + 10, e.point.y + 10]
          ], {
            layers: ['overhead-cables']
          });
          
          const allFeatures = [...undergroundFeatures, ...overheadFeatures];
          console.log('All cable features at click point:', allFeatures);
          
          if (allFeatures.length > 0) {
            const cableData = allFeatures[0].properties;
            console.log('Selected cable data:', cableData);
            setSelectedCable(cableData);
            assessCableRisk(cableData);
          } else {
            console.log('No cable features found at click point');
          }
        });
      });

      map.current.on('error', (e) => {
        console.error('Map error:', e);
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
