import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, Activity, Thermometer, Wind, Zap } from 'lucide-react';
import './ComponentInfoPanel.css';

const ComponentInfoPanel = ({ data, fireDate }) => {
  const getZoneColor = (zone) => {
    const colors = {
      green: '#10b981',
      yellow: '#eab308',
      orange: '#f97316',
      red: '#ef4444'
    };
    return colors[zone] || '#6b7280';
  };

  const getZoneLabel = (zone) => {
    const labels = {
      green: 'Normal Operation',
      yellow: 'Warning',
      orange: 'Degradation',
      red: 'Critical'
    };
    return labels[zone] || zone;
  };

  const getRiskDescription = (zone) => {
    const descriptions = {
      green: 'Component operating within normal parameters. No immediate action required.',
      yellow: 'Increased wear detected. Schedule maintenance inspection.',
      orange: 'Significant degradation. Plan replacement soon.',
      red: 'Critical condition. Immediate maintenance/replacement required.'
    };
    return descriptions[zone] || '';
  };

  const getImpactStatement = (daysUntilFire) => {
    if (daysUntilFire > 308) {
      return {
        text: 'Early detection possible',
        icon: '✓',
        color: '#10b981'
      };
    } else if (daysUntilFire > 0) {
      const daysSinceCritical = 308 - daysUntilFire;
      return {
        text: `${daysSinceCritical} days to prevent disaster`,
        icon: '⏰',
        color: '#ef4444'
      };
    } else {
      return {
        text: 'Disaster occurred',
        icon: '🔥',
        color: '#ef4444'
      };
    }
  };

  const impact = getImpactStatement(data.daysUntilFire);

  return (
    <motion.div
      className="component-info-panel"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="panel-header">
        <div className="header-title">
          <h3>{data.name}</h3>
          <p className="location">{data.location}</p>
        </div>
        <div className="component-age">
          <span className="age-label">Built</span>
          <span className="age-value">{data.built_year}</span>
        </div>
      </div>

      {/* Risk Status Card */}
      <motion.div
        className="risk-status-card"
        style={{
          borderLeft: `4px solid ${getZoneColor(data.zone)}`,
          background: `linear-gradient(135deg, rgba(${data.zone === 'green' ? '16,185,129' : data.zone === 'yellow' ? '234,179,8' : data.zone === 'orange' ? '249,115,22' : '239,68,68'},0.1), transparent)`
        }}
        animate={{
          boxShadow: data.zone !== 'green' ? [
            `0 0 10px rgba(${data.zone === 'yellow' ? '234,179,8' : data.zone === 'orange' ? '249,115,22' : '239,68,68'},0.3)`,
            `0 0 20px rgba(${data.zone === 'yellow' ? '234,179,8' : data.zone === 'orange' ? '249,115,22' : '239,68,68'},0.5)`,
            `0 0 10px rgba(${data.zone === 'yellow' ? '234,179,8' : data.zone === 'orange' ? '249,115,22' : '239,68,68'},0.3)`
          ] : 'none'
        }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        <div className="risk-indicator">
          {data.zone === 'green' ? (
            <CheckCircle size={24} color="#10b981" />
          ) : (
            <AlertCircle size={24} color={getZoneColor(data.zone)} />
          )}
        </div>
        <div className="risk-info">
          <div className="risk-zone" style={{ color: getZoneColor(data.zone) }}>
            {getZoneLabel(data.zone)}
          </div>
          <p className="risk-desc">{getRiskDescription(data.zone)}</p>
        </div>
      </motion.div>

      {/* CCI Score */}
      <div className="metric-card">
        <div className="metric-label">CCI Score (Component Condition Index)</div>
        <motion.div
          className="metric-value"
          initial={{ scale: 0.5 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200 }}
        >
          <span className="score" style={{ color: getZoneColor(data.zone) }}>
            {(data.cci * 100).toFixed(1)}%
          </span>
        </motion.div>
        <div className="progress-bar">
          <motion.div
            className="progress-fill"
            style={{ backgroundColor: getZoneColor(data.zone) }}
            animate={{ width: `${data.cci * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <p className="metric-helper">
          {data.cci < 0.5 ? 'Low degradation' : data.cci < 0.7 ? 'Moderate degradation' : data.cci < 0.9 ? 'Severe degradation' : 'Critical condition'}
        </p>
      </div>

      {/* Sensor Readings */}
      <div className="sensors-grid">
        <div className="sensor-item">
          <div className="sensor-icon">
            <Thermometer size={20} />
          </div>
          <div className="sensor-data">
            <span className="sensor-label">Temperature</span>
            <span className="sensor-value">{data.temperature.toFixed(1)}°C</span>
          </div>
        </div>

        <div className="sensor-item">
          <div className="sensor-icon">
            <Activity size={20} />
          </div>
          <div className="sensor-data">
            <span className="sensor-label">Vibration</span>
            <span className="sensor-value">{data.vibration.toFixed(3)} g</span>
          </div>
        </div>

        <div className="sensor-item">
          <div className="sensor-icon">
            <Zap size={20} />
          </div>
          <div className="sensor-data">
            <span className="sensor-label">Strain</span>
            <span className="sensor-value">{data.strain.toFixed(1)} µε</span>
          </div>
        </div>

        <div className="sensor-item">
          <div className="sensor-icon">
            <Wind size={20} />
          </div>
          <div className="sensor-data">
            <span className="sensor-label">Wind Speed</span>
            <span className="sensor-value">{data.wind_speed.toFixed(1)} m/s</span>
          </div>
        </div>
      </div>

      {/* Impact Statement */}
      <motion.div
        className="impact-statement"
        style={{ borderLeft: `4px solid ${impact.color}` }}
      >
        <div className="impact-icon">{impact.icon}</div>
        <div className="impact-text">
          <p className="impact-title">Time to Prevent Disaster</p>
          <p className="impact-value" style={{ color: impact.color }}>
            {impact.text}
          </p>
        </div>
      </motion.div>

      {/* Key Insights */}
      <div className="insights-section">
        <h4>Key Insights</h4>
        <ul className="insights-list">
          {data.daysUntilFire > 308 ? (
            <>
              <li>✓ Component still operating normally at this time</li>
              <li>✓ No immediate maintenance required yet</li>
              <li>ℹ LiveWire is continuously monitoring for early signs of degradation</li>
            </>
          ) : data.daysUntilFire > 0 ? (
            <>
              <li>⚠️ Model detected critical degradation</li>
              <li>⚠️ This is when maintenance should be scheduled</li>
              <li>ℹ Grid operators have time to plan replacement before failure</li>
              <li style={{ color: '#ef4444', fontWeight: 'bold' }}>
                → {308 - (308 - data.daysUntilFire)} days of advance warning
              </li>
            </>
          ) : (
            <>
              <li>🔥 C-hook fails under wind load</li>
              <li>🔥 Molten metal ignites dry brush below tower</li>
              <li>🔥 Becomes deadliest wildfire in California history</li>
              <li style={{ color: '#ef4444', fontWeight: 'bold' }}>
                → With LiveWire, this disaster would have been prevented
              </li>
            </>
          )}
        </ul>
      </div>

      {/* Call to Action */}
      <motion.div
        className="cta-banner"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <p>
          <strong>LiveWire's Impact:</strong> By predicting infrastructure failures 308 days in advance,
          we give operators the time they need to act. This isn't just about maintenance—it's about saving lives.
        </p>
      </motion.div>
    </motion.div>
  );
};

export default ComponentInfoPanel;
