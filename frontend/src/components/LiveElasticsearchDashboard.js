import React, { useState, useEffect } from 'react';
import { RefreshCw, Activity, ExternalLink, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import './ElasticsearchDashboard.css';

const LiveElasticsearchDashboard = () => {
  // Fetch real data from backend proxy (no longer hardcoded)
  const [sensorData, setSensorData] = useState({
    avgPower: 0,
    avgStrain: 0,
    avgTemp: 0,
    avgVibration: 0,
    maxPower: 0,
    maxTemp: 0,
    sampleCount: 0,
    riskZones: {}
  });

  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  // Fetch sensor data from backend every 5 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/sensor-data');
        if (!response.ok) throw new Error('Failed to fetch sensor data');
        const data = await response.json();
        setSensorData(data);
        setLastUpdated(new Date());
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching sensor data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Fetch alerts from backend every 10 seconds
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('/api/alerts');
        if (!response.ok) throw new Error('Failed to fetch alerts');
        const data = await response.json();
        setAlerts(data.alerts || []);
      } catch (err) {
        console.error('Error fetching alerts:', err);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Open the full Elasticsearch dashboard
  const openDashboard = () => {
    window.open(
      'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/dashboards#/view/893b0606-6fc1-48f8-8f1d-4b760d160de3?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-15m,to:now))',
      '_blank',
      'noopener,noreferrer'
    );
  };

  const openKibana = () => {
    window.open(
      'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/r/s/oxRR4',
      '_blank',
      'noopener,noreferrer'
    );
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading real-time data from Elasticsearch...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  const getStatusColor = (value, type) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return '#6b7280';
    
    switch(type) {
      case 'power':
        return numValue > 500 ? '#ef4444' : numValue > 200 ? '#f59e0b' : '#10b981';
      case 'strain':
        return numValue > 150 ? '#ef4444' : numValue > 100 ? '#f59e0b' : '#10b981';
      case 'temperature':
        return numValue > 50 ? '#ef4444' : numValue > 35 ? '#f59e0b' : '#10b981';
      case 'vibration':
        return numValue > 1.0 ? '#ef4444' : numValue > 0.7 ? '#f59e0b' : '#10b981';
      default:
        return '#10b981';
    }
  };

  const getStatusIcon = (value, type) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return <AlertTriangle size={20} />;
    
    const color = getStatusColor(value, type);
    if (color === '#ef4444') return <XCircle size={20} style={{ color }} />;
    if (color === '#f59e0b') return <AlertTriangle size={20} style={{ color }} />;
    return <CheckCircle size={20} style={{ color }} />;
  };

  return (
    <div className="elasticsearch-dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <Activity className="dashboard-icon" />
          <h2>Elasticsearch Dashboard Data</h2>
          <span className="live-indicator">
            <span className="pulse-dot"></span>
            DASHBOARD DATA
          </span>
        </div>
        <div className="header-controls">
          <button 
            className="refresh-btn"
            onClick={openDashboard}
            title="Open Full Dashboard"
          >
            <ExternalLink size={16} />
            Open Live Dashboard
          </button>
          <button 
            className="refresh-btn"
            onClick={openKibana}
            title="Open Kibana"
          >
            <RefreshCw size={16} />
            Open Kibana
          </button>
        </div>
      </div>

      <div className="last-updated">
        Dashboard data from: {lastUpdated.toLocaleString()}
        <span className="data-count"> • {sensorData.totalHits}</span>
      </div>

      {/* Live Sensor Data Cards */}
      <div className="sensor-grid">
        {/* Power */}
        <div className="sensor-card" style={{ borderColor: getStatusColor(sensorData?.avgPower, 'power') }}>
          <div className="sensor-header">
            {getStatusIcon(sensorData?.avgPower, 'power')}
            <h3>Power Monitoring</h3>
          </div>
          <div className="sensor-values">
            <div className="primary-value">
              <span className="label">Average</span>
              <span className="value" style={{ color: getStatusColor(sensorData.avgPower, 'power') }}>
                {sensorData.avgPower} W
              </span>
            </div>
            <div className="secondary-value">
              <span className="label">Current</span>
              <span className="value">{sensorData.lastPower} W</span>
            </div>
          </div>
        </div>

        {/* Strain */}
        <div className="sensor-card" style={{ borderColor: getStatusColor(sensorData.avgStrain, 'strain') }}>
          <div className="sensor-header">
            {getStatusIcon(sensorData.avgStrain, 'strain')}
            <h3>Strain Analysis</h3>
          </div>
          <div className="sensor-values">
            <div className="primary-value">
              <span className="label">Average</span>
              <span className="value" style={{ color: getStatusColor(sensorData.avgStrain, 'strain') }}>
                {sensorData.avgStrain}
              </span>
            </div>
            <div className="secondary-value">
              <span className="label">Current</span>
              <span className="value">{sensorData.lastStrain}</span>
            </div>
          </div>
        </div>

        {/* Temperature */}
        <div className="sensor-card" style={{ borderColor: getStatusColor(sensorData.avgTemp, 'temperature') }}>
          <div className="sensor-header">
            {getStatusIcon(sensorData.avgTemp, 'temperature')}
            <h3>Temperature</h3>
          </div>
          <div className="sensor-values">
            <div className="primary-value">
              <span className="label">Average</span>
              <span className="value" style={{ color: getStatusColor(sensorData.avgTemp, 'temperature') }}>
                {sensorData.avgTemp}°C
              </span>
            </div>
            <div className="secondary-value">
              <span className="label">Current</span>
              <span className="value">{sensorData.lastTemp}°C</span>
            </div>
          </div>
        </div>

        {/* Vibration */}
        <div className="sensor-card" style={{ borderColor: getStatusColor(sensorData.avgVibration, 'vibration') }}>
          <div className="sensor-header">
            {getStatusIcon(sensorData.avgVibration, 'vibration')}
            <h3>Vibration</h3>
          </div>
          <div className="sensor-values">
            <div className="primary-value">
              <span className="label">Average</span>
              <span className="value" style={{ color: getStatusColor(sensorData.avgVibration, 'vibration') }}>
                {sensorData.avgVibration}
              </span>
            </div>
            <div className="secondary-value">
              <span className="label">Max</span>
              <span className="value">{sensorData.maxTemp || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Model Performance */}
      <div className="model-performance">
        <h3>🎯 AI Model Performance</h3>
        <div className="performance-grid">
          <div className="performance-item success">
            <span className="performance-value">99.73%</span>
            <span className="performance-label">Model Accuracy</span>
          </div>
          <div className="performance-item info">
            <span className="performance-value">365,002</span>
            <span className="performance-label">Training Samples</span>
          </div>
          <div className="performance-item warning">
            <span className="performance-value">Real-time</span>
            <span className="performance-label">Monitoring</span>
          </div>
          <div className="performance-item success">
            <span className="performance-value">3 Classes</span>
            <span className="performance-label">Normal/Degradation/Fault</span>
          </div>
        </div>
      </div>

      {/* Note about accessing live dashboard */}
      <div className="dashboard-note">
        <AlertTriangle size={16} />
        <span>This shows your current dashboard data. Click "Open Live Dashboard" above for real-time updates and interactive features.</span>
      </div>
    </div>
  );
};

export default LiveElasticsearchDashboard;