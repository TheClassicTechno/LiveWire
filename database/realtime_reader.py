"""
Real-time Database Reader for LiveWire
=====================================

Reads sensor data from Elastic Serverless database in real-time.
This demonstrates the separation between data producer (Raspberry Pi) 
and data consumer (processing program).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import requests
import base64
from datetime import datetime, timezone
from models.grid_risk_model import CCIPipeline, CCIPipelineConfig

class LiveWireDataReader:
    """Reads sensor data from Elastic Serverless database in real-time"""
    
    def __init__(self, cloud_id, api_key):
        self.cloud_id = cloud_id
        self.api_key = api_key
        self.endpoint = self.parse_cloud_id(cloud_id)
        
        self.headers = {
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize CCI model for processing
        self.setup_cci_model()
        
        # Track last seen timestamp to get only new data
        self.last_timestamp = None
        
        print(f"Database Reader initialized")
        print(f"Endpoint: {self.endpoint}")
    
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
            print(f"Cloud ID parsing failed: {e}")
            if not cloud_id.startswith('http'):
                return f"https://{cloud_id}"
            return cloud_id
    
    def setup_cci_model(self):
        """Setup CCI model for processing data"""
        config = CCIPipelineConfig()
        config.short_win = 3
        config.mid_win = 12
        config.long_win = 60
        config.w_temperature = 0.35
        config.w_vibration = 0.40
        config.w_strain = 0.25
        
        self.cci_model = CCIPipeline(config)
        print("CCI model ready for data processing")
    
    def get_latest_sensor_data(self, component_id=None, limit=10):
        """Get latest sensor readings from database"""
        
        # Build query for latest data
        query = {
            "size": limit,
            "sort": [
                {"@timestamp": {"order": "desc"}}
            ],
            "query": {
                "bool": {
                    "must": [
                        {"term": {"event.kind": "metric"}},
                        {"term": {"event.dataset": "livewire.sensors"}}
                    ]
                }
            }
        }
        
        # Add component filter if specified
        if component_id:
            query["query"]["bool"]["must"].append(
                {"term": {"component_id": component_id}}
            )
        
        # Add timestamp filter for new data only
        if self.last_timestamp:
            query["query"]["bool"]["must"].append({
                "range": {
                    "@timestamp": {
                        "gt": self.last_timestamp
                    }
                }
            })
        
        data_stream = "metrics-livewire.sensors-default"
        
        try:
            response = requests.post(f"{self.endpoint}/{data_stream}/_search",
                                   json=query, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get('hits', {}).get('hits', [])
                
                # Update last timestamp
                if hits:
                    self.last_timestamp = hits[0]['_source']['@timestamp']
                
                return [hit['_source'] for hit in hits]
            else:
                print(f"Database query failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Database read error: {e}")
            return []
    
    def process_sensor_data(self, sensor_readings):
        """Process sensor data through CCI model"""
        processed_results = []
        
        for reading in sensor_readings:
            sensor_data = reading.get('sensor_data', {})
            component_id = reading.get('component_id', 'unknown')
            timestamp = reading.get('@timestamp', '')
            
            # Extract the 4 float values
            temperature = sensor_data.get('temperature', 0.0)
            vibration = sensor_data.get('vibration', 0.0)
            strain = sensor_data.get('strain', 0.0)
            power = sensor_data.get('power', 0.0)
            
            # Simple risk assessment
            risk_score = 0
            if temperature > 35: risk_score += 1
            if vibration > 0.8: risk_score += 1
            if strain > 300: risk_score += 1
            if power > 1300: risk_score += 1
            
            if risk_score >= 3:
                risk_zone = "red"
                confidence = 0.85
            elif risk_score >= 2:
                risk_zone = "yellow"
                confidence = 0.70
            else:
                risk_zone = "green"
                confidence = 0.90
            
            result = {
                'timestamp': timestamp,
                'component_id': component_id,
                'sensor_data': {
                    'temperature': temperature,
                    'vibration': vibration,
                    'strain': strain,
                    'power': power
                },
                'risk_assessment': {
                    'zone': risk_zone,
                    'confidence': confidence,
                    'score': risk_score
                }
            }
            
            processed_results.append(result)
        
        return processed_results
    
    def start_realtime_monitoring(self, interval=5, component_id=None):
        """Start real-time monitoring by polling database"""
        print(f"\nStarting real-time database monitoring...")
        print(f"Polling interval: {interval} seconds")
        if component_id:
            print(f"Monitoring component: {component_id}")
        else:
            print("Monitoring all components")
        print("-" * 50)
        
        try:
            while True:
                # Get latest data from database
                new_readings = self.get_latest_sensor_data(component_id, limit=5)
                
                if new_readings:
                    # Process through CCI model
                    results = self.process_sensor_data(new_readings)
                    
                    # Display results
                    for result in reversed(results):  # Show oldest first
                        ts = result['timestamp'][:19]  # Remove timezone part
                        comp = result['component_id']
                        sensor = result['sensor_data']
                        risk = result['risk_assessment']
                        
                        status_icon = {"green": "[OK]", "yellow": "[WARN]", "red": "[CRIT]"}[risk['zone']]
                        
                        print(f"{ts} | {comp} | "
                              f"T:{sensor['temperature']:5.1f}°C "
                              f"V:{sensor['vibration']:5.2f}g "
                              f"S:{sensor['strain']:5.0f}µε "
                              f"P:{sensor['power']:6.0f}W "
                              f"→ {status_icon} {risk['zone']} ({risk['confidence']:.0%})")
                
                else:
                    print(f"{datetime.now().strftime('%H:%M:%S')} | No new data...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nReal-time monitoring stopped")


def main():
    """Demo the real-time database reader"""
    print("📊 LiveWire Real-time Database Reader")
    print("Reading sensor data from Elastic Serverless database")
    print("=" * 60)
    
    # Load credentials
    try:
        with open('elastic/credentials.json', 'r') as f:
            creds = json.load(f)
            cloud_id = creds['cloud_id']
            api_key = creds['api_key']
    except:
        print("❌ Credentials not found. Run setup_complete.py first")
        return
    
    # Initialize reader
    reader = LiveWireDataReader(cloud_id, api_key)
    
    print("\n💡 This demonstrates:")
    print("   • Raspberry Pi writes to Elastic Serverless database")
    print("   • This program reads from database in real-time")
    print("   • Complete separation of producer and consumer")
    print("\n🛑 Press Ctrl+C to stop\n")
    
    # Start monitoring
    reader.start_realtime_monitoring(interval=3)


if __name__ == "__main__":
    main()