import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar
} from 'recharts';
import './LiveComponentDashboard.css';

const LiveComponentDashboard = () => {
  const [initialized, setInitialized] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [componentSummary, setComponentSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Initialize the live component system (generate 35 days of synthetic data)
  const initializeComponent = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/live-component/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          component_id: 'LIVE_COMPONENT_01',
          total_days: 35
        })
      });

      if (!response.ok) {
        throw new Error(`Initialization failed: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Live component initialized:', data);
      setInitialized(true);
      setError(null);

      // Fetch the summary and historical data
      await fetchData();
    } catch (err) {
      console.error('Error initializing component:', err);
      setError(`Initialization failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch current status and historical data
  const fetchData = async () => {
    try {
      // Fetch current status
      const statusResponse = await fetch('/api/live-component/status');
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setCurrentStatus(statusData);
      }

      // Fetch historical data for chart
      const historyResponse = await fetch('/api/live-component/history?days=35&interval=1');
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        // Transform readings for charting
        const chartData = historyData.readings.map((reading) => ({
          timestamp: new Date(reading.timestamp).toLocaleDateString(),
          rul_true: reading.rul_true,
          sensor_1: reading.sensor_1,
          sensor_2: reading.sensor_2,
          sensor_3: reading.sensor_3,
          time_cycles: reading.time_cycles,
        }));
        setHistoricalData(chartData);
      }

      // Fetch summary
      const summaryResponse = await fetch('/api/live-component/summary');
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setComponentSummary(summaryData);
      }

      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(`Data fetch failed: ${err.message}`);
    }
  };

  // Auto-refresh every 10 seconds if initialized
  useEffect(() => {
    if (!initialized) return;

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [initialized]);

  // Apply hardware stress
  const applyStress = async (stressType, magnitude) => {
    try {
      const response = await fetch('/api/live-component/simulate-stress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stress_type: stressType,
          magnitude: magnitude
        })
      });

      if (response.ok) {
        const data = await response.json();

        // Log the detailed stress impact
        if (data.rul_change) {
          const ruiChange = data.rul_change;
          console.log(`✅ Stress Applied: ${stressType} +${magnitude}%`);
          console.log(`   Baseline RUL: ${data.baseline_rul.rul_hours}h`);
          console.log(`   Stressed RUL: ${data.stressed_rul.rul_hours}h`);
          console.log(`   Change: ${ruiChange.hours > 0 ? '+' : ''}${ruiChange.hours}h (${ruiChange.percent > 0 ? '+' : ''}${ruiChange.percent}%)`);
          console.log(`   Direction: ${ruiChange.direction}`);
        }

        // Immediately fetch updated status
        await fetchData();
      } else {
        throw new Error(`Stress simulation failed: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error applying stress:', err);
      setError(`Stress simulation failed: ${err.message}`);
    }
  };

  // Format time remaining
  const formatTimeRemaining = (hours) => {
    if (!hours || hours < 0) return 'N/A';
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours < 24) return `${Math.round(hours)}h`;
    return `${(hours / 24).toFixed(1)}d`;
  };

  // Get risk color
  const getRiskColor = (zone) => {
    switch (zone) {
      case 'green':
        return '#22c55e';
      case 'yellow':
        return '#f97316';
      case 'red':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  // Not initialized yet - show init button
  if (!initialized) {
    return (
      <div className="live-component-container">
        <div className="init-panel">
          <h1>Live Component System</h1>
          <p>Generate 35 days of synthetic degradation data and track a live component</p>
          <button
            onClick={initializeComponent}
            disabled={loading}
            className="init-button"
          >
            {loading ? 'Initializing...' : 'Initialize Live Component'}
          </button>
          {error && <div className="error-message">{error}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="live-component-container">
      {/* Header */}
      <div className="lc-header">
        <div className="header-left">
          <h1>Live Component Monitoring System</h1>
          <p>Real-time RUL prediction with 35-day degradation baseline</p>
          {currentStatus?.data_source === 'elastic' && (
            <div className="data-source-badge elastic">
              <span className="pulse"></span>
              Data from Elasticsearch (Live Hardware)
            </div>
          )}
          {currentStatus?.data_source === 'synthetic' && (
            <div className="data-source-badge synthetic">
              Data from Synthetic Baseline
            </div>
          )}
        </div>
        <div className="header-right">
          <button
            onClick={fetchData}
            disabled={loading}
            className="refresh-button"
          >
            <RefreshCw size={16} />
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          {lastUpdated && (
            <span className="last-updated">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Current Status Panel */}
      {currentStatus && (
        <div className="status-panel">
          <div className="status-card">
            <h3>Component Status</h3>
            <div className="status-content">
              <div className="status-item">
                <span className="label">Component ID</span>
                <span className="value">{currentStatus.component_id}</span>
              </div>
              <div className="status-item">
                <span className="label">Location</span>
                <span className="value">
                  {currentStatus.location?.name || 'LA Downtown Grid'}
                  ({currentStatus.location?.lat?.toFixed(4)}, {currentStatus.location?.lon?.toFixed(4)})
                </span>
              </div>
              <div className="status-item">
                <span className="label">Last Update</span>
                <span className="value">{new Date(currentStatus.last_update).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* RUL Status */}
          {currentStatus.rul_prediction && (
            <div className="rul-card">
              <h3>RUL Prediction</h3>
              <div className="rul-display">
                <div className="rul-value" style={{ color: getRiskColor(currentStatus.rul_prediction.risk_zone) }}>
                  {formatTimeRemaining(currentStatus.rul_prediction.rul_hours)}
                </div>
                <div className="rul-details">
                  <div className="detail-row">
                    <span className="label">RUL Hours:</span>
                    <span className="value">{currentStatus.rul_prediction.rul_hours?.toFixed(2)}h</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">RUL Days:</span>
                    <span className="value">{currentStatus.rul_prediction.rul_days?.toFixed(2)}d</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Risk Zone:</span>
                    <span
                      className="risk-badge"
                      style={{ backgroundColor: getRiskColor(currentStatus.rul_prediction.risk_zone) }}
                    >
                      {currentStatus.rul_prediction.risk_zone?.toUpperCase()}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Risk Score:</span>
                    <span className="value">{(currentStatus.rul_prediction.risk_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Current Readings */}
          {currentStatus.current_reading && (
            <div className="readings-card">
              <h3>Current Sensor Readings</h3>
              <div className="sensor-grid">
                <div className="sensor-item">
                  <span className="sensor-label">sensor_1 (vibration)</span>
                  <span className="sensor-value">{currentStatus.current_reading.sensor_1?.toFixed(2)}</span>
                </div>
                <div className="sensor-item">
                  <span className="sensor-label">sensor_2 (temperature)</span>
                  <span className="sensor-value">{currentStatus.current_reading.sensor_2?.toFixed(2)}</span>
                </div>
                <div className="sensor-item">
                  <span className="sensor-label">sensor_3</span>
                  <span className="sensor-value">{currentStatus.current_reading.sensor_3?.toFixed(2)}</span>
                </div>
                <div className="sensor-item">
                  <span className="sensor-label">sensor_4</span>
                  <span className="sensor-value">{currentStatus.current_reading.sensor_4?.toFixed(2)}</span>
                </div>
                <div className="sensor-item">
                  <span className="sensor-label">op_setting_1</span>
                  <span className="sensor-value">{currentStatus.current_reading.op_setting_1?.toFixed(2)}</span>
                </div>
                <div className="sensor-item">
                  <span className="sensor-label">time_cycles</span>
                  <span className="sensor-value">{currentStatus.current_reading.time_cycles}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Hardware Stress Controls */}
      <div className="stress-panel">
        <h3>Hardware Stress Simulation</h3>
        <p className="stress-description">
          Apply simulated hardware stress to test model responsiveness
        </p>
        <div className="stress-controls">
          <div className="stress-group">
            <h4>Temperature Stress</h4>
            <div className="button-row">
              <button onClick={() => applyStress('temperature', 10)}>+10%</button>
              <button onClick={() => applyStress('temperature', 25)}>+25%</button>
              <button onClick={() => applyStress('temperature', 50)}>+50%</button>
            </div>
          </div>
          <div className="stress-group">
            <h4>Vibration Stress</h4>
            <div className="button-row">
              <button onClick={() => applyStress('vibration', 10)}>+10%</button>
              <button onClick={() => applyStress('vibration', 25)}>+25%</button>
              <button onClick={() => applyStress('vibration', 50)}>+50%</button>
            </div>
          </div>
          <div className="stress-group">
            <h4>All Sensors</h4>
            <div className="button-row">
              <button onClick={() => applyStress('all', 10)}>+10%</button>
              <button onClick={() => applyStress('all', 25)}>+25%</button>
              <button onClick={() => applyStress('all', 50)}>+50%</button>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Degradation Chart */}
      {historicalData.length > 0 && (
        <div className="chart-panel">
          <h3>Historical Degradation Curve (35 Days)</h3>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={historicalData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                label={{ value: 'Time (Days)', position: 'insideBottomRight', offset: -5 }}
              />
              <YAxis
                yAxisId="left"
                label={{ value: 'RUL (Cycles)', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                label={{ value: 'Sensor Values', angle: 90, position: 'insideRight' }}
              />
              <Tooltip />
              <Legend />

              {/* RUL Curve */}
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="rul_true"
                stroke="#ef4444"
                name="RUL (Cycles)"
                strokeWidth={2}
                dot={false}
              />

              {/* Sensor trends */}
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="sensor_1"
                stroke="#3b82f6"
                name="Sensor 1 (Vibration)"
                strokeWidth={1}
                dot={false}
                opacity={0.7}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="sensor_2"
                stroke="#f97316"
                name="Sensor 2 (Temperature)"
                strokeWidth={1}
                dot={false}
                opacity={0.7}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Summary Information */}
      {componentSummary && (
        <div className="summary-panel">
          <div className="summary-card">
            <h3>System Summary</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="label">Total Readings</span>
                <span className="value">{componentSummary.historical_data?.total_readings}</span>
              </div>
              <div className="summary-item">
                <span className="label">Days of Data</span>
                <span className="value">{componentSummary.historical_data?.days_of_data}</span>
              </div>
              <div className="summary-item">
                <span className="label">Initial RUL</span>
                <span className="value">{componentSummary.historical_data?.initial_rul_cycles} cycles</span>
              </div>
              <div className="summary-item">
                <span className="label">Final RUL</span>
                <span className="value">{componentSummary.historical_data?.final_rul_cycles} cycles</span>
              </div>
              <div className="summary-item">
                <span className="label">Current RUL</span>
                <span className="value" style={{ color: getRiskColor(componentSummary.current_state?.risk_zone) }}>
                  {formatTimeRemaining(componentSummary.current_state?.rul_hours)}
                </span>
              </div>
              <div className="summary-item">
                <span className="label">Risk Status</span>
                <span
                  className="risk-badge"
                  style={{ backgroundColor: getRiskColor(componentSummary.current_state?.risk_zone) }}
                >
                  {componentSummary.current_state?.risk_zone?.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="help-panel">
        <h4>System Information</h4>
        <ul>
          <li><strong>Historical Data:</strong> 35 days of simulated component degradation (420 readings at 12/day)</li>
          <li><strong>Live Component:</strong> Starts from end of historical data (highly degraded state)</li>
          <li><strong>RUL Prediction:</strong> Uses Gradient Boosting model trained on NASA CMaps turbofan data</li>
          <li><strong>Model Note:</strong> Time-based predictions (88% importance on time_normalized) - sensor changes have minimal impact</li>
          <li><strong>Stress Simulation:</strong> Modifies sensor readings to test model sensitivity</li>
        </ul>
      </div>
    </div>
  );
};

export default LiveComponentDashboard;
