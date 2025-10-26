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
from datetime import datetime, timezone
import numpy as np

class RaspberryPiSensor:
    """Simulates Raspberry Pi sensor readings for cable infrastructure monitoring"""
    
    def __init__(self, component_id="CABLE_001", elastic_url="http://localhost:9200"):
        self.component_id = component_id
        self.elastic_url = elastic_url
        self.elastic_index = "livewire-sensors"
        
        # Sensor calibration (realistic ranges for cable monitoring)
        self.temp_baseline = 25.0      # °C - normal operating temperature
        self.vibration_baseline = 0.1  # g-force - minimal vibration
        self.strain_baseline = 100.0   # µε - normal strain
        self.power_baseline = 1000.0   # W - normal power load
        
        print(f"Initialized sensor for component: {component_id}")
        print(f"Elastic endpoint: {elastic_url}")
    
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
                                  json=mapping, headers={'Content-Type': 'application/json'})
            if response.status_code in [200, 400]:  # 400 if index exists
                print(f"Elastic index '{self.elastic_index}' ready")
            else:
                print(f"Elastic index creation: {response.status_code}")
        except Exception as e:
            print(f"Elastic connection failed: {e}")
    
    def send_to_elastic(self, sensor_data, risk_zone="green", confidence=0.0):
        """Send sensor reading to Elastic with CCI prediction"""
        
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
                                   json=document, headers={'Content-Type': 'application/json'})
            
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
    
    def start_monitoring(self, interval=5.0, duration=60):
        """Start continuous sensor monitoring"""
        print(f"🔄 Starting {duration}s monitoring (interval: {interval}s)")
        
        # Create Elastic index
        self.create_elastic_mapping()
        
        end_time = time.time() + duration
        anomaly_trigger = random.uniform(20, 40)  # Random anomaly time
        
        while time.time() < end_time:
            # Decide if this should be an anomaly reading
            elapsed = time.time() - (end_time - duration)
            if elapsed > anomaly_trigger and elapsed < anomaly_trigger + 15:
                sensor_data = self.simulate_anomaly()
                risk_zone = "red"  # High risk during anomaly
                confidence = 0.85
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
                elif risk_score >= 2:
                    risk_zone = "yellow"
                    confidence = 0.60
                else:
                    risk_zone = "green"
                    confidence = 0.90
            
            # Send to Elastic
            self.send_to_elastic(sensor_data, risk_zone, confidence)
            
            time.sleep(interval)
        
        print("✅ Monitoring session completed")


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
    
    # Start monitoring
    print(f"\n🔄 Starting live monitoring...")
    sensor.start_monitoring(interval=3.0, duration=30)
    
    print(f"\n✅ Demo complete! Check Elastic at: http://localhost:9200/livewire-sensors/_search")


if __name__ == "__main__":
    main()