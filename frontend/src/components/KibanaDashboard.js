import React, { useState, useEffect } from 'react';
import { ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import './KibanaDashboard.css';

const KibanaDashboard = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Your Kibana dashboard URL with embedding parameters
  const dashboardUrl = "https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/dashboards#/view/893b0606-6fc1-48f8-8f1d-4b760d160de3?embed=true&_g=(filters:!(),refreshInterval:(pause:!f,value:10000),time:(from:now-15m,to:now))";

  const handleIframeLoad = () => {
    setIsLoading(false);
    setError(false);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError(true);
  };

  const refreshDashboard = () => {
    setIsLoading(true);
    setLastRefresh(new Date());
    // Force iframe refresh by updating src
    const iframe = document.getElementById('kibana-iframe');
    if (iframe) {
      iframe.src = iframe.src;
    }
  };

  const openInNewTab = () => {
    window.open(dashboardUrl.replace('embed=true&', ''), '_blank');
  };

  return (
    <div className="kibana-dashboard">
      <div className="kibana-header">
        <div className="kibana-title">
          <h2>Live Elastic Dashboard</h2>
          <p>Real-time sensor monitoring from Kibana</p>
        </div>
        
        <div className="kibana-controls">
          <button 
            className="kibana-refresh-btn" 
            onClick={refreshDashboard}
            disabled={isLoading}
          >
            <RefreshCw size={16} className={isLoading ? 'spinning' : ''} />
            Refresh
          </button>
          
          <button 
            className="kibana-external-btn" 
            onClick={openInNewTab}
            title="Open in new tab"
          >
            <ExternalLink size={16} />
            Full Screen
          </button>
        </div>
      </div>

      <div className="kibana-status">
        <div className="status-item">
          <span className="status-label">Last Update:</span>
          <span className="status-value">{lastRefresh.toLocaleTimeString()}</span>
        </div>
        <div className="status-item">
          <span className="status-label">Auto-refresh:</span>
          <span className="status-value">Every 10 seconds</span>
        </div>
      </div>

      <div className="kibana-container">
        {isLoading && (
          <div className="kibana-loading">
            <RefreshCw className="loading-spinner" size={24} />
            <p>Loading Kibana dashboard...</p>
          </div>
        )}

        {error && (
          <div className="kibana-error">
            <AlertCircle size={24} />
            <h3>Dashboard Unavailable</h3>
            <p>Unable to load Kibana dashboard. This could be due to:</p>
            <ul>
              <li>Authentication required (try opening in new tab)</li>
              <li>Network connectivity issues</li>
              <li>CORS restrictions</li>
            </ul>
            <button onClick={openInNewTab} className="kibana-fallback-btn">
              Open Dashboard in New Tab
            </button>
          </div>
        )}

        <iframe
          id="kibana-iframe"
          src={dashboardUrl}
          className={`kibana-iframe ${isLoading ? 'loading' : ''} ${error ? 'hidden' : ''}`}
          title="Kibana Dashboard"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
          loading="lazy"
        />
      </div>

      <div className="kibana-footer">
        <p>
          <strong>Note:</strong> If the dashboard doesn't load, click "Full Screen" to open in a new tab.
          Some security settings may prevent embedding.
        </p>
      </div>
    </div>
  );
};

export default KibanaDashboard;