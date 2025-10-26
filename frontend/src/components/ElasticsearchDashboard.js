import React, { useState } from 'react';
import { ExternalLink, RefreshCw, Activity, AlertCircle } from 'lucide-react';
import './ElasticsearchDashboard.css';

const ElasticsearchDashboard = () => {
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const [iframeError, setIframeError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Your Elasticsearch URLs
  const dashboardUrl = 'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/dashboards#/view/893b0606-6fc1-48f8-8f1d-4b760d160de3?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-15m,to:now))';
  const kibanaUrl = 'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/r/s/oxRR4';

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    setIframeLoaded(false);
    setIframeError(false);
  };

  const openInNewTab = () => {
    window.open(dashboardUrl, '_blank', 'noopener,noreferrer');
  };

  const handleIframeLoad = () => {
    setIframeLoaded(true);
    setIframeError(false);
  };

  const handleIframeError = () => {
    setIframeError(true);
    setIframeLoaded(false);
  };

  return (
    <div className="elasticsearch-dashboard">
      <div className="dashboard-header">
        <div className="header-left">
          <Activity className="dashboard-icon" />
          <h2>Live Elasticsearch Dashboard</h2>
        </div>
        <div className="header-controls">
          <button 
            className="refresh-btn"
            onClick={handleRefresh}
            title="Refresh Dashboard"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
          <button 
            className="external-link-btn"
            onClick={openInNewTab}
            title="Open in New Tab"
          >
            <ExternalLink size={16} />
            Open Full Dashboard
          </button>
        </div>
      </div>

      <div className="dashboard-status">
        <span className="status-indicator">
          {iframeLoaded ? (
            <>
              <span className="status-dot status-online"></span>
              Dashboard Loaded Successfully
            </>
          ) : iframeError ? (
            <>
              <span className="status-dot status-error"></span>
              Dashboard Blocked by CSP - Click "Open Full Dashboard" above
            </>
          ) : (
            <>
              <span className="status-dot status-loading"></span>
              Loading Elasticsearch Dashboard...
            </>
          )}
        </span>
      </div>

      <div className="dashboard-container">
        {/* Show error message and fallback options */}
        {iframeError && (
          <div className="iframe-fallback">
            <AlertCircle size={48} className="fallback-icon" />
            <h3>Dashboard Embedding Blocked</h3>
            <p>Elasticsearch Cloud has Content Security Policy restrictions that prevent iframe embedding.</p>
            <div className="fallback-actions">
              <button 
                className="fallback-btn primary"
                onClick={openInNewTab}
              >
                <ExternalLink size={16} />
                Open Dashboard in New Tab
              </button>
              <button 
                className="fallback-btn"
                onClick={handleRefresh}
              >
                <RefreshCw size={16} />
                Try Iframe Again
              </button>
            </div>
            
            <div className="manual-access">
              <h4>Direct Access Links:</h4>
              <ul>
                <li>
                  <strong>Main Dashboard:</strong>
                  <a href={dashboardUrl} target="_blank" rel="noopener noreferrer">
                    View Live Dashboard
                  </a>
                </li>
                <li>
                  <strong>Kibana Space:</strong>
                  <a href={kibanaUrl} target="_blank" rel="noopener noreferrer">
                    Open Kibana
                  </a>
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Iframe - will try to load but likely fail due to CSP */}
        <iframe
          key={refreshKey}
          id="elasticsearch-iframe"
          src={dashboardUrl}
          title="Elasticsearch Dashboard"
          className={`dashboard-iframe ${iframeLoaded ? 'loaded' : ''} ${iframeError ? 'error' : ''}`}
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
          referrerPolicy="strict-origin-when-cross-origin"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          style={{
            width: '100%',
            height: '800px',
            border: 'none',
            borderRadius: '8px',
            display: iframeError ? 'none' : 'block'
          }}
        />

        {/* Loading overlay */}
        {!iframeLoaded && !iframeError && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>Attempting to load Elasticsearch Dashboard...</p>
            <small>This may fail due to Content Security Policy restrictions</small>
          </div>
        )}
      </div>

      {/* Quick stats preview showing your actual data */}
      <div className="quick-stats">
        <h3>Latest Sensor Readings (From Your Dashboard)</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-label">Avg Power</span>
            <span className="stat-value">691.237</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Avg Strain</span>
            <span className="stat-value">168.637</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Avg Temperature</span>
            <span className="stat-value">32.532°C</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Avg Vibration</span>
            <span className="stat-value">0.828</span>
          </div>
        </div>
        <div className="stats-grid">
          <div className="stat-item current">
            <span className="stat-label">Current Power</span>
            <span className="stat-value">0.7</span>
          </div>
          <div className="stat-item current">
            <span className="stat-label">Current Strain</span>
            <span className="stat-value">0.3</span>
          </div>
          <div className="stat-item current">
            <span className="stat-label">Current Temperature</span>
            <span className="stat-value">62.19°C</span>
          </div>
          <div className="stat-item current">
            <span className="stat-label">Current Vibration</span>
            <span className="stat-value">1.532</span>
          </div>
        </div>
        <div className="stats-footer">
          <p className="stats-note">
            For real-time updates and interactive features, 
            <button className="inline-link" onClick={openInNewTab}>
              open the full dashboard in a new tab
            </button>
          </p>
          <p className="stats-source">
            Data source: Elasticsearch Serverless | Last updated: Live
          </p>
        </div>
      </div>
    </div>
  );
};

export default ElasticsearchDashboard;