import React, { useState, useEffect } from 'react';
import { Activity, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import './ElasticsearchDashboard.css';

const ElasticsearchDashboard = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Elasticsearch Serverless Dashboard URLs
  const ELASTIC_DASHBOARD_URL = "https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/dashboards#/view/893b0606-6fc1-48f8-8f1d-4b760d160de3?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-15m,to:now))";
  const ELASTIC_SPACE_URL = "https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/r/s/oxRR4";
  
  // For embedding, we need to add embed=true parameter  
  const EMBEDDED_DASHBOARD_URL = `${ELASTIC_DASHBOARD_URL}&embed=true`;
  const EMBEDDED_SPACE_URL = `${ELASTIC_SPACE_URL}?embed=true`;

  useEffect(() => {
    // Simulate loading time
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, [refreshKey]);

  const handleRefresh = () => {
    setIsLoading(true);
    setRefreshKey(prev => prev + 1);
  };

  const handleIframeError = () => {
    setDashboardError(true);
    setIsLoading(false);
  };

  const openInNewTab = () => {
    window.open(ELASTIC_DASHBOARD_URL, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="elasticsearch-dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <Activity className="dashboard-icon" />
          <h2>Real-Time Cable Monitoring Dashboard</h2>
        </div>
        <div className="header-controls">
          <button 
            className="refresh-btn"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`refresh-icon ${isLoading ? 'spinning' : ''}`} />
            Refresh
          </button>
          <button 
            className="external-btn"
            onClick={openInNewTab}
          >
            <ExternalLink className="external-icon" />
            Open Full Dashboard
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner">
              <Activity className="spinner-icon" />
              <p>Loading Elasticsearch Dashboard...</p>
            </div>
          </div>
        )}

        {dashboardError ? (
          <div className="dashboard-error">
            <AlertCircle className="error-icon" />
            <h3>Dashboard Unavailable</h3>
            <p>
              The embedded Elasticsearch dashboard cannot be displayed due to security restrictions.
              Click "Open Full Dashboard" to view it in a new tab.
            </p>
            <div className="error-actions">
              <button className="retry-btn" onClick={handleRefresh}>
                Try Again
              </button>
              <button className="external-btn" onClick={openInNewTab}>
                <ExternalLink className="external-icon" />
                Open Dashboard
              </button>
            </div>
          </div>
        ) : (
          <div className="iframe-container">
            <iframe
              key={refreshKey}
              src={EMBEDDED_DASHBOARD_URL}
              className="elasticsearch-iframe"
              title="LiveWire Elasticsearch Dashboard"
              onLoad={() => setIsLoading(false)}
              onError={handleIframeError}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
              referrerPolicy="strict-origin-when-cross-origin"
            />
          </div>
        )}
      </div>

      <div className="dashboard-info">
        <div className="info-grid">
          <div className="info-card">
            <h4>🏆 AI Model</h4>
            <p>Optimized Gradient Boosting</p>
            <span className="accuracy">99.73% Accuracy</span>
          </div>
          <div className="info-card">
            <h4>📊 Data Source</h4>
            <p>365,000 Real Cable Samples</p>
            <span className="status">Live Monitoring</span>
          </div>
          <div className="info-card">
            <h4>🚨 Risk Zones</h4>
            <p>Green • Yellow • Red</p>
            <span className="monitoring">Real-time Alerts</span>
          </div>
          <div className="info-card">
            <h4>⚡ Sensors</h4>
            <p>Temp • Vibration • Strain • Power</p>
            <span className="raspberry-pi">Raspberry Pi</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ElasticsearchDashboard;