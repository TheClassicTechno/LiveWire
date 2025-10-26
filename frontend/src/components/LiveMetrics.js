import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Thermometer,
  Zap,
  BarChart3,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import ElasticService from '../services/ElasticService';
import './LiveMetrics.css';

const LiveMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [readings, setReadings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Start real-time updates
    const cleanup = ElasticService.startRealTimeUpdates(
      ({ stats, readings }) => {
        setMetrics(stats);
        setReadings(readings);
        setLastUpdate(new Date());
        setLoading(false);
      },
      5000 // Update every 5 seconds
    );

    return cleanup; // Cleanup on unmount
  }, []);

  if (loading) {
    return (
      <div className="live-metrics loading">
        <motion.div
          className="loading-spinner"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <Activity size={24} />
        </motion.div>
        <p>Loading live sensor data...</p>
      </div>
    );
  }

  const getRiskIcon = (zone) => {
    switch (zone) {
      case 'red': return <AlertCircle className="risk-red" />;
      case 'yellow': return <AlertTriangle className="risk-yellow" />;
      default: return <CheckCircle className="risk-green" />;
    }
  };

  const getRiskColor = (zone) => {
    switch (zone) {
      case 'red': return '#dc2626';
      case 'yellow': return '#f59e0b';
      default: return '#16a34a';
    }
  };

  const formatValue = (value, decimals = 1) => {
    return typeof value === 'number' ? value.toFixed(decimals) : value;
  };

  return (
    <div className="live-metrics">
      {/* Header */}
      <div className="metrics-header">
        <h2>
          <Activity className="header-icon" />
          Live Infrastructure Metrics
        </h2>
        <div className="last-update">
          <Clock size={16} />
          {lastUpdate && `Updated ${lastUpdate.toLocaleTimeString()}`}
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="metrics-grid">
        {/* Temperature */}
        <motion.div 
          className="metric-card temperature"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="metric-header">
            <Thermometer size={24} />
            <span className="metric-label">Temperature</span>
          </div>
          <div className="metric-value">
            {formatValue(metrics?.temperature)}°C
          </div>
          <div className="metric-trend">
            Median across all sensors
          </div>
        </motion.div>

        {/* Power */}
        <motion.div 
          className="metric-card power"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="metric-header">
            <Zap size={24} />
            <span className="metric-label">Power Load</span>
          </div>
          <div className="metric-value">
            {formatValue(metrics?.power, 0)}W
          </div>
          <div className="metric-trend">
            Median electrical load
          </div>
        </motion.div>

        {/* Vibration */}
        <motion.div 
          className="metric-card vibration"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="metric-header">
            <Activity size={24} />
            <span className="metric-label">Vibration</span>
          </div>
          <div className="metric-value">
            {formatValue(metrics?.vibration, 3)}g
          </div>
          <div className="metric-trend">
            Structural oscillations
          </div>
        </motion.div>

        {/* Strain */}
        <motion.div 
          className="metric-card strain"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="metric-header">
            <BarChart3 size={24} />
            <span className="metric-label">Strain</span>
          </div>
          <div className="metric-value">
            {formatValue(metrics?.strain, 0)}µε
          </div>
          <div className="metric-trend">
            Mechanical stress
          </div>
        </motion.div>

        {/* Confidence */}
        <motion.div 
          className="metric-card confidence"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="metric-header">
            <TrendingUp size={24} />
            <span className="metric-label">AI Confidence</span>
          </div>
          <div className="metric-value">
            {formatValue(metrics?.confidence * 100, 0)}%
          </div>
          <div className="metric-trend">
            Prediction accuracy
          </div>
        </motion.div>
      </div>

      {/* Risk Distribution */}
      <div className="risk-section">
        <h3>Risk Zone Distribution</h3>
        <div className="risk-distribution">
          {Object.entries(metrics?.riskDistribution || {}).map(([zone, count]) => (
            <motion.div 
              key={zone}
              className={`risk-item risk-${zone}`}
              whileHover={{ scale: 1.05 }}
            >
              {getRiskIcon(zone)}
              <span className="risk-label">{zone.toUpperCase()}</span>
              <span className="risk-count">{count}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Readings */}
      <div className="recent-readings">
        <h3>Latest Sensor Readings</h3>
        <div className="readings-list">
          {readings.slice(0, 5).map((reading, index) => (
            <motion.div
              key={index}
              className="reading-item"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="reading-time">
                {new Date(reading.timestamp).toLocaleTimeString()}
              </div>
              <div className="reading-component">
                {reading.componentId}
              </div>
              <div className="reading-values">
                <span>T: {formatValue(reading.sensorData?.temperature)}°C</span>
                <span>P: {formatValue(reading.sensorData?.power, 0)}W</span>
                <span>V: {formatValue(reading.sensorData?.vibration, 3)}g</span>
              </div>
              <div 
                className={`reading-risk risk-${reading.riskZone}`}
                style={{ color: getRiskColor(reading.riskZone) }}
              >
                {getRiskIcon(reading.riskZone)}
                {reading.riskZone?.toUpperCase()}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Connection Status */}
      <div className="connection-status">
        <div className="status-indicator online">
          <div className="pulse"></div>
          Live connection to Elastic Serverless
        </div>
      </div>
    </div>
  );
};

export default LiveMetrics;