"""
Enhanced Data Generator for LiveWire Dashboard Demo
=================================================

Generates realistic sensor data with different risk scenarios
to populate your Kibana dashboard with interesting visualizations.
"""

import time
import random
import json
from datetime import datetime
from hardware.raspberry_pi_sensor import RaspberryPiSensor

class LiveWireDemoDataGenerator:
    """Generate diverse sensor data for dashboard demonstration"""
    
    def __init__(self):
        # Create multiple demo components
        self.components = {
            "CABLE_A1_MAIN": {
                "normal_temp": 25.0,
                "normal_vibration": 0.2,
                "normal_strain": 100,
                "normal_power": 1000,
                "risk_tendency": "stable"  # stable, warning, critical
            },
            "CABLE_B2_BACKUP": {
                "normal_temp": 22.0,
                "normal_vibration": 0.15,
                "normal_strain": 80,
                "normal_power": 800,
                "risk_tendency": "stable"
            },
            "TRANSFORMER_T1": {
                "normal_temp": 30.0,
                "normal_vibration": 0.1,
                "normal_strain": 150,
                "normal_power": 1200,
                "risk_tendency": "warning"  # This one will show some issues
            },
            "SWITCH_S3_CRITICAL": {
                "normal_temp": 35.0,
                "normal_vibration": 0.3,
                "normal_strain": 200,
                "normal_power": 1100,
                "risk_tendency": "critical"  # This one will show problems
            }
        }
        
        # Initialize sensors for each component
        self.sensors = {}
        for comp_id in self.components:
            self.sensors[comp_id] = RaspberryPiSensor(comp_id)
            print(f"📡 Initialized sensor for {comp_id}")
    
    def generate_reading(self, component_id, config, iteration):
        """Generate a single sensor reading with realistic variations"""
        
        # Base values
        base_temp = config["normal_temp"]
        base_vibration = config["normal_vibration"]
        base_strain = config["normal_strain"]
        base_power = config["normal_power"]
        
        # Add time-based patterns and random variations
        time_factor = iteration / 10.0  # Gradual changes over time
        
        # Temperature variations
        if config["risk_tendency"] == "critical":
            # Critical component gets hotter over time
            temperature = base_temp + (time_factor * 2) + random.uniform(-2, 5)
        elif config["risk_tendency"] == "warning":
            # Warning component has occasional spikes
            spike = 8 if random.random() < 0.3 else 0
            temperature = base_temp + spike + random.uniform(-3, 3)
        else:
            # Stable component stays normal
            temperature = base_temp + random.uniform(-3, 3)
        
        # Vibration variations
        if config["risk_tendency"] == "critical":
            vibration = base_vibration + (time_factor * 0.1) + random.uniform(-0.05, 0.15)
        elif config["risk_tendency"] == "warning":
            vibration = base_vibration + random.uniform(-0.1, 0.2)
        else:
            vibration = base_vibration + random.uniform(-0.05, 0.05)
        
        # Strain variations
        if config["risk_tendency"] == "critical":
            strain = base_strain + (time_factor * 20) + random.uniform(-20, 50)
        else:
            strain = base_strain + random.uniform(-30, 30)
        
        # Power variations (inversely related to problems)
        if config["risk_tendency"] == "critical":
            power = base_power - (time_factor * 50) + random.uniform(-100, 50)
        else:
            power = base_power + random.uniform(-100, 100)
        
        return {
            "temperature": max(15, min(50, temperature)),  # Clamp to realistic range
            "vibration": max(0, min(2.0, vibration)),
            "strain": max(0, min(500, strain)),
            "power": max(500, min(1500, power))
        }
    
    def assess_risk(self, sensor_data):
        """Assess risk level based on sensor readings"""
        risk_score = 0
        
        # Temperature risk
        if sensor_data["temperature"] > 40:
            risk_score += 2
        elif sensor_data["temperature"] > 35:
            risk_score += 1
        
        # Vibration risk
        if sensor_data["vibration"] > 0.8:
            risk_score += 2
        elif sensor_data["vibration"] > 0.5:
            risk_score += 1
        
        # Strain risk
        if sensor_data["strain"] > 300:
            risk_score += 2
        elif sensor_data["strain"] > 200:
            risk_score += 1
        
        # Power risk (low power can indicate problems)
        if sensor_data["power"] < 700:
            risk_score += 1
        
        # Determine risk zone
        if risk_score >= 4:
            return "red", 0.90
        elif risk_score >= 2:
            return "yellow", 0.75
        else:
            return "green", 0.85
    
    def generate_historical_data(self, hours_back=2, interval_minutes=1):
        """Generate historical data for the past few hours"""
        print(f"📊 Generating {hours_back} hours of historical data...")
        
        total_readings = hours_back * 60 // interval_minutes
        
        for i in range(total_readings):
            for comp_id, config in self.components.items():
                # Generate sensor reading
                sensor_data = self.generate_reading(comp_id, config, i)
                risk_zone, confidence = self.assess_risk(sensor_data)
                
                # Send to Elasticsearch
                sensor = self.sensors[comp_id]
                success = sensor.send_to_elastic(sensor_data, risk_zone, confidence)
                
                if success and i % 10 == 0:  # Print progress every 10 readings
                    print(f"   ✅ {comp_id}: {risk_zone} zone, T={sensor_data['temperature']:.1f}°C")
            
            # Small delay to avoid overwhelming Elasticsearch
            time.sleep(0.1)
        
        print(f"✅ Historical data generation complete!")
    
    def generate_live_stream(self, duration_minutes=5, interval_seconds=5):
        """Generate live streaming data"""
        print(f"🔄 Starting live data stream for {duration_minutes} minutes...")
        
        total_iterations = duration_minutes * 60 // interval_seconds
        
        for i in range(total_iterations):
            print(f"\n📡 Reading {i+1}/{total_iterations} at {datetime.now().strftime('%H:%M:%S')}")
            
            for comp_id, config in self.components.items():
                # Generate sensor reading
                sensor_data = self.generate_reading(comp_id, config, i)
                risk_zone, confidence = self.assess_risk(sensor_data)
                
                # Send to Elasticsearch
                sensor = self.sensors[comp_id]
                success = sensor.send_to_elastic(sensor_data, risk_zone, confidence)
                
                if success:
                    status_emoji = "🔴" if risk_zone == "red" else "🟡" if risk_zone == "yellow" else "🟢"
                    print(f"   {status_emoji} {comp_id}: {risk_zone} - T={sensor_data['temperature']:.1f}°C, V={sensor_data['vibration']:.3f}g")
            
            time.sleep(interval_seconds)
        
        print(f"\n✅ Live stream completed!")

def main():
    """Main demo data generation"""
    print("🎨 LiveWire Dashboard Demo Data Generator")
    print("=" * 50)
    print("This will generate realistic sensor data for your Kibana dashboard")
    print()
    
    generator = LiveWireDemoDataGenerator()
    
    print("\nChoose data generation mode:")
    print("1. Historical data (2 hours of past data)")
    print("2. Live stream (5 minutes of real-time data)")
    print("3. Both (historical + live stream)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        generator.generate_historical_data(hours_back=2, interval_minutes=2)
    
    if choice in ['2', '3']:
        input("\nPress Enter to start live streaming...")
        generator.generate_live_stream(duration_minutes=5, interval_seconds=5)
    
    print("\n🎉 Data generation complete!")
    print("📊 Your Kibana dashboard should now have rich data to visualize!")
    print("🔗 Go to Kibana and create the visualizations from the guide")

if __name__ == "__main__":
    main()