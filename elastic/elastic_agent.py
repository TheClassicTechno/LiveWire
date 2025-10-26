"""
Elastic Agent for LiveWire Infrastructure Monitoring
===================================================

Custom Elastic Agent that sends sensor data to Serverless instance
using Agent Builder framework for real-time infrastructure monitoring.

This targets: Best Use of the Elastic Agent Builder on a Serverless Instance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import requests
import base64
from datetime import datetime, timezone
from hardware.raspberry_pi_sensor import RaspberryPiSensor
from models.grid_risk_model import CCIPipeline, CCIPipelineConfig

class LiveWireElasticAgent:
    """Custom Elastic Agent for LiveWire infrastructure monitoring"""
    
    def __init__(self, cloud_id, api_key, agent_id="livewire-agent-001"):
        self.cloud_id = cloud_id
        self.api_key = api_key
        self.agent_id = agent_id
        
        # Parse endpoint from cloud ID
        self.endpoint = self.parse_cloud_id(cloud_id)
        
        # Setup headers
        self.headers = {
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize components
        self.sensors = {}
        self.cci_model = None
        self.setup_cci_model()
        
        print(f"🤖 LiveWire Elastic Agent initialized")
        print(f"🆔 Agent ID: {agent_id}")
        print(f"Endpoint: {self.endpoint}")
    
    def parse_cloud_id(self, cloud_id):
        """Parse Cloud ID to extract Elasticsearch endpoint"""
        try:
            # Handle direct URL format (Serverless often provides direct URLs)
            if cloud_id.startswith('https://'):
                return cloud_id.rstrip('/')
            
            # Handle traditional Cloud ID format
            if ':' in cloud_id:
                try:
                    encoded_part = cloud_id.split(':')[1]
                    decoded = base64.b64decode(encoded_part + '===').decode('utf-8')  # Add padding
                    parts = decoded.split('$')
                    domain = parts[0]
                    es_uuid = parts[1]
                    return f"https://{es_uuid}.{domain}"
                except:
                    pass
            
            # If all else fails, treat as direct endpoint
            if not cloud_id.startswith('http'):
                cloud_id = f"https://{cloud_id}"
            
            return cloud_id.rstrip('/')
        except Exception as e:
            print(f"❌ Cloud ID parsing failed: {e}")
            if not cloud_id.startswith('http'):
                return f"https://{cloud_id}"
            return cloud_id
    
    def setup_cci_model(self):
        """Setup CCI model for real-time predictions"""
        config = CCIPipelineConfig()
        config.short_win = 3
        config.mid_win = 12
        config.long_win = 60
        config.w_temperature = 0.35
        config.w_vibration = 0.40
        config.w_strain = 0.25
        
        self.cci_model = CCIPipeline(config)
        print("⚙️ CCI model configured for agent")
    
    def register_components(self, component_ids):
        """Register infrastructure components for monitoring"""
        for comp_id in component_ids:
            self.sensors[comp_id] = RaspberryPiSensor(comp_id)
        
        print(f"Registered {len(component_ids)} components: {component_ids}")
    
    def collect_sensor_data(self, component_id):
        """Collect sensor data from component"""
        if component_id not in self.sensors:
            return None
        
        sensor = self.sensors[component_id]
        data = sensor.read_sensors()
        
        # Create agent-formatted document
        document = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": {
                "type": "livewire-agent",
                "version": "1.0.0",
                "id": self.agent_id
            },
            "component_id": component_id,
            "sensor_data": {
                "temperature": data['temperature'],
                "vibration": data['vibration'],
                "strain": data['strain'],
                "power": data['power']
            },
            "event": {
                "kind": "metric",
                "category": ["infrastructure"],
                "type": ["sensor"],
                "dataset": "livewire.sensors"
            }
        }
        
        return document
    
    def predict_risk_level(self, component_id, historical_data):
        """Predict risk level using CCI model"""
        try:
            # Simple risk assessment based on current thresholds
            latest = historical_data[-1]['sensor_data']
            
            risk_score = 0
            if latest['temperature'] > 35: risk_score += 1
            if latest['vibration'] > 0.8: risk_score += 1
            if latest['strain'] > 300: risk_score += 1
            if latest['power'] > 1300: risk_score += 1
            
            if risk_score >= 3:
                risk_zone = "red"
                confidence = 0.85
            elif risk_score >= 2:
                risk_zone = "yellow"
                confidence = 0.70
            else:
                risk_zone = "green"
                confidence = 0.90
            
            return {
                "risk_zone": risk_zone,
                "confidence": confidence,
                "time_left_days": max(1, 30 - (risk_score * 5))  # Estimated days
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return {"risk_zone": "unknown", "confidence": 0.0}
    
    def send_metric_data(self, component_id, prediction=None):
        """Send metric data to Elastic Serverless using Agent Builder"""
        
        # Collect sensor reading
        doc = self.collect_sensor_data(component_id)
        if not doc:
            return False
        
        # Add prediction data if available
        if prediction:
            doc["prediction"] = prediction
        
        # Send to data stream
        data_stream = "metrics-livewire.sensors-default"
        
        try:
            response = requests.post(f"{self.endpoint}/{data_stream}/_doc",
                                   json=doc, headers=self.headers)
            
            if response.status_code == 201:
                risk = prediction.get('risk_zone', 'unknown') if prediction else 'unknown'
                conf = prediction.get('confidence', 0) if prediction else 0
                
                print(f"{component_id}: T={doc['sensor_data']['temperature']:.1f}°C, "
                      f"V={doc['sensor_data']['vibration']:.2f}g → {risk} ({conf:.1%})")
                return True
            else:
                print(f"❌ Metric send failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Metric send error: {e}")
            return False
    
    def send_alert(self, component_id, prediction, sensor_data):
        """Send alert to Elastic Serverless"""
        
        risk_zone = prediction['risk_zone']
        confidence = prediction['confidence']
        
        # Only send alerts for yellow/red zones with high confidence
        if risk_zone in ['yellow', 'red'] and confidence > 0.6:
            
            alert_level = "warning" if risk_zone == "yellow" else "critical"
            
            alert_doc = {
                "@timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": {
                    "type": "livewire-agent",
                    "version": "1.0.0",
                    "id": self.agent_id
                },
                "component_id": component_id,
                "alert_level": alert_level,
                "risk_zone": risk_zone,
                "confidence": confidence,
                "message": f"Infrastructure component {component_id} shows {risk_zone} risk level "
                          f"(confidence: {confidence:.1%}). "
                          f"Temperature: {sensor_data['temperature']:.1f}°C, "
                          f"Vibration: {sensor_data['vibration']:.2f}g, "
                          f"Strain: {sensor_data['strain']:.0f}µε",
                "acknowledged": False,
                "event": {
                    "kind": "alert",
                    "category": ["infrastructure"],
                    "type": ["alert"],
                    "severity": 3 if risk_zone == "yellow" else 1,
                    "dataset": "livewire.alerts"
                }
            }
            
            # Send to alerts data stream
            data_stream = "logs-livewire.alerts-default"
            
            try:
                response = requests.post(f"{self.endpoint}/{data_stream}/_doc",
                                       json=alert_doc, headers=self.headers)
                
                if response.status_code == 201:
                    print(f"🚨 {alert_level.upper()} ALERT: {component_id} → {risk_zone}")
                    return True
                else:
                    print(f"❌ Alert send failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Alert send error: {e}")
        
        return False
    
    def start_monitoring(self, component_ids, interval=5, duration=300):
        """Start monitoring infrastructure components"""
        print(f"Starting LiveWire Agent monitoring")
        print(f"Components: {component_ids}")
        print(f"Interval: {interval}s, Duration: {duration}s")
        print("Sending data to Elastic Serverless with Agent Builder")
        
        # Register components
        self.register_components(component_ids)
        
        # Store recent data for predictions
        recent_data = {comp_id: [] for comp_id in component_ids}
        
        end_time = time.time() + duration
        
        try:
            while time.time() < end_time:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n⏰ {timestamp} - Agent data collection cycle")
                
                for comp_id in component_ids:
                    # Collect sensor data
                    doc = self.collect_sensor_data(comp_id)
                    if doc:
                        # Store for prediction
                        recent_data[comp_id].append(doc)
                        
                        # Keep only recent readings
                        if len(recent_data[comp_id]) > 20:
                            recent_data[comp_id] = recent_data[comp_id][-20:]
                        
                        # Make prediction if we have enough data
                        prediction = None
                        if len(recent_data[comp_id]) >= 3:
                            prediction = self.predict_risk_level(comp_id, recent_data[comp_id])
                        
                        # Send metric data
                        self.send_metric_data(comp_id, prediction)
                        
                        # Send alert if needed
                        if prediction:
                            self.send_alert(comp_id, prediction, doc['sensor_data'])
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n🛑 Agent monitoring stopped by user")
        
        print(f"\nAgent monitoring session complete")
        print(f"Data streams used:")
        print(f"   Metrics: metrics-livewire.sensors-default")
        print(f"   🚨 Alerts: logs-livewire.alerts-default")


def main():
    """Run LiveWire Elastic Agent"""
    print("🤖 LiveWire Elastic Agent for Serverless")
    print("Infrastructure monitoring with Elastic Agent Builder")
    print("=" * 60)
    
    # Get credentials
    cloud_id = input("🆔 Enter your Cloud ID: ").strip()
    api_key = input("🔑 Enter your API Key: ").strip()
    
    if not cloud_id or not api_key:
        print("❌ Cloud ID and API Key are required")
        return
    
    # Initialize agent
    agent = LiveWireElasticAgent(cloud_id, api_key)
    
    # Infrastructure components to monitor
    components = [
        "CABLE_A1_MAIN",
        "CABLE_B2_BACKUP", 
        "CABLE_C3_CRITICAL"
    ]
    
    print(f"\nStarting infrastructure monitoring...")
    print("💡 This demonstrates Elastic Agent Builder on Serverless!")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Start monitoring
    agent.start_monitoring(components, interval=3, duration=120)


if __name__ == "__main__":
    main()