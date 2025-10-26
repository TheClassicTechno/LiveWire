import React from 'react';
import { motion } from 'framer-motion';
import LosAngelesMap from './LosAngelesMap';
import './HealthVisualization.css';

const HealthVisualization = () => {
  return (
    <div className="health-visualization">
      <div className="map-container card-electric">
        <LosAngelesMap />
      </div>

      {/* System Performance Graph */}
      <motion.div 
        className="system-performance"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
      >
        <h3 className="performance-title">System Performance Overview</h3>
        <div className="performance-graphs">
          {/* Temperature Trend */}
          <motion.div 
            className="graph-container"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <div className="graph-header">
              <h4>Temperature Trend</h4>
              <div className="time-controls">
                <button className="time-btn active">24h</button>
                <button className="time-btn">7d</button>
              </div>
            </div>
            <div className="graph-visual">
              <svg viewBox="0 0 400 150" className="temperature-chart">
                {/* Grid lines */}
                <defs>
                  <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
                
                {/* Temperature line */}
                <motion.path
                  d="M20,120 Q60,100 100,110 T180,80 T260,70 T340,75"
                  stroke="#ff6b35"
                  strokeWidth="3"
                  fill="none"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 3, delay: 0.8 }}
                />
                
                {/* Data points */}
                {[
                  {x: 20, y: 120, temp: 28},
                  {x: 60, y: 100, temp: 22},
                  {x: 100, y: 110, temp: 24},
                  {x: 140, y: 90, temp: 18},
                  {x: 180, y: 80, temp: 16},
                  {x: 220, y: 70, temp: 14},
                  {x: 260, y: 70, temp: 14},
                  {x: 300, y: 60, temp: 12},
                  {x: 340, y: 75, temp: 15},
                  {x: 380, y: 85, temp: 18}
                ].map((point, i) => (
                  <motion.circle
                    key={i}
                    cx={point.x} cy={point.y} r="4"
                    fill="#ff6b35"
                    stroke="#fff"
                    strokeWidth="2"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.3, delay: 0.8 + i * 0.2 }}
                  />
                ))}
                
                {/* Y-axis labels */}
                <text x="10" y="25" fill="rgba(255,255,255,0.7)" fontSize="12" textAnchor="middle">40</text>
                <text x="10" y="50" fill="rgba(255,255,255,0.7)" fontSize="12" textAnchor="middle">30</text>
                <text x="10" y="75" fill="rgba(255,255,255,0.7)" fontSize="12" textAnchor="middle">20</text>
                <text x="10" y="100" fill="rgba(255,255,255,0.7)" fontSize="12" textAnchor="middle">10</text>
                <text x="10" y="125" fill="rgba(255,255,255,0.7)" fontSize="12" textAnchor="middle">0</text>
                
                {/* X-axis labels */}
                <text x="20" y="145" fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">6PM</text>
                <text x="100" y="145" fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">10PM</text>
                <text x="180" y="145" fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">2AM</text>
                <text x="260" y="145" fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">6AM</text>
                <text x="340" y="145" fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">10AM</text>
                <text x="380" y="145" fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">2PM</text>
              </svg>
            </div>
          </motion.div>

          {/* Vibration Analysis */}
          <motion.div 
            className="graph-container"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <div className="graph-header">
              <h4>Vibration Analysis</h4>
              <div className="current-value">1.8 m/s²</div>
            </div>
            <div className="graph-visual">
              <div className="bar-chart">
                {[1.2, 2.1, 1.8, 2.5, 1.6, 2.0, 1.9, 2.3, 1.7, 2.2].map((value, i) => (
                  <motion.div
                    key={i}
                    className="bar"
                    style={{ height: `${(value / 3) * 100}%` }}
                    initial={{ height: 0 }}
                    animate={{ height: `${(value / 3) * 100}%` }}
                    transition={{ duration: 0.5, delay: 1 + i * 0.1 }}
                  />
                ))}
              </div>
            </div>
          </motion.div>

          {/* Strain Monitoring */}
          <motion.div 
            className="graph-container"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 1.0 }}
          >
            <div className="graph-header">
              <h4>Strain Monitoring</h4>
              <div className="current-value">0.65 mm/m</div>
            </div>
            <div className="graph-visual">
              <div className="gauge-container">
                <svg viewBox="0 0 200 100" className="gauge">
                  <motion.path
                    d="M20,80 A60,60 0 0,1 180,80"
                    stroke="#333"
                    strokeWidth="8"
                    fill="none"
                  />
                  <motion.path
                    d="M20,80 A60,60 0 0,1 180,80"
                    stroke="#00ff88"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray="188.5"
                    strokeDashoffset="94.25"
                    initial={{ strokeDashoffset: 188.5 }}
                    animate={{ strokeDashoffset: 94.25 }}
                    transition={{ duration: 2, delay: 1.2 }}
                  />
                  <motion.text
                    x="100" y="70"
                    textAnchor="middle"
                    fill="#00ff88"
                    fontSize="16"
                    fontWeight="bold"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 3.2 }}
                  >
                    65%
                  </motion.text>
                </svg>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default HealthVisualization;
