"""
LiveWire Web Dashboard
=====================

Simple Flask web dashboard to visualize real-time sensor data
from Elastic Serverless. Shows live charts and risk assessments.
"""

import json
import requests
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import threading
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Register blueprints
from backend.elasticsearch_proxy import bp as elasticsearch_bp
from backend.rul_api import bp as rul_bp
from backend.rul_elasticsearch_integration import bp as rul_elasticsearch_bp
from backend.live_component_api import bp as live_component_bp

app.register_blueprint(elasticsearch_bp)
app.register_blueprint(rul_bp)
app.register_blueprint(rul_elasticsearch_bp)
app.register_blueprint(live_component_bp)

# Initialize RUL model
from backend.rul_api import load_rul_artifacts
load_rul_artifacts()

# Initialize RUL Elasticsearch manager
from backend.rul_elasticsearch_integration import rul_manager
try:
    rul_manager.connect()
    print("✅ RUL Elasticsearch integration ready")
except Exception as e:
    print(f"⚠️ RUL Elasticsearch connection failed: {e}")

class LiveWireDataFetcher:
    """Fetches data from Elastic Serverless for dashboard"""
    
    def __init__(self):
        # Load credentials
        try:
            with open('elastic/credentials.json', 'r') as f:
                creds = json.load(f)
                self.cloud_id = creds['cloud_id']
                self.api_key = creds['api_key']
        except:
            print("❌ No Elastic credentials found")
            self.cloud_id = None
            self.api_key = None
            return
        
        self.endpoint = self.parse_cloud_id(self.cloud_id)
        self.headers = {
            'Authorization': f'ApiKey {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        self.latest_data = {}
        print(f"📊 Data fetcher initialized: {self.endpoint}")
    
    def parse_cloud_id(self, cloud_id):
        """Parse Cloud ID"""
        try:
            if cloud_id.startswith('https://'):
                return cloud_id.rstrip('/')
            if not cloud_id.startswith('http'):
                cloud_id = f"https://{cloud_id}"
            return cloud_id.rstrip('/')
        except:
            return cloud_id
    
    def get_latest_data(self):
        """Get latest sensor data from Elastic"""
        if not self.cloud_id:
            return {"error": "No Elastic connection"}
        
        query = {
            "size": 20,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {"term": {"event.kind": "metric"}},
                        {"range": {"@timestamp": {"gte": "now-1h"}}}
                    ]
                }
            }
        }
        
        try:
            response = requests.post(f"{self.endpoint}/metrics-livewire.sensors-default/_search",
                                   json=query, headers=self.headers)
            
            if response.status_code == 200:
                hits = response.json().get('hits', {}).get('hits', [])
                
                # Process data by component
                components = {}
                for hit in hits:
                    source = hit['_source']
                    comp_id = source.get('component_id', 'unknown')
                    
                    if comp_id not in components:
                        components[comp_id] = []
                    
                    # Extract sensor data
                    sensor_data = source.get('sensor_data', {})
                    
                    components[comp_id].append({
                        'timestamp': source.get('@timestamp'),
                        'temperature': sensor_data.get('temperature', 0),
                        'vibration': sensor_data.get('vibration', 0),
                        'strain': sensor_data.get('strain', 0),
                        'power': sensor_data.get('power', 0),
                        'risk_zone': source.get('risk_zone', 'unknown'),
                        'confidence': source.get('prediction_confidence', 0)
                    })
                
                return components
            else:
                return {"error": f"Query failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}

# Global data fetcher
data_fetcher = LiveWireDataFetcher()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LiveWire Infrastructure Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
            .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .risk-green { border-left: 5px solid #4CAF50; }
            .risk-yellow { border-left: 5px solid #FF9800; }
            .risk-red { border-left: 5px solid #F44336; }
            .metric { display: inline-block; margin: 10px; text-align: center; }
            .metric-value { font-size: 24px; font-weight: bold; }
            .metric-label { font-size: 12px; color: #666; }
            .status { padding: 5px 10px; border-radius: 4px; color: white; font-weight: bold; }
            .status-green { background: #4CAF50; }
            .status-yellow { background: #FF9800; }
            .status-red { background: #F44336; }
            .refresh { text-align: center; margin: 20px; }
            .btn { padding: 10px 20px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔌 LiveWire Infrastructure Dashboard</h1>
            <p>Real-time monitoring of power grid components with AI risk assessment</p>
        </div>
        
        <div class="refresh">
            <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
            <span id="last-update"></span>
        </div>
        
        <div id="dashboard-content">
            <p>Loading sensor data...</p>
        </div>
        
        <script>
            function refreshData() {
                document.getElementById('last-update').textContent = 'Loading...';
                
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => {
                        updateDashboard(data);
                        document.getElementById('last-update').textContent = 
                            'Last updated: ' + new Date().toLocaleTimeString();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('dashboard-content').innerHTML = 
                            '<p style="color: red;">Error loading data: ' + error + '</p>';
                    });
            }
            
            function updateDashboard(data) {
                if (data.error) {
                    document.getElementById('dashboard-content').innerHTML = 
                        '<p style="color: red;">Error: ' + data.error + '</p>';
                    return;
                }
                
                let html = '<div class="grid">';
                
                for (const [componentId, readings] of Object.entries(data)) {
                    if (readings.length === 0) continue;
                    
                    const latest = readings[0];
                    const riskClass = 'risk-' + (latest.risk_zone || 'green');
                    const statusClass = 'status-' + (latest.risk_zone || 'green');
                    
                    html += `
                        <div class="card ${riskClass}">
                            <h3>${componentId}</h3>
                            <div class="status ${statusClass}">
                                ${(latest.risk_zone || 'unknown').toUpperCase()} 
                                (${Math.round((latest.confidence || 0) * 100)}% confidence)
                            </div>
                            
                            <div style="margin: 20px 0;">
                                <div class="metric">
                                    <div class="metric-value">${latest.temperature?.toFixed(1) || 'N/A'}°C</div>
                                    <div class="metric-label">Temperature</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${latest.vibration?.toFixed(2) || 'N/A'}g</div>
                                    <div class="metric-label">Vibration</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${latest.strain?.toFixed(0) || 'N/A'}µε</div>
                                    <div class="metric-label">Strain</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${latest.power?.toFixed(0) || 'N/A'}W</div>
                                    <div class="metric-label">Power</div>
                                </div>
                            </div>
                            
                            <canvas id="chart-${componentId}" width="400" height="200"></canvas>
                        </div>
                    `;
                }
                
                html += '</div>';
                document.getElementById('dashboard-content').innerHTML = html;
                
                // Create charts for each component
                for (const [componentId, readings] of Object.entries(data)) {
                    if (readings.length === 0) continue;
                    createChart(componentId, readings);
                }
            }
            
            function createChart(componentId, readings) {
                const ctx = document.getElementById('chart-' + componentId);
                if (!ctx) return;
                
                const labels = readings.reverse().map(r => 
                    new Date(r.timestamp).toLocaleTimeString()
                );
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Temperature (°C)',
                                data: readings.map(r => r.temperature),
                                borderColor: '#FF6384',
                                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                                tension: 0.3
                            },
                            {
                                label: 'Vibration (g)',
                                data: readings.map(r => r.vibration * 10), // Scale for visibility
                                borderColor: '#36A2EB',
                                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                                tension: 0.3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Sensor Trends'
                            }
                        }
                    }
                });
            }
            
            // Auto-refresh every 10 seconds
            refreshData();
            setInterval(refreshData, 10000);
        </script>
    </body>
    </html>
    """

@app.route('/api/data')
def api_data():
    """API endpoint for sensor data"""
    return jsonify(data_fetcher.get_latest_data())

if __name__ == '__main__':
    print("🌐 Starting LiveWire Web Dashboard")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔄 Auto-refreshes every 10 seconds")
    app.run(debug=True, host='0.0.0.0', port=5000)