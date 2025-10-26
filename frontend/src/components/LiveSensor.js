import React, { useState, useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "./LiveSensor.css";

const SENSOR_LOCATION = {
  lat: 37.7749, // San Francisco center
  lon: -122.4194,
};

export const addLiveSensorToMap = (map) => {
  if (!map.current) return;

  // Add sensor source if it doesn't exist
  if (!map.current.getSource("live-sensor")) {
    map.current.addSource("live-sensor", {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [SENSOR_LOCATION.lon, SENSOR_LOCATION.lat],
        },
        properties: {
          id: "sf-sensor-1",
          type: "sensor",
          name: "SF Transmission Monitor 1",
          status: "active",
        },
      },
    });
  }

  // Add sensor marker layer
  if (!map.current.getLayer("live-sensor-marker")) {
    map.current.addLayer({
      id: "live-sensor-marker",
      type: "circle",
      source: "live-sensor",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          10,
          6,
          15,
          12,
          20,
          20,
        ],
        "circle-color": "#00ff88",
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 2,
        "circle-opacity": 0.9,
      },
    });

    // Add glow effect layer
    map.current.addLayer({
      id: "live-sensor-glow",
      type: "circle",
      source: "live-sensor",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          10,
          15,
          15,
          25,
          20,
          40,
        ],
        "circle-color": "#00ff88",
        "circle-opacity": 0.2,
        "circle-blur": 1,
      },
    });
  }

  // Add click handler for sensor
  map.current.on("click", "live-sensor-marker", (e) => {
    if (!e.features.length) return;

    const coordinates = e.features[0].geometry.coordinates.slice();
    const { name } = e.features[0].properties;

    // Create popup content
    const popupContent = document.createElement("div");
    popupContent.className = "sensor-popup";
    popupContent.innerHTML = `
      <h3>${name}</h3>
      <div class="sensor-stats">
        <div class="stat">
          <label>Temperature</label>
          <span id="sensor-temp">Loading...</span>
        </div>
        <div class="stat">
          <label>Strain</label>
          <span id="sensor-strain">Loading...</span>
        </div>
        <div class="stat">
          <label>Vibration</label>
          <span id="sensor-vibration">Loading...</span>
        </div>
        <div class="stat">
          <label>RUL Prediction</label>
          <span id="sensor-rul">Loading...</span>
        </div>
      </div>
    `;

    // Create and show popup
    new mapboxgl.Popup({
      closeButton: true,
      closeOnClick: false,
      maxWidth: "300px",
    })
      .setLngLat(coordinates)
      .setDOMContent(popupContent)
      .addTo(map.current);

    // Start updating sensor data
    const updateSensorData = async () => {
      try {
        const response = await fetch("/api/sensor-data");
        if (!response.ok) throw new Error("Failed to fetch sensor data");
        const data = await response.json();

        // Update popup content
        document.getElementById(
          "sensor-temp"
        ).textContent = `${data.avgTemp.toFixed(1)}°C`;
        document.getElementById("sensor-strain").textContent =
          data.avgStrain.toFixed(2);
        document.getElementById("sensor-vibration").textContent =
          data.avgVibration.toFixed(3);
        document.getElementById("sensor-rul").textContent = `${
          data.rulPrediction || "99.9"
        }%`;
      } catch (error) {
        console.error("Error fetching sensor data:", error);
      }
    };

    // Update immediately and then every 5 seconds
    updateSensorData();
    const interval = setInterval(updateSensorData, 5000);

    // Cleanup interval when popup is closed
    const popup = document.querySelector(".mapboxgl-popup");
    if (popup) {
      popup.addEventListener("remove", () => {
        clearInterval(interval);
      });
    }
  });

  // Add hover effect
  map.current.on("mouseenter", "live-sensor-marker", () => {
    map.current.getCanvas().style.cursor = "pointer";
  });

  map.current.on("mouseleave", "live-sensor-marker", () => {
    map.current.getCanvas().style.cursor = "";
  });
};
