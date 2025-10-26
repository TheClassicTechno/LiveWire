"""
Raspberry Pi Sensor Data Collection for LiveWire CCI Monitoring
==============================================================

Simulates sensor readings from Raspberry Pi hardware:
- Temperature (°C): Infrastructure thermal stress
- Vibration (g-force): Structural oscillations  
- Strain (µε): Mechanical stress
- Power (W): Electrical load

Sends data to Elastic for real-time processing.
"""

import time
import random
import json
import requests
import base64
from datetime import datetime, timezone
import numpy as np

class RaspberryPiSensor:
    """Simulates Raspberry Pi sensor readings for cable infrastructure monitoring"""
    
    def __init__(self, component_id="CABLE_001", cloud_id=None, api_key=None):
        self.component_id = component_id
        
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
        else:
            self.elastic_url = "http://localhost:9200"
            self.headers = {'Content-Type': 'application/json'}
            self.elastic_index = "livewire-sensors"
        
        # Sensor calibration (realistic ranges for cable monitoring)
        self.temp_baseline = 25.0      # °C - normal operating temperature
        self.vibration_baseline = 0.1  # g-force - minimal vibration
        self.strain_baseline = 100.0   # µε - normal strain
        self.power_baseline = 1000.0   # W - normal power load
        
        print(f"Initialized sensor for component: {component_id}")
        print(f"Elastic endpoint: {self.elastic_url}")
    
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
    
    def read_sensors(self):
        """Read current sensor values with realistic cable monitoring ranges"""
        
        # Temperature: 15°C to 45°C (normal operation to thermal stress)
        temperature = self.temp_baseline + random.normalvariate(0, 5)
        temperature = max(15.0, min(45.0, temperature))
        
        # Vibration: 0.05g to 2.0g (minimal to high oscillation)
        vibration = self.vibration_baseline + abs(random.normalvariate(0, 0.3))
        vibration = max(0.05, min(2.0, vibration))
        
        # Strain: 50µε to 500µε (low to high mechanical stress)
        strain = self.strain_baseline + random.normalvariate(0, 50)
        strain = max(50.0, min(500.0, strain))
        
        # Power: 800W to 1500W (low load to high load)
        power = self.power_baseline + random.normalvariate(0, 100)
        power = max(800.0, min(1500.0, power))
        
        return {
            'temperature': round(temperature, 2),
            'vibration': round(vibration, 3),
            'strain': round(strain, 1),
            'power': round(power, 1)
        }
    
    def create_elastic_mapping(self):
        """Create Elastic index mapping for sensor data"""
        mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "component_id": {"type": "keyword"},
                    "temperature": {"type": "float"},
                    "vibration": {"type": "float"},
                    "strain": {"type": "float"},
                    "power": {"type": "float"},
                    "risk_zone": {"type": "keyword"},
                    "prediction_confidence": {"type": "float"}
                }
            }
        }
        
        try:
            response = requests.put(f"{self.elastic_url}/{self.elastic_index}", 
                                  json=mapping, headers=self.headers)
            if response.status_code in [200, 400]:  # 400 if index exists
                print(f"Elastic index '{self.elastic_index}' ready")
            else:
                print(f"Elastic index creation: {response.status_code}")
        except Exception as e:
            print(f"Elastic connection failed: {e}")
    
    def send_to_elastic(self, sensor_data, risk_zone="green", confidence=0.0):
        """Send sensor reading to Elastic with CCI prediction"""
        
        # Use Elastic Serverless format if connected to serverless
        if self.api_key:
            document = {
                "@timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": {
                    "type": "raspberry-pi",
                    "version": "1.0.0",
                    "id": "pi-sensor-001"
                },
                "component_id": self.component_id,
                "sensor_data": {
                    "temperature": sensor_data['temperature'],
                    "vibration": sensor_data['vibration'],
                    "strain": sensor_data['strain'],
                    "power": sensor_data['power']
                },
                "risk_zone": risk_zone,
                "prediction_confidence": confidence,
                "event": {
                    "kind": "metric",
                    "category": ["infrastructure"],
                    "type": ["sensor"],
                    "dataset": "livewire.sensors"
                }
            }
        else:
            # Local Elasticsearch format
            document = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component_id": self.component_id,
                "temperature": sensor_data['temperature'],
                "vibration": sensor_data['vibration'],
                "strain": sensor_data['strain'],
                "power": sensor_data['power'],
                "risk_zone": risk_zone,
                "prediction_confidence": confidence
            }
        
        try:
            response = requests.post(f"{self.elastic_url}/{self.elastic_index}/_doc",
                                   json=document, headers=self.headers)
            
            if response.status_code == 201:
                print(f"Data sent: T={sensor_data['temperature']}°C, "
                      f"V={sensor_data['vibration']}g, S={sensor_data['strain']}µε, "
                      f"P={sensor_data['power']}W → Zone: {risk_zone}")
                return True
            else:
                print(f"Elastic error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def simulate_anomaly(self):
        """Simulate cable stress condition for testing"""
        print("🚨 Simulating cable stress condition...")
        
        # Simulate high temperature, vibration, and strain
        return {
            'temperature': 42.0 + random.uniform(-2, 3),  # High heat
            'vibration': 1.5 + random.uniform(-0.2, 0.5), # High oscillation
            'strain': 400.0 + random.uniform(-50, 100),    # High stress
            'power': 1350.0 + random.uniform(-100, 150)    # High load
        }
    
    def start_monitoring(self, interval=1.0, duration=30):
        """Start real-time monitoring with immediate Elastic updates"""
        print(f"🔄 Starting {duration}s monitoring (interval: {interval}s)")
        print(f"📡 Each reading sent immediately to Elastic Serverless")
        
        # Create Elastic index
        self.create_elastic_mapping()
        
        reading_count = 0
        end_time = time.time() + duration
        anomaly_trigger = random.uniform(duration * 0.3, duration * 0.7)  # Random anomaly time
        
        while time.time() < end_time:
            reading_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Decide if this should be an anomaly reading
            elapsed = time.time() - (end_time - duration)
            if elapsed > anomaly_trigger and elapsed < anomaly_trigger + 10:
                sensor_data = self.simulate_anomaly()
                risk_zone = "red"  # High risk during anomaly
                confidence = 0.85
                status_emoji = "🔴"
            else:
                sensor_data = self.read_sensors()
                # Simple risk assessment based on thresholds
                risk_score = 0
                if sensor_data['temperature'] > 35: risk_score += 1
                if sensor_data['vibration'] > 0.8: risk_score += 1
                if sensor_data['strain'] > 300: risk_score += 1
                if sensor_data['power'] > 1300: risk_score += 1
                
                if risk_score >= 3:
                    risk_zone = "red"
                    confidence = 0.75
                    status_emoji = "🔴"
                elif risk_score >= 2:
                    risk_zone = "yellow"
                    confidence = 0.60
                    status_emoji = "🟡"
                else:
                    risk_zone = "green"
                    confidence = 0.90
                    status_emoji = "🟢"
            
            # Send to Elastic immediately (1 reading = 1 send)
            success = self.send_to_elastic(sensor_data, risk_zone, confidence)
            
            if success:
                print(f"#{reading_count:3d} [{current_time}] {status_emoji} {risk_zone.upper():6s} | "
                      f"T={sensor_data['temperature']:5.1f}°C V={sensor_data['vibration']:5.3f}g | ✅ Elastic")
            else:
                print(f"#{reading_count:3d} [{current_time}] ❌ FAILED to send to Elastic")
            
            time.sleep(interval)
        
        print(f"\n✅ Monitoring completed: {reading_count} readings sent individually")
        print(f"🎯 Dashboard shows all {reading_count} real-time updates!")


def main():
    """Demo the Raspberry Pi sensor integration"""
    print("🔌 LiveWire Raspberry Pi Sensor Demo")
    print("=" * 50)
    
    # Initialize sensor
    sensor = RaspberryPiSensor("CABLE_DEMO_001")
    
    # Test single reading
    print("\n📊 Single sensor reading:")
    data = sensor.read_sensors()
    print(f"Temperature: {data['temperature']}°C")
    print(f"Vibration: {data['vibration']}g")
    print(f"Strain: {data['strain']}µε")
    print(f"Power: {data['power']}W")
    
    # Start monitoring with faster updates for real-time dashboard
    print(f"\n🔄 Starting live monitoring...")
    print("Choose monitoring mode:")
    print("1. Fast demo (1-second intervals, 30 seconds)")
    print("2. Standard monitoring (3-second intervals, 60 seconds)")
    print("3. Extended monitoring (5-second intervals, 5 minutes)")
    
    choice = input("Enter choice (1-3, default=1): ").strip() or "1"
    
    if choice == "1":
        print("🚀 Fast demo mode - updating dashboard every second!")
        sensor.start_monitoring(interval=1.0, duration=30)
    elif choice == "2":
        print("📊 Standard monitoring mode")
        sensor.start_monitoring(interval=3.0, duration=60)
    else:
        print("⏱️ Extended monitoring mode")
        sensor.start_monitoring(interval=5.0, duration=300)
    
    print(f"\n🎉 Demo complete! Check your dashboards:")
    print(f"📊 Elastic Serverless: https://my-elasticsearch-project-c80e6e.kb.us-west1.gcp.elastic.cloud")
    print(f"🌐 Simple Dashboard: Open simple_dashboard.html in browser")


if __name__ == "__main__":
    main()