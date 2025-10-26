"""
Elastic Setup and Configuration for LiveWire
===========================================

Sets up Elastic for time-series sensor data ingestion and alerting.
Run this first to configure the Elastic environment.
"""

import requests
import json
from datetime import datetime

class ElasticSetup:
    """Setup Elastic for LiveWire sensor monitoring"""
    
    def __init__(self, elastic_url="http://localhost:9200"):
        self.elastic_url = elastic_url
        print(f"🔧 Setting up Elastic at: {elastic_url}")
    
    def check_elastic_health(self):
        """Check if Elastic is running and healthy"""
        try:
            response = requests.get(f"{self.elastic_url}/_cluster/health")
            if response.status_code == 200:
                health = response.json()
                status = health['status']
                print(f"✅ Elastic cluster status: {status}")
                return True
            else:
                print(f"❌ Elastic health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Elastic: {e}")
            print("💡 Make sure Elastic is running on localhost:9200")
            return False
    
    def create_sensor_index(self):
        """Create optimized index for sensor data"""
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "refresh_interval": "5s"
            },
            "mappings": {
                "properties": {
                    "timestamp": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "component_id": {
                        "type": "keyword",
                        "fields": {
                            "text": {"type": "text"}
                        }
                    },
                    "temperature": {
                        "type": "float",
                        "fields": {
                            "scaled": {
                                "type": "scaled_float",
                                "scaling_factor": 100
                            }
                        }
                    },
                    "vibration": {
                        "type": "float",
                        "fields": {
                            "scaled": {
                                "type": "scaled_float", 
                                "scaling_factor": 1000
                            }
                        }
                    },
                    "strain": {
                        "type": "float",
                        "fields": {
                            "scaled": {
                                "type": "scaled_float",
                                "scaling_factor": 10
                            }
                        }
                    },
                    "power": {
                        "type": "float",
                        "fields": {
                            "scaled": {
                                "type": "scaled_float",
                                "scaling_factor": 10
                            }
                        }
                    },
                    "risk_zone": {
                        "type": "keyword"
                    },
                    "prediction_confidence": {
                        "type": "float"
                    }
                }
            }
        }
        
        try:
            response = requests.put(f"{self.elastic_url}/livewire-sensors",
                                  json=mapping, headers={'Content-Type': 'application/json'})
            
            if response.status_code in [200, 400]:  # 400 if exists
                print("✅ Sensor data index created")
                return True
            else:
                print(f"❌ Index creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Index setup error: {e}")
            return False
    
    def create_alert_index(self):
        """Create index for storing alerts"""
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "component_id": {"type": "keyword"},
                    "alert_level": {
                        "type": "keyword",
                        "fields": {
                            "text": {"type": "text"}
                        }
                    },
                    "risk_zone": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "sensor_readings": {
                        "type": "object",
                        "enabled": True
                    },
                    "message": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "acknowledged": {"type": "boolean"}
                }
            }
        }
        
        try:
            response = requests.put(f"{self.elastic_url}/livewire-alerts",
                                  json=mapping, headers={'Content-Type': 'application/json'})
            
            if response.status_code in [200, 400]:
                print("✅ Alert index created")
                return True
            else:
                print(f"❌ Alert index creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Alert index setup error: {e}")
            return False
    
    def setup_index_templates(self):
        """Setup index templates for automatic index creation"""
        
        template = {
            "index_patterns": ["livewire-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "5s"
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "component_id": {"type": "keyword"}
                    }
                }
            }
        }
        
        try:
            response = requests.put(f"{self.elastic_url}/_index_template/livewire-template",
                                  json=template, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                print("✅ Index template created")
                return True
            else:
                print(f"❌ Template creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Template setup error: {e}")
            return False
    
    def create_kibana_dashboard_config(self):
        """Generate Kibana dashboard configuration"""
        
        dashboard_config = {
            "version": "8.0.0",
            "objects": [
                {
                    "id": "livewire-sensor-dashboard",
                    "type": "dashboard",
                    "attributes": {
                        "title": "LiveWire Cable Monitoring Dashboard",
                        "description": "Real-time infrastructure monitoring",
                        "panelsJSON": json.dumps([
                            {
                                "gridData": {"x": 0, "y": 0, "w": 24, "h": 15},
                                "panelIndex": "1",
                                "embeddableConfig": {},
                                "panelRefName": "panel_1"
                            }
                        ])
                    }
                }
            ]
        }
        
        # Save to file
        with open("elastic/kibana_dashboard.json", "w") as f:
            json.dump(dashboard_config, f, indent=2)
        
        print("✅ Kibana dashboard config saved to elastic/kibana_dashboard.json")
    
    def test_data_ingestion(self):
        """Test data ingestion with sample sensor reading"""
        
        test_doc = {
            "timestamp": datetime.now().isoformat(),
            "component_id": "TEST_CABLE_001",
            "temperature": 28.5,
            "vibration": 0.15,
            "strain": 125.0,
            "power": 1050.0,
            "risk_zone": "green",
            "prediction_confidence": 0.85
        }
        
        try:
            response = requests.post(f"{self.elastic_url}/livewire-sensors/_doc",
                                   json=test_doc, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 201:
                print("✅ Test data ingestion successful")
                return True
            else:
                print(f"❌ Test ingestion failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Test ingestion error: {e}")
            return False
    
    def setup_all(self):
        """Complete Elastic setup for LiveWire"""
        print("🔥 LiveWire Elastic Setup")
        print("=" * 40)
        
        success = True
        
        # Check Elastic health
        if not self.check_elastic_health():
            print("\n❌ Setup failed: Elastic not available")
            return False
        
        # Create indices
        print("\n📊 Creating indices...")
        success &= self.create_sensor_index()
        success &= self.create_alert_index()
        
        # Setup templates
        print("\n📋 Setting up templates...")
        success &= self.setup_index_templates()
        
        # Test ingestion
        print("\n🧪 Testing data ingestion...")
        success &= self.test_data_ingestion()
        
        # Create Kibana config
        print("\n📈 Creating Kibana dashboard config...")
        self.create_kibana_dashboard_config()
        
        if success:
            print("\n✅ LiveWire Elastic setup complete!")
            print("\n🚀 Next steps:")
            print("1. Run raspberry_pi_sensor.py to start sending sensor data")
            print("2. Run realtime_predictor.py to start CCI predictions")
            print("3. Open Kibana to view dashboards")
            print(f"4. View data at: {self.elastic_url}/livewire-sensors/_search")
        else:
            print("\n❌ Setup had some issues - check the logs above")
        
        return success


def main():
    """Setup Elastic for LiveWire"""
    setup = ElasticSetup()
    setup.setup_all()


if __name__ == "__main__":
    main()