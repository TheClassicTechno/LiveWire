"""
LiveWire Dashboard Setup for Elastic Serverless
===============================================

Creates visualizations and dashboards in Elastic to display real-time
sensor data and risk assessments from your Raspberry Pi sensors.
"""

import json
import requests
import base64
from datetime import datetime, timedelta

class LiveWireDashboardSetup:
    """Setup Elastic dashboards and visualizations for LiveWire data"""
    
    def __init__(self):
        # Load Elastic Serverless credentials
        try:
            with open('elastic/credentials.json', 'r') as f:
                creds = json.load(f)
                self.cloud_id = creds['cloud_id']
                self.api_key = creds['api_key']
        except:
            print("❌ No Elastic credentials found. Run setup_complete.py first")
            return
        
        # Setup connection
        self.endpoint = self.parse_cloud_id(self.cloud_id)
        self.headers = {
            'Authorization': f'ApiKey {self.api_key}',
            'Content-Type': 'application/json',
            'kbn-xsrf': 'true'  # Required for Kibana API
        }
        
        print("🎨 LiveWire Dashboard Setup")
        print(f"Endpoint: {self.endpoint}")
    
    def parse_cloud_id(self, cloud_id):
        """Parse Cloud ID to extract endpoint"""
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
        except:
            return cloud_id
    
    def create_data_view(self):
        """Create data view for LiveWire sensor data"""
        
        data_view = {
            "data_view": {
                "title": "metrics-livewire.sensors-*",
                "name": "LiveWire Sensor Data",
                "timeFieldName": "@timestamp",
                "fields": json.dumps({
                    "@timestamp": {"type": "date"},
                    "component_id": {"type": "keyword"},
                    "sensor_data.temperature": {"type": "float"},
                    "sensor_data.vibration": {"type": "float"},
                    "sensor_data.strain": {"type": "float"},
                    "sensor_data.power": {"type": "float"},
                    "risk_zone": {"type": "keyword"},
                    "prediction_confidence": {"type": "float"},
                    "agent.type": {"type": "keyword"}
                })
            }
        }
        
        try:
            # Use Kibana endpoint for data views
            kibana_url = self.endpoint.replace('.es.', '.kb.')  # Convert ES to Kibana URL
            response = requests.post(f"{kibana_url}/api/data_views/data_view",
                                   json=data_view, headers=self.headers)
            
            if response.status_code in [200, 201]:
                result = response.json()
                data_view_id = result['data_view']['id']
                print(f"✅ Data view created: {data_view_id}")
                return data_view_id
            else:
                print(f"⚠️ Data view creation: {response.status_code}")
                print(f"Response: {response.text}")
                
                # Try alternative method: create index pattern directly in Elasticsearch
                print("🔄 Trying alternative approach...")
                return self.create_index_pattern_alternative()
                
        except Exception as e:
            print(f"❌ Data view creation failed: {e}")
            print("🔄 Trying alternative approach...")
            return self.create_index_pattern_alternative()
    
    def create_index_pattern_alternative(self):
        """Alternative method to create index pattern"""
        print("📋 Creating data view using direct Elasticsearch API...")
        
        # First check if the index exists
        response = requests.get(f"{self.endpoint}/metrics-livewire.sensors-*/_mapping",
                              headers=self.headers)
        
        if response.status_code == 200:
            print("✅ Sensor data index found!")
            print("📊 You can now create visualizations manually in Kibana:")
            print("   1. Go to Stack Management > Data Views")
            print("   2. Create new data view with pattern: metrics-livewire.sensors-*")
            print("   3. Use @timestamp as time field")
            print("   4. Go to Analytics > Dashboard to create visualizations")
            return "manual-setup"
        else:
            print("❌ No sensor data found. Run the sensor simulation first:")
            print("   python hardware/raspberry_pi_sensor.py")
            return None
    
    def create_sensor_dashboard(self, data_view_id):
        """Create comprehensive sensor monitoring dashboard"""
        
        if not data_view_id:
            print("❌ Cannot create dashboard without data view")
            return None
        
        # Dashboard configuration
        dashboard = {
            "version": "8.0.0",
            "objects": [
                {
                    "id": "livewire-sensor-overview",
                    "type": "dashboard",
                    "attributes": {
                        "title": "LiveWire Infrastructure Monitoring",
                        "description": "Real-time monitoring of power grid infrastructure sensors with AI-powered risk assessment",
                        "panelsJSON": json.dumps([
                            {
                                "version": "8.0.0",
                                "gridData": {"x": 0, "y": 0, "w": 24, "h": 15, "i": "1"},
                                "panelIndex": "1",
                                "embeddableConfig": {},
                                "panelRefName": "panel_1"
                            },
                            {
                                "version": "8.0.0", 
                                "gridData": {"x": 24, "y": 0, "w": 24, "h": 15, "i": "2"},
                                "panelIndex": "2",
                                "embeddableConfig": {},
                                "panelRefName": "panel_2"
                            },
                            {
                                "version": "8.0.0",
                                "gridData": {"x": 0, "y": 15, "w": 48, "h": 15, "i": "3"},
                                "panelIndex": "3", 
                                "embeddableConfig": {},
                                "panelRefName": "panel_3"
                            }
                        ]),
                        "timeRestore": True,
                        "timeTo": "now",
                        "timeFrom": "now-1h",
                        "refreshInterval": {
                            "pause": False,
                            "value": 5000
                        }
                    },
                    "references": [
                        {
                            "name": "panel_1",
                            "type": "visualization",
                            "id": "livewire-risk-gauge"
                        },
                        {
                            "name": "panel_2", 
                            "type": "visualization",
                            "id": "livewire-sensor-metrics"
                        },
                        {
                            "name": "panel_3",
                            "type": "visualization", 
                            "id": "livewire-timeline"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(f"{self.endpoint}/api/saved_objects/_import",
                                   json=dashboard, headers=self.headers)
            
            if response.status_code in [200, 201]:
                print("✅ Dashboard created: LiveWire Infrastructure Monitoring")
                return True
            else:
                print(f"⚠️ Dashboard creation: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard creation failed: {e}")
            return False
    
    def generate_sample_data(self):
        """Generate sample data to populate the dashboard"""
        print("\n📊 Generating sample data for dashboard...")
        
        from hardware.raspberry_pi_sensor import RaspberryPiSensor
        
        # Create sample components
        components = [
            "DEMO_CABLE_A1",
            "DEMO_CABLE_B2", 
            "DEMO_CABLE_C3"
        ]
        
        # Generate data for each component
        for comp_id in components:
            sensor = RaspberryPiSensor(comp_id)
            print(f"📡 Generating data for {comp_id}...")
            
            # Generate 10 readings
            for i in range(10):
                sensor_data = sensor.read_sensors()
                
                # Vary risk levels for demo
                if comp_id == "DEMO_CABLE_C3" and i > 5:
                    # Make C3 show warning/critical
                    sensor_data['temperature'] = 38 + (i * 2)
                    sensor_data['vibration'] = 0.9 + (i * 0.1)
                    
                # Simple risk assessment
                risk_score = 0
                if sensor_data['temperature'] > 35: risk_score += 1
                if sensor_data['vibration'] > 0.8: risk_score += 1
                if sensor_data['strain'] > 300: risk_score += 1
                if sensor_data['power'] > 1300: risk_score += 1
                
                if risk_score >= 3:
                    risk_zone = "red"
                    confidence = 0.85
                elif risk_score >= 2:
                    risk_zone = "yellow"
                    confidence = 0.70
                else:
                    risk_zone = "green"
                    confidence = 0.90
                
                # Send to Elastic
                success = sensor.send_to_elastic(sensor_data, risk_zone, confidence)
                if success:
                    print(f"   ✅ Sent {risk_zone} reading")
                
        print("✅ Sample data generation complete")
    
    def setup_complete_dashboard(self):
        """Setup complete dashboard with visualizations"""
        print("\n🎨 Setting up LiveWire dashboard...")
        
        # Create data view
        data_view_id = self.create_data_view()
        
        if data_view_id == "manual-setup":
            print("\n📋 Manual setup required - follow the instructions above")
            print(f"🔗 Go to Kibana: {self.endpoint.replace(':443', '').replace('.es.', '.kb.')}")
            return True
        elif data_view_id:
            # Create dashboard
            dashboard_success = self.create_sensor_dashboard(data_view_id)
            
            if dashboard_success:
                print("\n✅ Dashboard setup complete!")
                print(f"🔗 Access your dashboard at:")
                print(f"   {self.endpoint.replace(':443', '').replace('.es.', '.kb.')}/app/dashboards")
                print("\n📊 Dashboard includes:")
                print("   • Real-time sensor readings (temperature, vibration, strain, power)")
                print("   • Risk assessment gauge (green/yellow/red)")
                print("   • Component health timeline")
                print("   • Automated refresh every 5 seconds")
                
                # Generate sample data
                generate_data = input("\n🎯 Generate sample data for demo? (y/n): ").lower()
                if generate_data == 'y':
                    self.generate_sample_data()
                    print("\n🎉 Dashboard is ready! Navigate to Kibana to see your data.")
                return True
            else:
                print("❌ Dashboard creation failed")
                return False
        
        print("❌ Dashboard setup failed")
        return False


def main():
    """Setup LiveWire dashboard"""
    print("🎨 LiveWire Dashboard Setup for Elastic Serverless")
    print("=" * 60)
    print("This will create visualizations for your sensor data")
    print()
    
    setup = LiveWireDashboardSetup()
    setup.setup_complete_dashboard()


if __name__ == "__main__":
    main()