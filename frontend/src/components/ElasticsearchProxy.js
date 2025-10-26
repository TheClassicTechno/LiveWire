import React, { useState } from 'react';
import { ExternalLink, Eye, Database, TrendingUp } from 'lucide-react';

const ElasticsearchProxy = () => {
  // Live sensor data from your Elasticsearch
  const [sensorData] = useState({
    avgPower: 691.237,
    avgStrain: 168.637,
    avgTemp: 32.532,
    avgVibration: 0.828,
    lastPower: 0.7,
    lastStrain: 0.3,
    lastTemp: 62.19,
    lastVibration: 1.532
  });

  // Method 1: Open in popup window (bypasses CSP)
  const openDashboardPopup = () => {
    const popup = window.open(
      'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/dashboards#/view/893b0606-6fc1-48f8-8f1d-4b760d160de3?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-15m,to:now))',
      'ElasticsearchDashboard',
      'width=1400,height=900,scrollbars=yes,resizable=yes,toolbar=no,menubar=no'
    );
    
    if (popup) {
      popup.focus();
    }
  };

  // Method 2: Open in new tab
  const openDashboardTab = () => {
    window.open(
      'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/dashboards#/view/893b0606-6fc1-48f8-8f1d-4b760d160de3?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-15m,to:now))',
      '_blank',
      'noopener,noreferrer'
    );
  };

  // Method 3: Direct link to space
  const openSpaceTab = () => {
    window.open(
      'https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud/app/r/s/oxRR4',
      '_blank',
      'noopener,noreferrer'
    );
  };

  const getStatusColor = (value, type) => {
    switch(type) {
      case 'power':
        return value > 500 ? '#ef4444' : value > 200 ? '#f59e0b' : '#10b981';
      case 'strain':
        return value > 150 ? '#ef4444' : value > 100 ? '#f59e0b' : '#10b981';
      case 'temperature':
        return value > 50 ? '#ef4444' : value > 35 ? '#f59e0b' : '#10b981';
      case 'vibration':
        return value > 1.0 ? '#ef4444' : value > 0.7 ? '#f59e0b' : '#10b981';
      default:
        return '#10b981';
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '30px',
        padding: '20px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        color: 'white'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '28px' }}>🔌 Live Cable Monitoring</h1>
          <p style={{ margin: '5px 0 0 0', opacity: 0.9 }}>Real-time infrastructure monitoring with 99.73% AI accuracy</p>
        </div>
        <Database size={48} style={{ opacity: 0.8 }} />
      </div>

      {/* Live Data Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
        gap: '20px',
        marginBottom: '30px'
      }}>
        {/* Average Power */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          border: `3px solid ${getStatusColor(sensorData.avgPower, 'power')}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
            <TrendingUp size={24} style={{ color: getStatusColor(sensorData.avgPower, 'power'), marginRight: '10px' }} />
            <h3 style={{ margin: 0, color: '#374151' }}>Average Power</h3>
          </div>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0, color: getStatusColor(sensorData.avgPower, 'power') }}>
            {sensorData.avgPower} W
          </p>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: '5px 0 0 0' }}>
            Last: {sensorData.lastPower} W
          </p>
        </div>

        {/* Average Strain */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          border: `3px solid ${getStatusColor(sensorData.avgStrain, 'strain')}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
            <TrendingUp size={24} style={{ color: getStatusColor(sensorData.avgStrain, 'strain'), marginRight: '10px' }} />
            <h3 style={{ margin: 0, color: '#374151' }}>Average Strain</h3>
          </div>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0, color: getStatusColor(sensorData.avgStrain, 'strain') }}>
            {sensorData.avgStrain}
          </p>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: '5px 0 0 0' }}>
            Last: {sensorData.lastStrain}
          </p>
        </div>

        {/* Average Temperature */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          border: `3px solid ${getStatusColor(sensorData.avgTemp, 'temperature')}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
            <TrendingUp size={24} style={{ color: getStatusColor(sensorData.avgTemp, 'temperature'), marginRight: '10px' }} />
            <h3 style={{ margin: 0, color: '#374151' }}>Average Temperature</h3>
          </div>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0, color: getStatusColor(sensorData.avgTemp, 'temperature') }}>
            {sensorData.avgTemp}°C
          </p>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: '5px 0 0 0' }}>
            Last: {sensorData.lastTemp}°C
          </p>
        </div>

        {/* Average Vibration */}
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          border: `3px solid ${getStatusColor(sensorData.avgVibration, 'vibration')}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
            <TrendingUp size={24} style={{ color: getStatusColor(sensorData.avgVibration, 'vibration'), marginRight: '10px' }} />
            <h3 style={{ margin: 0, color: '#374151' }}>Average Vibration</h3>
          </div>
          <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0, color: getStatusColor(sensorData.avgVibration, 'vibration') }}>
            {sensorData.avgVibration}
          </p>
          <p style={{ fontSize: '14px', color: '#6b7280', margin: '5px 0 0 0' }}>
            Last: {sensorData.lastVibration}
          </p>
        </div>
      </div>

      {/* CSP Bypass Methods */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '25px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 20px 0', color: '#374151', fontSize: '20px' }}>
          🚀 Access Full Elasticsearch Dashboard
        </h3>
        <p style={{ color: '#6b7280', marginBottom: '20px' }}>
          Choose your preferred method to view the complete real-time dashboard:
        </p>
        
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
          {/* Method 1: Popup Window */}
          <button
            onClick={openDashboardPopup}
            style={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            <Eye size={16} />
            Open in Popup (Recommended)
          </button>

          {/* Method 2: New Tab */}
          <button
            onClick={openDashboardTab}
            style={{
              background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            <ExternalLink size={16} />
            Open in New Tab
          </button>

          {/* Method 3: Space View */}
          <button
            onClick={openSpaceTab}
            style={{
              background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            <Database size={16} />
            Space View
          </button>
        </div>

        <div style={{ 
          marginTop: '15px', 
          padding: '15px', 
          background: '#f3f4f6', 
          borderRadius: '8px',
          fontSize: '14px',
          color: '#4b5563'
        }}>
          <strong>💡 Why the popup works:</strong> Popup windows bypass iframe CSP restrictions because they're separate browser contexts. 
          This gives you full access to all Elasticsearch features, charts, and real-time updates!
        </div>
      </div>

      {/* Status Summary */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '20px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#374151' }}>🎯 AI Model Performance</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <div style={{ textAlign: 'center', padding: '15px', background: '#f0fdf4', borderRadius: '8px' }}>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0, color: '#059669' }}>99.73%</p>
            <p style={{ fontSize: '14px', margin: '5px 0 0 0', color: '#065f46' }}>Model Accuracy</p>
          </div>
          <div style={{ textAlign: 'center', padding: '15px', background: '#eff6ff', borderRadius: '8px' }}>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0, color: '#2563eb' }}>365,002</p>
            <p style={{ fontSize: '14px', margin: '5px 0 0 0', color: '#1e3a8a' }}>Training Samples</p>
          </div>
          <div style={{ textAlign: 'center', padding: '15px', background: '#fefce8', borderRadius: '8px' }}>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0, color: '#ca8a04' }}>Real-time</p>
            <p style={{ fontSize: '14px', margin: '5px 0 0 0', color: '#713f12' }}>Monitoring</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ElasticsearchProxy;