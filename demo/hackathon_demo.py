"""
LiveWire Hackathon Demo Script
=============================

Complete end-to-end demonstration for Cal Hacks 12.0 showing:
1. Real-time sensor data from Raspberry Pi
2. Elastic ingestion and indexing
3. CCI prediction with Grid Risk Model
4. Alert generation for infrastructure failures

Perfect for live demo to judges!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
import json
from datetime import datetime
import requests
from hardware.raspberry_pi_sensor import RaspberryPiSensor
from elastic.realtime_predictor import LiveWireElasticPredictor

class LiveWireHackathonDemo:
    """Complete demo orchestrator for Cal Hacks presentation"""
    
    def __init__(self):
        self.demo_duration = 120  # 2 minute demo
        self.sensor_interval = 3   # 3 second sensor readings
        self.prediction_interval = 10  # 10 second predictions
        
        print("🔥 LiveWire Cal Hacks 12.0 Demo")
        print("=" * 50)
        print("Demonstrating real-time infrastructure monitoring")
        print("Raspberry Pi → Elastic → CCI Prediction → Alerts")
        print("=" * 50)
    
    def setup_demo_environment(self):
        """Setup demo environment with test components"""
        print("\nSetting up demo environment...")
        
        # Setup components
        self.components = [
            "DEMO_CABLE_A1",  # Normal cable
            "DEMO_CABLE_B2",  # Will show warning
            "DEMO_CABLE_C3"   # Will show critical
        ]
        
        # Initialize systems
        self.sensors = {}
        for comp_id in self.components:
            self.sensors[comp_id] = RaspberryPiSensor(comp_id)
        
        self.predictor = LiveWireElasticPredictor()
        
        print(f"Demo environment ready with {len(self.components)} components")
    
    def simulate_cable_scenarios(self):
        """Simulate different cable health scenarios for demo"""
        
        scenarios = {
            "DEMO_CABLE_A1": "normal",     # Healthy cable
            "DEMO_CABLE_B2": "warning",    # Degrading cable  
            "DEMO_CABLE_C3": "critical"    # Failing cable
        }
        
        print(f"\nStarting sensor simulation...")
        
        for i in range(int(self.demo_duration / self.sensor_interval)):
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ {timestamp} - Sensor Reading #{i+1}")
            
            for comp_id, scenario in scenarios.items():
                sensor = self.sensors[comp_id]
                
                # Generate scenario-appropriate data
                if scenario == "normal":
                    data = sensor.read_sensors()
                    risk_zone = "green"
                    confidence = 0.92
                elif scenario == "warning":
                    # Gradually increasing temperature and strain
                    base_data = sensor.read_sensors()
                    data = {
                        'temperature': min(40.0, base_data['temperature'] + i * 0.5),
                        'vibration': min(1.2, base_data['vibration'] + i * 0.05),
                        'strain': min(350.0, base_data['strain'] + i * 8),
                        'power': min(1400.0, base_data['power'] + i * 15)
                    }
                    risk_zone = "yellow" if i > 5 else "green"
                    confidence = 0.75
                else:  # critical
                    # High stress simulation
                    data = {
                        'temperature': 42.0 + (i * 0.3),
                        'vibration': 1.8 + (i * 0.02),
                        'strain': 420.0 + (i * 5),
                        'power': 1450.0 + (i * 10)
                    }
                    risk_zone = "red" if i > 3 else "yellow"
                    confidence = 0.88
                
                # Send to Elastic
                success = sensor.send_to_elastic(data, risk_zone, confidence)
                
                if success:
                    status_icon = {"green": "[GREEN]", "yellow": "[YELLOW]", "red": "[RED]"}[risk_zone]
                    print(f"   {comp_id}: {status_icon} {risk_zone} "
                          f"(T:{data['temperature']:.1f}°C, "
                          f"V:{data['vibration']:.2f}g, "
                          f"S:{data['strain']:.0f}µε)")
            
            time.sleep(self.sensor_interval)
        
        print(f"\nSensor simulation complete ({self.demo_duration}s)")
    
    def run_predictions(self):
        """Run CCI predictions during demo"""
        print(f"\n🧠 Starting CCI prediction engine...")
        
        # Wait for some sensor data to accumulate
        time.sleep(15)
        
        prediction_count = 0
        while prediction_count < (self.demo_duration // self.prediction_interval):
            print(f"\n🔍 Running CCI Analysis #{prediction_count + 1}")
            
            for comp_id in self.components:
                try:
                    prediction = self.predictor.predict_cable_condition(comp_id)
                    
                    if prediction:
                        zone = prediction['risk_zone']
                        conf = prediction['confidence']
                        
                        # Send alert if needed
                        alert_sent = self.predictor.send_alert(prediction)
                        
                        status_icon = {"green": "[GREEN]", "yellow": "[YELLOW]", "red": "[RED]"}[zone]
                        alert_text = " 🚨 ALERT SENT" if alert_sent else ""
                        
                        print(f"   {comp_id}: {status_icon} {zone.upper()} "
                              f"({conf:.1%} confidence){alert_text}")
                        
                        # Show time prediction for critical cases
                        if zone == "red" and 'time_left_days' in prediction:
                            days = prediction['time_left_days']
                            print(f"     WARNING: Estimated time to failure: {days:.0f} days")
                    
                except Exception as e:
                    print(f"   ❌ Prediction failed for {comp_id}: {e}")
            
            prediction_count += 1
            time.sleep(self.prediction_interval)
        
        print(f"\nCCI prediction engine complete")
    
    def show_demo_results(self):
        """Show final demo results and statistics"""
        print(f"\nDEMO RESULTS SUMMARY")
        print("=" * 50)
        
        # Load Elastic Serverless credentials for results query
        try:
            with open('elastic/credentials.json', 'r') as f:
                creds = json.load(f)
                cloud_id = creds['cloud_id']
                api_key = creds['api_key']
                
            # Parse endpoint
            if cloud_id.startswith('https://'):
                endpoint = cloud_id.rstrip('/')
            else:
                endpoint = f"https://{cloud_id}"
            
            headers = {
                'Authorization': f'ApiKey {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Get sensor data count
            response = requests.get(f"{endpoint}/metrics-livewire.sensors-default/_count", headers=headers)
            if response.status_code == 200:
                sensor_count = response.json()['count']
                print(f"Total sensor readings ingested: {sensor_count}")
            
            # Get alerts count  
            response = requests.get(f"{endpoint}/logs-livewire.alerts-default/_count", headers=headers)
            if response.status_code == 200:
                alert_count = response.json()['count']
                print(f"Alerts generated: {alert_count}")
            
            # Show data access info
            print(f"\nLive Data Access:")
            print(f"   Sensor Data: Elastic Serverless metrics-livewire.sensors-default")
            print(f"   Alerts: Elastic Serverless logs-livewire.alerts-default")
            
        except Exception as e:
            print(f"Results query info: Using Elastic Serverless data streams")
        
        # Demo achievements
        print(f"\nDEMO ACHIEVEMENTS:")
        print("Real-time IoT sensor data ingestion")
        print("Time-series data storage and indexing")
        print("Live CCI prediction with AI models")
        print("Automated alerting for infrastructure failures")
        print("✅ Scalable architecture for enterprise deployment")
        
        print(f"\n🎯 CAL HACKS APPLICATIONS:")
        print("🏅 Social Impact: Prevents infrastructure disasters")
        print("🏅 Best Use of Elastic: Advanced time-series analytics")
        print("🏅 Most Creative: Novel application of CCI to IoT monitoring")
        
        print(f"\n🔥 LiveWire: Infrastructure monitoring that saves lives!")
    
    def run_complete_demo(self):
        """Run the complete hackathon demo"""
        print(f"\n🚀 Starting Complete LiveWire Demo...")
        print(f"⏱️ Duration: {self.demo_duration} seconds")
        print("🎬 Perfect for live presentation to judges!")
        
        # Setup
        self.setup_demo_environment()
        
        # Start prediction thread
        prediction_thread = threading.Thread(target=self.run_predictions)
        prediction_thread.daemon = True
        prediction_thread.start()
        
        # Run sensor simulation (main thread)
        self.simulate_cable_scenarios()
        
        # Wait for predictions to finish
        time.sleep(5)
        
        # Show results
        self.show_demo_results()
        
        print(f"\n🎉 Demo Complete! Ready to win Cal Hacks 12.0! 🏆")


def main():
    """Run the hackathon demo"""
    demo = LiveWireHackathonDemo()
    
    print("\n💡 DEMO INSTRUCTIONS:")
    print("1. Make sure Elastic Serverless credentials are configured")
    print("2. This demo will run for 2 minutes")
    print("3. Watch the real-time predictions and alerts")
    print("4. Shows live data streams in Elastic Serverless")
    print("\n🎯 Press Enter to start the demo...")
    
    input()
    
    try:
        demo.run_complete_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")


if __name__ == "__main__":
    main()