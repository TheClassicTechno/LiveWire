import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { X, AlertCircle, Zap, TrendingDown, TrendingUp } from 'lucide-react';
import './SensorDetailsPanel.css';

/**
 * SensorDetailsPanel
 * Displays live sensor data, historical degradation trends, and RUL predictions
 * Connects to Phase 3 live component API for real-time updates
 *
 * NEW FEATURES:
 * - Shows data source (LIVE from Elasticsearch or BASELINE synthetic)
 * - Real-time RUL countdown with live updates every 2 seconds
 * - RUL change from baseline tracking
 * - Stress indicators showing which sensors are elevated
 * - 5-minute RUL trend visualization
 */

const SensorDetailsPanel = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [sensorStatus, setSensorStatus] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);

  // Track RUL history for trend visualization
  const [rulTrendData, setRulTrendData] = useState([]);
  const [dataSource, setDataSource] = useState('synthetic');
  const [elasticAvailable, setElasticAvailable] = useState(false);

  // Speedup/acceleration mode
  const [speedupActive, setSpeedupActive] = useState(false);
  const [speedupProgress, setSpeedupProgress] = useState(0);
  const [speedupDays, setSpeedupDays] = useState(0);
  const [speedupSummary, setSpeedupSummary] = useState(null);
  const [speedupTrendData, setSpeedupTrendData] = useState([]); // Track speedup simulation graph data

  // Fetch sensor data from Phase 3 live component API
  const fetchSensorData = async () => {
    try {
      setError(null);

      // Check if component is initialized
      let statusRes = await fetch('/api/live-component/status');

      // If not found or bad request, try to initialize
      if (!statusRes.ok && (statusRes.status === 400 || statusRes.status === 404)) {
        console.log('📡 Initializing live component...');
        const initRes = await fetch('/api/live-component/init', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        });

        if (!initRes.ok) {
          const errorText = await initRes.text();
          console.error('❌ Init failed:', errorText);
          throw new Error(`Failed to initialize component: ${initRes.status} ${errorText}`);
        }

        // Retry fetch after initialization
        statusRes = await fetch('/api/live-component/status');
      }

      if (!statusRes.ok) {
        throw new Error(`API error: ${statusRes.status} ${statusRes.statusText}`);
      }

      // Parse JSON with error handling
      let statusData;
      let responseText = '';
      try {
        responseText = await statusRes.text();
        if (!responseText) {
          throw new Error('Empty response from status endpoint');
        }
        statusData = JSON.parse(responseText);
      } catch (parseErr) {
        console.error('Failed to parse status response:', parseErr);
        throw new Error(`Invalid JSON response from status endpoint`);
      }

      setSensorStatus(statusData);
      setDataSource(statusData.data_source || 'synthetic');
      setElasticAvailable(statusData.elastic_available || false);

      // Add to RUL trend data (keep last 150 points = 5 minutes at 2-second intervals)
      if (statusData.rul_prediction?.rul_hours !== undefined) {
        const newTrendPoint = {
          timestamp: new Date().toLocaleTimeString(),
          rul: statusData.rul_prediction.rul_hours,
          riskZone: statusData.rul_prediction.risk_zone,
          dataSource: statusData.data_source,
        };

        setRulTrendData((prev) => {
          const updated = [...prev, newTrendPoint];
          // Keep only last 150 points (5 minutes at 2-sec intervals)
          return updated.slice(-150);
        });
      }

      // Fetch historical baseline data (35 days of simulated data)
      const historyRes = await fetch('/api/live-component/history?days=35&interval=2');
      if (!historyRes.ok) throw new Error('Failed to fetch history');

      let historyData;
      try {
        historyData = await historyRes.json();
      } catch (parseErr) {
        console.error('Failed to parse history response:', parseErr);
        historyData = { readings: [] };
      }

      // Populate LIVE graph with baseline data on first load
      if (historyData.readings && Array.isArray(historyData.readings) && rulTrendData.length === 0) {
        const baselineGraphData = historyData.readings.map((reading, index) => ({
          timestamp: `${index * 4}h`, // Roughly 4 hours per reading (interval=2 from 35 days)
          rul: (reading.rul_true || 0) / 24, // Convert cycles to hours for consistent display
          riskZone: 'green', // Baseline data is stable
          dataSource: 'baseline',
        }));
        setRulTrendData(baselineGraphData);
        console.log(`📊 Loaded ${baselineGraphData.length} baseline data points to live graph`);
      }

      // Format history data for other uses
      if (historyData.readings && Array.isArray(historyData.readings)) {
        const formattedData = historyData.readings.map((reading) => ({
          timestamp: new Date(reading.timestamp).toLocaleDateString(),
          rul: reading.rul_true || 0,
          temp: reading.sensor_2 || 0,
          vibration: reading.sensor_1 || 0,
          strain: reading.sensor_3 || 0,
        }));
        setHistoricalData(formattedData);
      }

      // Fetch summary
      const summaryRes = await fetch('/api/live-component/summary');
      if (summaryRes.ok) {
        let summaryData;
        try {
          summaryData = await summaryRes.json();
          setSummary(summaryData);
        } catch (parseErr) {
          console.error('Failed to parse summary response:', parseErr);
        }
      }

      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching sensor data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch and setup polling
  useEffect(() => {
    if (!isOpen) return;

    setLoading(true);

    // Fetch immediately
    fetchSensorData();

    // Poll for updates: 2 seconds when Elasticsearch available, 10 seconds otherwise
    // This will be determined after first fetch
    let interval;

    const startPolling = () => {
      interval = setInterval(fetchSensorData, elasticAvailable ? 2000 : 10000);
    };

    startPolling();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isOpen, elasticAvailable]);

  // Handle speedup/acceleration timeline
  const handleSpeedup = async () => {
    if (speedupActive) return; // Already running

    setSpeedupActive(true);
    setSpeedupProgress(0);
    setSpeedupDays(0);

    try {
      // Call backend to generate 30-day degradation trajectory
      const response = await fetch('/api/live-component/accelerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          days: 30,
          acceleration_factor: 100
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      const trajectory = data.trajectory || [];

      if (trajectory.length === 0) {
        setError('Failed to generate degradation trajectory');
        setSpeedupActive(false);
        return;
      }

      setSpeedupSummary(data.summary);

      // Initialize speedup trend data with baseline data
      // Copy the live graph's baseline data to speedup graph
      setSpeedupTrendData(rulTrendData.map(point => ({...point})));

      // Animate through trajectory: each day shown for 100ms
      for (let i = 0; i < trajectory.length; i++) {
        const point = trajectory[i];

        // Update sensor status with current trajectory point
        setSensorStatus({
          ...sensorStatus,
          current_reading: point.reading,
          rul_prediction: point.rul_prediction,
          data_source: 'synthetic',
          acceleration: true,
          acceleration_day: point.day,
          acceleration_total: trajectory.length
        });

        setSpeedupProgress(((i + 1) / trajectory.length) * 100);
        setSpeedupDays(point.day);

        // Add trajectory data to SPEEDUP graph (not live graph)
        setSpeedupTrendData((prev) => {
          const newTrendPoint = {
            timestamp: `Day ${point.day}`,
            rul: point.rul_hours,
            riskZone: point.risk_zone,
            dataSource: 'accelerated',
          };
          const updated = [...prev, newTrendPoint];
          return updated; // Keep all speedup trajectory points
        });

        // Wait 100ms before next frame (30 days in ~3 seconds)
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Animation complete - STAY OPEN, don't set speedupActive to false
      // setSpeedupActive(false);  // REMOVED: Keep panel open after animation
    } catch (err) {
      console.error('Speedup error:', err);
      setError(err.message);
      setSpeedupActive(false);
    }
  };

  const getRiskColor = (zone) => {
    const zones = {
      green: '#00ff88',
      yellow: '#ffaa00',
      orange: '#ff6600',
      red: '#ff3333',
    };
    return zones[zone?.toLowerCase()] || zones.green;
  };

  const getRiskLabel = (zone) => {
    const labels = {
      green: 'Healthy',
      yellow: 'Warning',
      orange: 'High Risk',
      red: 'Critical',
    };
    return labels[zone?.toLowerCase()] || 'Unknown';
  };

  const formatTime = (hours) => {
    if (hours === null || hours === undefined) return '--';
    if (hours >= 24) {
      return `${(hours / 24).toFixed(1)}d`;
    }
    return `${hours.toFixed(1)}h`;
  };

  const getRulChangeDisplay = () => {
    if (!sensorStatus?.rul_change_from_baseline) return null;

    const change = sensorStatus.rul_change_from_baseline;
    const isDecreasing = change.direction === 'decreasing';

    return {
      hours: change.hours,
      percent: change.percent,
      isDecreasing,
      icon: isDecreasing ? <TrendingDown size={16} /> : <TrendingUp size={16} />,
    };
  };

  const rulChange = getRulChangeDisplay();

  // Determine polling frequency message
  const pollingFrequency = elasticAvailable ? '2 seconds' : '10 seconds';
  const dataSourceMessage = elasticAvailable
    ? '📡 Live from Raspberry Pi → Elasticsearch'
    : '📊 Simulated baseline data';

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="sensor-panel-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            className="sensor-details-panel"
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          >
            {/* Header */}
            <div className="panel-header">
              <div className="header-title">
                <Zap size={20} />
                <h2>Sensor #1 - Live Monitor</h2>
              </div>
              <button className="close-btn" onClick={onClose}>
                <X size={24} />
              </button>
            </div>

            {/* Connection Status - Raspberry Pi */}
            <motion.div
              className={`connection-status ${elasticAvailable ? 'connected' : 'disconnected'}`}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="status-indicator">
                <span className={`status-dot ${elasticAvailable ? 'connected' : 'disconnected'}`}></span>
                <span className="status-text">
                  {elasticAvailable ? '🟢 Raspberry Pi Connected' : '🔴 Raspberry Pi Disconnected'}
                </span>
              </div>
              <span className="status-subtext">
                {elasticAvailable ? 'Real-time data flowing from Pi → Elasticsearch' : 'Using simulated baseline data'}
              </span>
            </motion.div>

            {/* Data Source Badge */}
            <motion.div
              className={`data-source-badge ${dataSource === 'elastic' ? 'elastic' : 'synthetic'}`}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
            >
              {elasticAvailable ? (
                <>
                  <span className="pulse-dot"></span>
                  <span className="badge-text">LIVE DATA - {dataSourceMessage}</span>
                </>
              ) : (
                <>
                  <span className="badge-text">{dataSourceMessage}</span>
                </>
              )}
            </motion.div>

            {/* Content */}
            <div className="panel-content">
              {error && (
                <motion.div
                  className="error-banner"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </motion.div>
              )}

              {loading && !sensorStatus ? (
                <div className="loading-state">
                  <div className="spinner" />
                  <p>Loading sensor data...</p>
                </div>
              ) : (
                <>
                  {/* Live Status Section */}
                  {sensorStatus && (
                    <motion.div
                      className="panel-section"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                    >
                      <h3 className="section-title">Live Status</h3>

                      {/* RUL Display - Enhanced */}
                      <div className="rul-display">
                        <div className="rul-main">
                          {/* Large RUL Countdown */}
                          <motion.div
                            className="rul-gauge"
                            style={{
                              borderColor: getRiskColor(
                                sensorStatus.rul_prediction?.risk_zone
                              ),
                            }}
                            key={sensorStatus.rul_prediction?.rul_hours}
                            animate={{ scale: 1.02 }}
                            transition={{ duration: 0.3 }}
                          >
                            <div className="rul-value">
                              {formatTime(sensorStatus.rul_prediction?.rul_hours)}
                            </div>
                            <div className="rul-label">Remaining Life</div>

                            {/* RUL Change Badge */}
                            {rulChange && (
                              <motion.div
                                className={`rul-change-badge ${rulChange.isDecreasing ? 'decreasing' : 'increasing'}`}
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 0.2 }}
                              >
                                {rulChange.icon}
                                <span>
                                  {rulChange.isDecreasing ? '-' : '+'}
                                  {Math.abs(rulChange.percent).toFixed(1)}%
                                </span>
                              </motion.div>
                            )}
                          </motion.div>

                          {/* RUL Details */}
                          <div className="rul-details">
                            <div className="detail-item">
                              <span className="label">Status</span>
                              <span
                                className="badge"
                                style={{
                                  backgroundColor: getRiskColor(
                                    sensorStatus.rul_prediction?.risk_zone
                                  ),
                                  color: '#000',
                                }}
                              >
                                {getRiskLabel(sensorStatus.rul_prediction?.risk_zone)}
                              </span>
                            </div>

                            <div className="detail-item">
                              <span className="label">Risk Score</span>
                              <span className="value">
                                {(
                                  sensorStatus.rul_prediction?.risk_score * 100
                                ).toFixed(0)}%
                              </span>
                            </div>

                            <div className="detail-item">
                              <span className="label">Confidence</span>
                              <span className="value">
                                {(
                                  sensorStatus.rul_prediction?.confidence * 100
                                ).toFixed(1)}%
                              </span>
                            </div>

                            {rulChange && (
                              <div className="detail-item">
                                <span className="label">From Baseline</span>
                                <span
                                  className={`value ${rulChange.isDecreasing ? 'decreasing' : 'increasing'}`}
                                >
                                  {rulChange.isDecreasing ? '↓' : '↑'} {rulChange.hours.toFixed(2)}h
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Current Sensor Readings */}
                      <div className="sensor-readings">
                        <h4>Current Readings</h4>
                        <div className="readings-grid">
                          <div className="reading-card">
                            <div className="reading-label">Temperature</div>
                            <div className="reading-value">
                              {sensorStatus.current_reading?.sensor_2?.toFixed(1) ||
                                '--'}
                              °C
                            </div>
                            {sensorStatus.stress_indicators?.temperature && (
                              <div className={`reading-status ${sensorStatus.stress_indicators.temperature.status}`}>
                                {sensorStatus.stress_indicators.temperature.status === 'critical' && '🔴'}
                                {sensorStatus.stress_indicators.temperature.status === 'elevated' && '🟡'}
                                {sensorStatus.stress_indicators.temperature.status === 'normal' && '🟢'}
                                {sensorStatus.stress_indicators.temperature.delta_percent > 0 && '+'}
                                {sensorStatus.stress_indicators.temperature.delta_percent.toFixed(1)}%
                              </div>
                            )}
                          </div>

                          <div className="reading-card">
                            <div className="reading-label">Vibration</div>
                            <div className="reading-value">
                              {sensorStatus.current_reading?.sensor_1?.toFixed(2) ||
                                '--'}
                              g
                            </div>
                            {sensorStatus.stress_indicators?.vibration && (
                              <div className={`reading-status ${sensorStatus.stress_indicators.vibration.status}`}>
                                {sensorStatus.stress_indicators.vibration.status === 'critical' && '🔴'}
                                {sensorStatus.stress_indicators.vibration.status === 'elevated' && '🟡'}
                                {sensorStatus.stress_indicators.vibration.status === 'normal' && '🟢'}
                                {sensorStatus.stress_indicators.vibration.delta_percent > 0 && '+'}
                                {sensorStatus.stress_indicators.vibration.delta_percent.toFixed(1)}%
                              </div>
                            )}
                          </div>

                          <div className="reading-card">
                            <div className="reading-label">Strain</div>
                            <div className="reading-value">
                              {sensorStatus.current_reading?.sensor_3?.toFixed(1) ||
                                '--'}
                              με
                            </div>
                            {sensorStatus.stress_indicators?.frequency && (
                              <div className={`reading-status ${sensorStatus.stress_indicators.frequency.status}`}>
                                {sensorStatus.stress_indicators.frequency.status === 'critical' && '🔴'}
                                {sensorStatus.stress_indicators.frequency.status === 'elevated' && '🟡'}
                                {sensorStatus.stress_indicators.frequency.status === 'normal' && '🟢'}
                                {sensorStatus.stress_indicators.frequency.delta_percent > 0 && '+'}
                                {sensorStatus.stress_indicators.frequency.delta_percent.toFixed(1)}%
                              </div>
                            )}
                          </div>

                          <div className="reading-card">
                            <div className="reading-label">Last Update</div>
                            <div className="reading-value">
                              {lastUpdated
                                ? lastUpdated.toLocaleTimeString()
                                : '--'}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Real-Time RUL Trend Section - Live Raspberry Pi data */}
                  {rulTrendData.length > 0 && (
                    <motion.div
                      className="panel-section"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.15 }}
                    >
                      <div className="graph-header">
                        <div>
                          <h3 className="section-title">
                            📡 Live RUL Monitoring
                            {elasticAvailable && <span style={{color: '#22c55e', marginLeft: '8px'}}>● LIVE from Pi</span>}
                            {!elasticAvailable && <span style={{color: '#f59e0b', marginLeft: '8px'}}>● Simulated</span>}
                          </h3>
                          <p style={{fontSize: '11px', color: '#94a3b8', margin: '4px 0 0 0'}}>
                            Real-time RUL prediction as Raspberry Pi sensor data flows in
                          </p>
                        </div>
                      </div>
                      <div className="chart-container">
                        <ResponsiveContainer width="100%" height={220}>
                          <LineChart data={rulTrendData}>
                            <CartesianGrid
                              strokeDasharray="3 3"
                              stroke="#334155"
                            />
                            <XAxis
                              dataKey="timestamp"
                              stroke="#64748b"
                              style={{ fontSize: '10px' }}
                              tick={{ fill: '#64748b' }}
                              interval={Math.max(0, Math.floor(rulTrendData.length / 6))}
                              label={{ value: 'Time', position: 'insideBottomRight', offset: -5, style: {fontSize: '11px', fill: '#94a3b8'} }}
                            />
                            <YAxis
                              stroke="#64748b"
                              style={{ fontSize: '10px' }}
                              tick={{ fill: '#64748b' }}
                              domain={['dataMin - 1', 'dataMax + 1']}
                              label={{ value: 'RUL (hours)', angle: -90, position: 'insideLeft', style: {fontSize: '11px', fill: '#94a3b8'} }}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #475569',
                                borderRadius: '8px',
                              }}
                              labelStyle={{ color: '#e2e8f0' }}
                              formatter={(value) => [value.toFixed(1) + 'h', 'RUL']}
                              labelFormatter={(label) => `Time: ${label}`}
                            />
                            <Line
                              type="monotone"
                              dataKey="rul"
                              stroke="#00d4ff"
                              dot={false}
                              isAnimationActive={false}
                              strokeWidth={2.5}
                              name="RUL (hours)"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </motion.div>
                  )}

                  {/* Speedup Simulation Graph - Shows 300-day projection at high speed */}
                  {speedupTrendData.length > 0 && (
                    <motion.div
                      className="panel-section"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                    >
                      <div className="graph-header">
                        <div>
                          <h3 className="section-title">
                            ⚡ Speedup Simulation (300-Day Projection)
                            {speedupActive && <span style={{color: '#ff6b35', marginLeft: '8px'}}>● Simulating</span>}
                            {!speedupActive && speedupTrendData.length > 0 && <span style={{color: '#8b5cf6', marginLeft: '8px'}}>● Complete</span>}
                          </h3>
                          <p style={{fontSize: '11px', color: '#94a3b8', margin: '4px 0 0 0'}}>
                            Accelerated 300-day degradation simulation based on current sensor readings
                          </p>
                        </div>
                      </div>
                      <div className="chart-container">
                        <ResponsiveContainer width="100%" height={220}>
                          <LineChart data={speedupTrendData}>
                            <CartesianGrid
                              strokeDasharray="3 3"
                              stroke="#334155"
                            />
                            <XAxis
                              dataKey="timestamp"
                              stroke="#64748b"
                              style={{ fontSize: '10px' }}
                              tick={{ fill: '#64748b' }}
                              interval={Math.max(0, Math.floor(speedupTrendData.length / 6))}
                              label={{ value: 'Simulated Days', position: 'insideBottomRight', offset: -5, style: {fontSize: '11px', fill: '#94a3b8'} }}
                            />
                            <YAxis
                              stroke="#64748b"
                              style={{ fontSize: '10px' }}
                              tick={{ fill: '#64748b' }}
                              domain={['dataMin - 10', 'dataMax + 10']}
                              label={{ value: 'RUL (hours)', angle: -90, position: 'insideLeft', style: {fontSize: '11px', fill: '#94a3b8'} }}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #475569',
                                borderRadius: '8px',
                              }}
                              labelStyle={{ color: '#e2e8f0' }}
                              formatter={(value) => [value.toFixed(1) + 'h', 'RUL']}
                              labelFormatter={(label) => `${label}`}
                            />
                            <Line
                              type="monotone"
                              dataKey="rul"
                              stroke="#ff6b35"
                              dot={false}
                              isAnimationActive={false}
                              strokeWidth={2.5}
                              name="Projected RUL"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                      {speedupSummary && !speedupActive && (
                        <div style={{marginTop: '12px', padding: '12px', background: 'rgba(255, 107, 53, 0.1)', borderRadius: '6px', border: '1px solid rgba(255, 107, 53, 0.2)'}}>
                          <p style={{fontSize: '12px', color: '#e2e8f0', margin: 0}}>
                            <strong>Projection:</strong> {speedupSummary.start_rul?.toFixed(0)}h → {speedupSummary.end_rul?.toFixed(0)}h
                            {speedupSummary.days_to_critical < 300 && (
                              <span style={{color: '#ff6b35', marginLeft: '12px'}}>
                                🔴 Critical at Day {speedupSummary.days_to_critical}
                              </span>
                            )}
                          </p>
                        </div>
                      )}
                    </motion.div>
                  )}

                  {/* Summary Statistics */}
                  {summary && summary.historical_data && (
                    <motion.div
                      className="panel-section"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.25 }}
                    >
                      <h3 className="section-title">Statistics</h3>
                      <div className="stats-grid">
                        <div className="stat-box">
                          <div className="stat-label">Data Points</div>
                          <div className="stat-value">
                            {summary.historical_data.total_readings || '--'}
                          </div>
                        </div>

                        <div className="stat-box">
                          <div className="stat-label">Time Period</div>
                          <div className="stat-value">
                            {summary.historical_data.days_of_data || '--'} days
                          </div>
                        </div>

                        <div className="stat-box">
                          <div className="stat-label">Initial RUL</div>
                          <div className="stat-value">
                            {summary.historical_data.initial_rul_cycles || '--'}
                            h
                          </div>
                        </div>

                        <div className="stat-box">
                          <div className="stat-label">Final RUL</div>
                          <div className="stat-value">
                            {summary.historical_data.final_rul_cycles || '--'} h
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Speedup Timeline */}
                  <motion.div
                    className="panel-section speedup-section"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <button
                      className={`speedup-button ${speedupActive ? 'active' : ''}`}
                      onClick={handleSpeedup}
                      disabled={speedupActive || loading}
                    >
                      {speedupActive ? (
                        <>
                          <span className="pulse-dot"></span>
                          Simulating {speedupDays} / 30 Days...
                        </>
                      ) : (
                        <>
                          <span className="speedup-emoji">⏩</span>
                          Show 30-Day Timeline
                        </>
                      )}
                    </button>

                    {speedupActive && (
                      <motion.div
                        className="speedup-timeline"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                      >
                        <div className="timeline-progress-container">
                          <div className="progress-bar">
                            <motion.div
                              className="progress-fill"
                              style={{ width: `${speedupProgress}%` }}
                              transition={{ type: 'tween', duration: 0.1 }}
                            />
                          </div>
                          <div className="timeline-label">
                            Day <span className="day-number">{speedupDays}</span> of 30
                          </div>
                        </div>

                        {speedupSummary && (
                          <div className="speedup-summary">
                            <div className="summary-item">
                              <span className="summary-label">Start RUL:</span>
                              <span className="summary-value">{speedupSummary.start_rul?.toFixed(0)}h</span>
                              <span className={`summary-zone ${speedupSummary.start_zone}`}>
                                {speedupSummary.start_zone?.toUpperCase()}
                              </span>
                            </div>
                            <div className="summary-arrow">→</div>
                            <div className="summary-item">
                              <span className="summary-label">End RUL:</span>
                              <span className="summary-value">{speedupSummary.end_rul?.toFixed(0)}h</span>
                              <span className={`summary-zone ${speedupSummary.end_zone}`}>
                                {speedupSummary.end_zone?.toUpperCase()}
                              </span>
                            </div>
                          </div>
                        )}

                        {speedupSummary && speedupSummary.days_to_critical && (
                          <div className="critical-day-alert">
                            🔴 <strong>Critical at Day {speedupSummary.days_to_critical}</strong>
                            {speedupSummary.days_to_critical < 10
                              ? ' - Very fast degradation!'
                              : speedupSummary.days_to_critical < 20
                              ? ' - Moderate degradation'
                              : ' - Slow degradation'}
                          </div>
                        )}
                      </motion.div>
                    )}
                  </motion.div>

                  {/* Info Footer */}
                  <div className="panel-footer">
                    <p>
                      {dataSourceMessage} | Updates every {pollingFrequency}
                    </p>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SensorDetailsPanel;
