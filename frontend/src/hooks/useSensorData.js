import { useState, useEffect } from "react";

const POLL_INTERVAL = 5000; // Poll every 5 seconds

export const useSensorData = (sensorId) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/sensor-data");
        if (!response.ok) throw new Error("Failed to fetch sensor data");
        const newData = await response.json();

        // Calculate RUL based on latest readings
        const rulCalculation = calculateRUL(newData);

        setData({
          ...newData,
          rulPrediction: rulCalculation.prediction,
          riskLevel: rulCalculation.riskLevel,
        });

        setError(null);
      } catch (err) {
        console.error("Error fetching sensor data:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Set up polling interval
    const interval = setInterval(fetchData, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [sensorId]);

  return { data, loading, error };
};

/**
 * Calculate Remaining Useful Life (RUL) prediction
 * Based on temperature, strain, and vibration thresholds
 */
const calculateRUL = (sensorData) => {
  const {
    avgTemp = 0,
    avgStrain = 0,
    avgVibration = 0,
    maxTemp = 0,
    maxStrain = 0,
  } = sensorData;

  // Define thresholds
  const CRITICAL_TEMP = 80;
  const CRITICAL_STRAIN = 200;
  const CRITICAL_VIBRATION = 1.5;

  // Calculate stress factors (0-1 scale)
  const tempStress = Math.min(maxTemp / CRITICAL_TEMP, 1);
  const strainStress = Math.min(maxStrain / CRITICAL_STRAIN, 1);
  const vibrationStress = Math.min(avgVibration / CRITICAL_VIBRATION, 1);

  // Weighted average of stress factors
  const totalStress =
    tempStress * 0.4 + strainStress * 0.4 + vibrationStress * 0.2;

  // Convert to RUL percentage (100% = full life, 0% = end of life)
  const rulPercentage = Math.max(0, Math.min(100, (1 - totalStress) * 100));

  // Determine risk level
  let riskLevel = "low";
  if (rulPercentage < 30) riskLevel = "critical";
  else if (rulPercentage < 60) riskLevel = "elevated";
  else if (rulPercentage < 80) riskLevel = "moderate";

  return {
    prediction: rulPercentage.toFixed(1),
    riskLevel,
  };
};
