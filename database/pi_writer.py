"""
Raspberry Pi Database Writer
===========================

Simulates Raspberry Pi sending sensor data to Elastic Serverless database.
This is the "producer" side - it only writes data, doesn't process it.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import requests
import base64
from datetime import datetime, timezone
import random

class RaspberryPiWriter:
    """Writes sensor data to Elastic Serverless database"""
    
    def __init__(self, cloud_id, api_key, component_id="CABLE_PI_001"):
        self.component_id = component_id
        self.cloud_id = cloud_id
        self.api_key = api_key
        self.endpoint = self.parse_cloud_id(cloud_id)
        
        self.headers = {
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Sensor baselines
        self.temp_baseline = 25.0
        self.vibration_baseline = 0.1
        self.strain_baseline = 100.0
        self.power_baseline = 1000.0
        
        print(f"Raspberry Pi Writer initialized: {component_id}")
        print(f"Database endpoint: {self.endpoint}")
    
    def parse_cloud_id(self, cloud_id):
        """Parse Cloud ID"""
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
        """Read sensor values (simulated)"""
        # Temperature: 15°C to 45°C
        temperature = self.temp_baseline + random.normalvariate(0, 5)
        temperature = max(15.0, min(45.0, temperature))
        
        # Vibration: 0.05g to 2.0g
        vibration = self.vibration_baseline + abs(random.normalvariate(0, 0.3))
        vibration = max(0.05, min(2.0, vibration))
        
        # Strain: 50µε to 500µε
        strain = self.strain_baseline + random.normalvariate(0, 50)
        strain = max(50.0, min(500.0, strain))
        
        # Power: 800W to 1500W
        power = self.power_baseline + random.normalvariate(0, 100)
        power = max(800.0, min(1500.0, power))
        
        return {
            'temperature': round(temperature, 2),
            'vibration': round(vibration, 3),
            'strain': round(strain, 1),
            'power': round(power, 1)
        }
    
    def write_to_database(self, sensor_data):
        """Write sensor data to Elastic Serverless database"""
        
        # Create database document
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
            "event": {
                "kind": "metric",
                "category": ["infrastructure"],
                "type": ["sensor"],
                "dataset": "livewire.sensors"
            }
        }
        
        # Send to database
        data_stream = "metrics-livewire.sensors-default"
        
        try:
            response = requests.post(f"{self.endpoint}/{data_stream}/_doc",
                                   json=document, headers=self.headers)
            
            if response.status_code == 201:
                print(f"[DB WRITE] T:{sensor_data['temperature']:5.1f}°C "
                      f"V:{sensor_data['vibration']:5.2f}g "
                      f"S:{sensor_data['strain']:5.0f}µε "
                      f"P:{sensor_data['power']:6.0f}W")
                return True
            else:
                print(f"Database write failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Database write error: {e}")
            return False
    
    def start_continuous_logging(self, interval=5, duration=300):
        """Start continuous sensor data logging"""
        print(f"\nStarting continuous sensor logging...")
        print(f"Interval: {interval} seconds")
        print(f"Duration: {duration} seconds")
        print("-" * 50)
        
        end_time = time.time() + duration
        
        try:
            while time.time() < end_time:
                # Read sensors
                sensor_data = self.read_sensors()
                
                # Write to database
                success = self.write_to_database(sensor_data)
                
                if not success:
                    print("⚠️ Write failed, but continuing...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nSensor logging stopped by user")
        
        print("Sensor logging session complete")


def main():
    """Run Raspberry Pi database writer"""
    print("🔌 Raspberry Pi Database Writer")
    print("Simulates Pi sending sensor data to database")
    print("=" * 50)
    
    # Load credentials
    try:
        with open('elastic/credentials.json', 'r') as f:
            creds = json.load(f)
            cloud_id = creds['cloud_id']
            api_key = creds['api_key']
    except:
        print("❌ Credentials not found. Run setup_complete.py first")
        return
    
    # Initialize Pi writer
    pi_writer = RaspberryPiWriter(cloud_id, api_key, "CABLE_PI_DEMO")
    
    print("\n💡 This simulates:")
    print("   • Raspberry Pi collecting sensor data")
    print("   • Writing data directly to Elastic Serverless database")
    print("   • Other programs can read this data in real-time")
    print("\n🛑 Press Ctrl+C to stop\n")
    
    # Start logging
    pi_writer.start_continuous_logging(interval=2, duration=120)


if __name__ == "__main__":
    main()