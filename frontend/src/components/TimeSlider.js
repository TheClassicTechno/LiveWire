import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import './TimeSlider.css';

const TimeSlider = ({ selectedDate, onDateChange, minDate, maxDate }) => {
  const fireDate = new Date(2018, 10, 8); // Nov 8, 2018
  const criticalAlertDate = new Date(fireDate);
  criticalAlertDate.setDate(criticalAlertDate.getDate() - 308); // 308 days before

  const handleSliderChange = (event) => {
    const timestamp = parseInt(event.target.value);
    onDateChange(new Date(timestamp));
  };

  const daysUntilFire = useMemo(() => {
    return Math.floor((fireDate - selectedDate) / (1000 * 60 * 60 * 24));
  }, [selectedDate]);

  const daysSinceCritical = useMemo(() => {
    if (selectedDate < criticalAlertDate) return null;
    return Math.floor((selectedDate - criticalAlertDate) / (1000 * 60 * 60 * 24));
  }, [selectedDate]);

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getDateLabel = () => {
    if (selectedDate < criticalAlertDate) {
      return `${formatDate(selectedDate)} - Normal Operation`;
    } else if (daysSinceCritical <= 308) {
      return `${formatDate(selectedDate)} - Model Alert Active (${308 - daysSinceCritical} days remaining)`;
    } else {
      return formatDate(selectedDate);
    }
  };

  const getPhaseColor = () => {
    if (selectedDate < criticalAlertDate) return '#10b981'; // green
    if (daysSinceCritical <= 100) return '#eab308'; // yellow
    if (daysSinceCritical <= 200) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const sliderProgress = ((selectedDate - minDate) / (maxDate - minDate)) * 100;

  return (
    <motion.div
      className="time-slider-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="slider-header">
        <div className="date-display">
          <h2>{getDateLabel()}</h2>
          <p className="days-until">
            {daysUntilFire > 0 ? (
              <>
                <span className="fire-icon">🔥</span>
                <strong>{daysUntilFire} days</strong> until Camp Fire
              </>
            ) : daysUntilFire === 0 ? (
              <>
                <span className="fire-icon">🔥</span>
                <strong>TODAY</strong> - Camp Fire ignition (6:33 AM)
              </>
            ) : (
              <>
                <span className="fire-icon">🔥</span>
                Fire occurred <strong>{Math.abs(daysUntilFire)} days ago</strong>
              </>
            )}
          </p>
        </div>

        <motion.div
          className="critical-alert-indicator"
          animate={{
            boxShadow: daysSinceCritical !== null ? [
              `0 0 10px rgba(239, 68, 68, 0.5)`,
              `0 0 20px rgba(239, 68, 68, 0.8)`,
              `0 0 10px rgba(239, 68, 68, 0.5)`
            ] : 'none'
          }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          {daysSinceCritical !== null ? (
            <>
              <span className="alert-badge">⚠️ MODEL ALERT ACTIVE</span>
              <p>Critical degradation detected {daysSinceCritical} days ago</p>
            </>
          ) : (
            <>
              <span className="normal-badge">✓ NORMAL OPERATION</span>
              <p>Component operating within normal parameters</p>
            </>
          )}
        </motion.div>
      </div>

      <div className="slider-track-container">
        <div className="slider-labels">
          <span className="label-start">Jan 2016</span>
          <span className="label-critical" style={{ left: `${((criticalAlertDate - minDate) / (maxDate - minDate)) * 100}%` }}>
            Critical Alert
          </span>
          <span className="label-end">Nov 8, 2018</span>
        </div>

        <div className="slider-wrapper">
          <input
            type="range"
            min={minDate.getTime()}
            max={maxDate.getTime()}
            value={selectedDate.getTime()}
            onChange={handleSliderChange}
            className="slider-input"
            style={{
              background: `linear-gradient(to right, #10b981 0%, #10b981 ${((criticalAlertDate - minDate) / (maxDate - minDate)) * 100}%, #ef4444 100%)`
            }}
          />
          <motion.div
            className="slider-progress-indicator"
            style={{ left: `calc(${sliderProgress}% - 12px)` }}
            animate={{
              boxShadow: daysSinceCritical !== null ? [
                `0 0 5px rgba(239, 68, 68, 0.5)`,
                `0 0 15px rgba(239, 68, 68, 0.8)`,
                `0 0 5px rgba(239, 68, 68, 0.5)`
              ] : 'none'
            }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        </div>
      </div>

      <div className="timeline-markers">
        <div className="marker-section">
          <span className="marker-label">2016-2018</span>
          <span className="marker-desc">Baseline & Degradation</span>
        </div>
        <div className="marker-section">
          <span className="marker-label">{formatDate(criticalAlertDate)}</span>
          <span className="marker-desc">Model Alert Threshold</span>
        </div>
        <div className="marker-section">
          <span className="marker-label">Nov 8, 2018</span>
          <span className="marker-desc">Camp Fire Ignition</span>
        </div>
      </div>

      <motion.div
        className="story-banner"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {selectedDate < criticalAlertDate && (
          <div className="story-text">
            <p>
              The 97-year-old C-hook on Tower 27/222 is operating normally, but years of wear are beginning to take their toll.
            </p>
          </div>
        )}
        {daysSinceCritical !== null && daysSinceCritical <= 308 && (
          <div className="story-text warning">
            <p>
              <strong>⚠️ MODEL ALERT DETECTED:</strong> Our prediction system detected critical degradation. Grid operators should schedule immediate maintenance to inspect and replace the aging C-hook before failure occurs.
            </p>
          </div>
        )}
        {daysSinceCritical > 308 && (
          <div className="story-text critical">
            <p>
              <strong>🔴 CRITICAL FAILURE IMMINENT:</strong> The C-hook stress levels are critical. Replacement is now urgent.
            </p>
          </div>
        )}
        {selectedDate >= fireDate && (
          <div className="story-text fire">
            <p>
              <strong>🔥 FIRE IGNITION:</strong> The C-hook fails under wind load. Molten metal falls onto dry brush below, starting the deadliest wildfire in California history. 85 lives lost.
            </p>
            <p style={{ marginTop: '10px', fontWeight: 'bold' }}>
              With LiveWire's 308-day warning, operators would have time to replace the hook and prevent this disaster.
            </p>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default TimeSlider;
