import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Zap, Shield, TrendingUp, MapPin, Menu, X, Globe } from "lucide-react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import "./LandingPage.css";

// Set Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const LandingPage = () => {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const handleGetStarted = () => {
    navigate("/dashboard");
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  // Initialize rotating world map
  useEffect(() => {
    if (map.current) return;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: [0, 0],
        zoom: 1.2,
        pitch: 0,
        bearing: 0,
        interactive: true,
        attributionControl: false,
        dragPan: true,
        dragRotate: true,
        scrollZoom: true,
        boxZoom: true,
        doubleClickZoom: true,
        keyboard: true,
        touchZoomRotate: true,
        accessToken: process.env.REACT_APP_MAPBOX_TOKEN,
      });

      map.current.on("load", () => {
        setMapLoaded(true);
        console.log(
          "World map loaded and interactive:",
          map.current.isStyleLoaded()
        );

        // Add global electrical cable network connecting all countries
        const globalCableData = {
          type: "FeatureCollection",
          features: [
            // North America to Europe
            {
              type: "Feature",
              properties: {
                name: "Trans-Atlantic Cable",
                voltage: "500kV",
                capacity: "2GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [-74.0, 40.7], // New York
                  [-25.0, 40.0], // Portugal
                  [-9.0, 38.7], // Lisbon
                ],
              },
            },
            // North America to Asia
            {
              type: "Feature",
              properties: {
                name: "Trans-Pacific Cable",
                voltage: "500kV",
                capacity: "1.8GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [-122.4, 37.8], // San Francisco
                  [139.7, 35.7], // Tokyo
                ],
              },
            },
            // Europe to Africa
            {
              type: "Feature",
              properties: {
                name: "Europe-Africa Cable",
                voltage: "400kV",
                capacity: "1.5GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [2.3, 48.9], // Paris
                  [31.2, 30.0], // Cairo
                  [18.4, -33.9], // Cape Town
                ],
              },
            },
            // Asia to Europe
            {
              type: "Feature",
              properties: {
                name: "Asia-Europe Cable",
                voltage: "500kV",
                capacity: "2.2GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [103.8, 1.3], // Singapore
                  [80.0, 25.0], // India
                  [50.0, 30.0], // Middle East
                  [30.0, 40.0], // Turkey
                  [2.3, 48.9], // Paris
                ],
              },
            },
            // Asia to Australia
            {
              type: "Feature",
              properties: {
                name: "Asia-Australia Cable",
                voltage: "400kV",
                capacity: "1GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [103.8, 1.3], // Singapore
                  [151.2, -33.9], // Sydney
                ],
              },
            },
            // South America Network
            {
              type: "Feature",
              properties: {
                name: "South America Grid",
                voltage: "500kV",
                capacity: "1.2GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [-46.6, -23.5], // São Paulo
                  [-43.2, -22.9], // Rio de Janeiro
                  [-58.4, -34.6], // Buenos Aires
                  [-70.7, -33.4], // Santiago
                ],
              },
            },
            // North America Network
            {
              type: "Feature",
              properties: {
                name: "North America Grid",
                voltage: "765kV",
                capacity: "3GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [-74.0, 40.7], // New York
                  [-87.6, 41.9], // Chicago
                  [-95.4, 29.8], // Houston
                  [-122.4, 37.8], // San Francisco
                ],
              },
            },
            // Europe Network
            {
              type: "Feature",
              properties: {
                name: "European Grid",
                voltage: "400kV",
                capacity: "2.5GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [2.3, 48.9], // Paris
                  [4.9, 52.4], // Amsterdam
                  [13.4, 52.5], // Berlin
                  [12.5, 41.9], // Rome
                  [2.3, 48.9], // Back to Paris
                ],
              },
            },
            // Asia Network
            {
              type: "Feature",
              properties: {
                name: "Asian Grid",
                voltage: "500kV",
                capacity: "3.5GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [139.7, 35.7], // Tokyo
                  [121.5, 31.2], // Shanghai
                  [103.8, 1.3], // Singapore
                  [77.2, 28.6], // Delhi
                  [139.7, 35.7], // Back to Tokyo
                ],
              },
            },
            // Africa Network
            {
              type: "Feature",
              properties: {
                name: "African Grid",
                voltage: "400kV",
                capacity: "1.8GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [31.2, 30.0], // Cairo
                  [18.4, -33.9], // Cape Town
                  [3.4, 6.4], // Lagos
                  [36.8, -1.3], // Nairobi
                  [31.2, 30.0], // Back to Cairo
                ],
              },
            },
            // Additional Intercontinental Connections
            {
              type: "Feature",
              properties: {
                name: "Arctic Cable",
                voltage: "500kV",
                capacity: "800MW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [-74.0, 40.7], // New York
                  [-20.0, 70.0], // Iceland
                  [2.3, 48.9], // Paris
                ],
              },
            },
            {
              type: "Feature",
              properties: {
                name: "Indian Ocean Cable",
                voltage: "400kV",
                capacity: "1.2GW",
                color: "#ffd700",
                status: "operational",
              },
              geometry: {
                type: "LineString",
                coordinates: [
                  [103.8, 1.3], // Singapore
                  [55.2, 25.2], // Dubai
                  [18.4, -33.9], // Cape Town
                ],
              },
            },
          ],
        };

        // Add cable network source
        map.current.addSource("global-cables", {
          type: "geojson",
          data: globalCableData,
        });

        // Add cable lines
        map.current.addLayer({
          id: "global-cable-lines",
          type: "line",
          source: "global-cables",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": ["get", "color"],
            "line-width": 4,
            "line-opacity": 0.8,
          },
        });

        // Add cable glow effect
        map.current.addLayer({
          id: "global-cable-glow",
          type: "line",
          source: "global-cables",
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": ["get", "color"],
            "line-width": 8,
            "line-opacity": 0.3,
            "line-blur": 2,
          },
        });

        // Add cable markers
        map.current.addLayer({
          id: "global-cable-markers",
          type: "circle",
          source: "global-cables",
          paint: {
            "circle-color": ["get", "color"],
            "circle-radius": 6,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
            "circle-opacity": 0.9,
          },
        });

        // Map is now interactive - users can pan, zoom, and rotate manually

        // Start automatic rotation
        const rotateWorld = () => {
          if (map.current) {
            const currentBearing = map.current.getBearing();
            map.current.easeTo({
              bearing: currentBearing + 0.5, // Faster rotation
              duration: 100,
              easing: (t) => t,
            });
            requestAnimationFrame(rotateWorld);
          }
        };

        // Start rotation after a delay
        setTimeout(() => {
          rotateWorld();
        }, 2000);

        // Add click event to test interactivity
        map.current.on("click", (e) => {
          console.log("Map clicked at:", e.lngLat);
        });

        // Add move event to test panning
        map.current.on("move", () => {
          console.log("Map moved to:", map.current.getCenter());
        });
      });
    } catch (error) {
      console.error("Failed to initialize world map:", error);
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  return (
    <div className="landing-page animated-bg">
      {/* Electric particles background */}
      <div className="electric-particles">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="particle"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
            }}
            animate={{
              y: [0, -20, 0],
              opacity: [0.3, 1, 0.3],
            }}
            transition={{
              duration: 2 + Math.random() * 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Main content */}
      <div className="landing-container">
        {/* Header */}
        <motion.header
          className="landing-header"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="nav-container">
            <div className="logo-container">
              <Zap className="logo-icon electric-pulse" />
              <span className="logo-text text-electric">LiveWire</span>
            </div>

            <nav className="main-nav">
              <a href="#developers" className="nav-link">
                About Us
              </a>
              <a href="#contact" className="nav-link">
                Contact
              </a>
            </nav>

            <div className="nav-actions">
              <button className="nav-btn login-btn">Log in</button>
              <button className="nav-btn signup-btn btn-electric">
                Sign up
              </button>
            </div>

            <button className="mobile-menu-toggle" onClick={toggleMobileMenu}>
              {mobileMenuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </motion.header>

        {/* Mobile Menu */}
        <motion.div
          className={`mobile-menu ${mobileMenuOpen ? "open" : ""}`}
          initial={{ opacity: 0, height: 0 }}
          animate={{
            opacity: mobileMenuOpen ? 1 : 0,
            height: mobileMenuOpen ? "auto" : 0,
          }}
          transition={{ duration: 0.3 }}
        >
          <nav className="mobile-nav">
            <a
              href="#products"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Products
            </a>
            <a
              href="#solutions"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Solutions
            </a>
            <a
              href="#developers"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Developers
            </a>
            <a
              href="#company"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Company
            </a>
            <a
              href="#resources"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Resources
            </a>
            <a
              href="#pricing"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Pricing
            </a>
            <a
              href="#contact"
              className="mobile-nav-link"
              onClick={toggleMobileMenu}
            >
              Contact us
            </a>
            <div className="mobile-nav-actions">
              <button
                className="mobile-nav-btn login-btn"
                onClick={toggleMobileMenu}
              >
                Log in
              </button>
              <button
                className="mobile-nav-btn signup-btn btn-electric"
                onClick={toggleMobileMenu}
              >
                Sign up
              </button>
            </div>
          </nav>
        </motion.div>

        {/* Hero section */}
        <motion.main
          className="hero-section"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="hero-content">
            <motion.div
              className="hero-brand"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.3 }}
            >
              <h1 className="brand-name">
                <span className="brand-text text-electric text-glow">
                  LiveWire
                </span>
                <div className="brand-subtitle">
                  Predict failures up to 308 days before they happen
                </div>
              </h1>
            </motion.div>

            <motion.p
              className="hero-subtitle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              Identify electrical cable degradation and failure in smart cities
              using advanced AI monitoring. Reduce fires, failures, accidents,
              costs and energy waste.
            </motion.p>

            <motion.button
              className="btn-electric btn-get-started"
              onClick={handleGetStarted}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.8 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Get Started
              <Zap className="btn-icon" />
            </motion.button>

            <motion.div
              className="hero-features"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1 }}
            >
              <div className="feature-item">
                <Shield className="feature-icon" />
                <span>Real-time Monitoring</span>
              </div>
              <div className="feature-item">
                <TrendingUp className="feature-icon" />
                <span>Predictive Analytics</span>
              </div>
              <div className="feature-item">
                <MapPin className="feature-icon" />
                <span>Smart City Integration</span>
              </div>
            </motion.div>
          </div>

          {/* Rotating World Map */}
          <motion.div
            className="hero-visual"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            <div className="world-map-container">
              <div className="map-header">
                <Globe className="globe-icon" />
              </div>
              <div className="map-wrapper">
                <div ref={mapContainer} className="rotating-world-map" />
                {mapLoaded && (
                  <motion.div
                    className="map-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 1, delay: 0.5 }}
                  >
                    <div className="cable-legend-overlay">
                      <div className="legend-item">
                        <div
                          className="legend-color"
                          style={{ backgroundColor: "#ffd700" }}
                        ></div>
                        <span className="legend-text">
                          Global Cable Network
                        </span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
              <div className="map-stats">
                <div className="stat-item">
                  <span className="stat-number">1M+</span>
                  <span className="stat-label">Cables Monitored</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">24/7</span>
                  <span className="stat-label">Live Coverage</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">300+</span>
                  <span className="stat-label">Days to Prepare</span>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.main>
      </div>
    </div>
  );
};

export default LandingPage;
