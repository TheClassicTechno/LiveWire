"""
LiveWire Real-time CCI Prediction with Elastic Integration
=========================================================

Integrates Raspberry Pi sensor data with the Grid Risk Model for real-time
cable condition monitoring and alerting.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests
import base64
import time
from models.grid_risk_model import CCIPipeline, CCIPipelineConfig

class LiveWireElasticPredictor:
    """Real-time CCI prediction using Elastic data and Grid Risk Model"""
    
    def __init__(self, cloud_id=None, api_key=None):
        # Load Elastic Serverless credentials if not provided
        if cloud_id and api_key:
            self.cloud_id = cloud_id
            self.api_key = api_key
        else:
            try:
                with open('elastic/credentials.json', 'r') as f:
                    creds = json.load(f)
                    self.cloud_id = creds['cloud_id']
                    self.api_key = creds['api_key']
            except:
                print("❌ No Elastic credentials found. Using localhost fallback.")
                self.cloud_id = None
                self.api_key = None
        
        # Setup Elastic connection
        if self.cloud_id and self.api_key:
            self.elastic_url = self.parse_cloud_id(self.cloud_id)
            self.headers = {
                'Authorization': f'ApiKey {self.api_key}',
                'Content-Type': 'application/json'
            }
            self.elastic_index = "metrics-livewire.sensors-default"
            self.alert_index = "logs-livewire.alerts-default"
        else:
            self.elastic_url = "http://localhost:9200"
            self.headers = {'Content-Type': 'application/json'}
            self.elastic_index = "livewire-sensors"
            self.alert_index = "livewire-alerts"
        
        # Initialize CCI model with optimized config for real-time data
        self.setup_cci_model()
        
        # Alert thresholds
        self.alert_thresholds = {
            'red': 0.8,    # High risk threshold
            'yellow': 0.5  # Medium risk threshold
        }
        
        print("🔥 LiveWire Elastic Predictor initialized")
    
    def parse_cloud_id(self, cloud_id):
        """Parse Cloud ID to extract Elasticsearch endpoint"""
        try:
            if cloud_id.startswith('https://'):
                return cloud_id.rstrip('/')
            
            if ':' in cloud_id:
                try:
                    encoded_part = cloud_id.split(':')[1]
                    decoded = base64.b64decode(encoded_part + '===').decode('utf-8')
                    parts = decoded.split('$')
                    domain = parts[0]
                    es_uuid = parts[1]
                    return f"https://{es_uuid}.{domain}"
                except:
                    pass
            
            if not cloud_id.startswith('http'):
                cloud_id = f"https://{cloud_id}"
            
            return cloud_id.rstrip('/')
        except Exception as e:
            if not cloud_id.startswith('http'):
                return f"https://{cloud_id}"
            return cloud_id
    
    def setup_cci_model(self):
        """Setup optimized Grid Risk Model for real-time prediction"""
        config = CCIPipelineConfig()
        
        # Optimized for real-time streaming data
        config.short_win = 3      # 3 recent readings
        config.mid_win = 12       # 12 readings (1 minute at 5s intervals)
        config.long_win = 60      # 60 readings (5 minutes)
        
        # Sensor weight optimization for cable monitoring
        config.w_temperature = 0.35  # Temperature critical for cables
        config.w_vibration = 0.40    # Vibration indicates structural issues
        config.w_strain = 0.25       # Strain shows mechanical stress
        
        # Sensitive thresholds for early warning
        config.yellow_q = 0.60
        config.red_q = 0.80
        
        self.cci_model = CCIPipeline(config)
        self.model_trained = False
        
        print("⚙️ CCI model configured for real-time monitoring")
    
    def create_alert_index(self):
        """Create Elastic index for storing alerts"""
        mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "component_id": {"type": "keyword"},
                    "alert_level": {"type": "keyword"},
                    "risk_zone": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "sensor_readings": {"type": "object"},
                    "message": {"type": "text"},
                    "acknowledged": {"type": "boolean"}
                }
            }
        }
        
        try:
            response = requests.put(f"{self.elastic_url}/{self.alert_index}", 
                                  json=mapping, headers={'Content-Type': 'application/json'})
            print(f"Alert index '{self.alert_index}' ready")
        except Exception as e:
            print(f"❌ Alert index creation failed: {e}")
    
    def fetch_recent_data(self, component_id, hours=1):
        """Fetch recent sensor data from Elastic"""
        
        # Query for recent data
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"component_id": component_id}},
                        {"range": {"timestamp": {"gte": f"now-{hours}h"}}}
                    ]
                }
            },
            "sort": [{"timestamp": {"order": "asc"}}],
            "size": 1000
        }
        
        try:
            response = requests.post(f"{self.elastic_url}/{self.elastic_index}/_search",
                                   json=query, headers=self.headers)
            
            if response.status_code == 200:
                hits = response.json()['hits']['hits']
                
                if len(hits) == 0:
                    print(f"No recent data found for {component_id}")
                    return None
                
                # Convert to DataFrame
                data = []
                for hit in hits:
                    source = hit['_source']
                    data.append({
                        'component_id': source['component_id'],
                        'timestamp': pd.to_datetime(source['timestamp']),
                        'temperature': source['temperature'],
                        'vibration': source['vibration'],
                        'strain': source['strain'],
                        'power': source.get('power', 1000.0),
                        'energy': source.get('power', 1000.0) / 1000.0,  # Convert to energy units
                        'processing_speed': 50.0 - abs(source['temperature'] - 25.0),  # Derived feature
                        'age_years': 25  # Assume 25-year-old infrastructure
                    })
                
                df = pd.DataFrame(data)
                print(f"Fetched {len(df)} recent readings for {component_id}")
                return df
                
            else:
                print(f"❌ Elastic query failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Data fetch error: {e}")
            return None
    
    def predict_cable_condition(self, component_id):
        """Predict cable condition using recent sensor data"""
        
        # Fetch recent data
        df = self.fetch_recent_data(component_id, hours=2)
        if df is None or len(df) < 5:
            print(f"Insufficient data for prediction")
            return None
        
        # Add required cable_state column for model compatibility
        # Use simple heuristic based on sensor readings
        def estimate_cable_state(row):
            risk_score = 0
            if row['temperature'] > 35: risk_score += 1
            if row['vibration'] > 0.8: risk_score += 1
            if row['strain'] > 300: risk_score += 1
            
            if risk_score >= 2:
                return 'Warning'
            elif risk_score >= 1:
                return 'Degradation'
            else:
                return 'Normal'
        
        df['cable_state'] = df.apply(estimate_cable_state, axis=1)
        
        try:
            # Train model if not already trained
            if not self.model_trained:
                print("Training CCI model on recent data...")
                self.cci_model.fit(df)
                self.model_trained = True
            
            # Make prediction on latest data
            latest_data = df.tail(min(len(df), 20))  # Use last 20 readings
            predictions = self.cci_model.score(latest_data)
            
            if len(predictions) > 0:
                latest_prediction = predictions.iloc[-1]
                
                result = {
                    'component_id': component_id,
                    'timestamp': datetime.now(),
                    'risk_zone': latest_prediction['zone'],
                    'time_left_days': latest_prediction.get('time_left_days', 0),
                    'confidence': latest_prediction.get('confidence', 0.5),
                    'sensor_data': df.iloc[-1].to_dict()
                }
                
                print(f"Prediction: {result['risk_zone']} zone "
                      f"(confidence: {result['confidence']:.2f})")
                
                return result
            else:
                print("❌ No predictions generated")
                return None
                
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return None
    
    def send_alert(self, prediction):
        """Send alert to Elastic if risk threshold exceeded"""
        
        risk_zone = prediction['risk_zone']
        confidence = prediction['confidence']
        component_id = prediction['component_id']
        
        # Determine alert level
        alert_level = "info"
        if risk_zone == "red" and confidence > self.alert_thresholds['red']:
            alert_level = "critical"
        elif risk_zone in ["red", "yellow"] and confidence > self.alert_thresholds['yellow']:
            alert_level = "warning"
        
        if alert_level in ["critical", "warning"]:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "component_id": component_id,
                "alert_level": alert_level,
                "risk_zone": risk_zone,
                "confidence": confidence,
                "sensor_readings": prediction['sensor_data'],
                "message": f"Cable {component_id} shows {risk_zone} risk level "
                          f"(confidence: {confidence:.1%})",
                "acknowledged": False
            }
            
            try:
                response = requests.post(f"{self.elastic_url}/{self.alert_index}/_doc",
                                       json=alert, headers=self.headers)
                
                if response.status_code == 201:
                    print(f"🚨 {alert_level.upper()} ALERT sent for {component_id}")
                    return True
                    
            except Exception as e:
                print(f"❌ Alert send failed: {e}")
        
        return False
    
    def start_realtime_monitoring(self, component_ids, interval=10):
        """Start real-time monitoring loop"""
        print(f"🔄 Starting real-time monitoring for {len(component_ids)} components")
        print(f"⏱️ Check interval: {interval} seconds")
        
        # Create alert index
        self.create_alert_index()
        
        try:
            while True:
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Checking components...")
                
                for component_id in component_ids:
                    print(f"\n🔍 Analyzing {component_id}:")
                    
                    # Get prediction
                    prediction = self.predict_cable_condition(component_id)
                    
                    if prediction:
                        # Send alert if needed
                        self.send_alert(prediction)
                        
                        # Display status
                        zone = prediction['risk_zone']
                        conf = prediction['confidence']
                        
                        if zone == "red":
                            status_icon = "[RED]"
                        elif zone == "yellow":
                            status_icon = "[YELLOW]"
                        else:
                            status_icon = "[GREEN]"
                        
                        print(f"   {status_icon} Status: {zone} (confidence: {conf:.1%})")
                
                print(f"\nSleeping {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")


def main():
    """Demo real-time prediction with Elastic"""
    print("🔥 LiveWire Real-time CCI Prediction Demo")
    print("=" * 50)
    
    # Initialize predictor
    predictor = LiveWireElasticPredictor()
    
    # Components to monitor
    components = ["CABLE_DEMO_001"]
    
    print(f"\nMonitoring components: {components}")
    print("💡 Make sure Raspberry Pi sensor is sending data to Elastic!")
    print("🚨 Press Ctrl+C to stop monitoring\n")
    
    # Start monitoring
    predictor.start_realtime_monitoring(components, interval=15)


if __name__ == "__main__":
    main()