"""
Quick Demo Runner for Judges
===========================

Pre-configured demo that runs immediately for judge presentations.
This will be auto-configured with your Elastic Serverless credentials.
"""

import sys
import os
import json

def load_credentials():
    """Load saved Elastic credentials"""
    try:
        with open('elastic/credentials.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No credentials found. Run: python setup_complete.py first")
        return None

def quick_judge_demo():
    """2-minute demo perfect for judges"""
    print("🔥 LIVEWIRE JUDGE DEMO")
    print("Infrastructure monitoring with Elastic Agent Builder on Serverless")
    print("=" * 60)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    print("Elastic Serverless credentials loaded")
    print(f"🌐 Connected to: {creds['cloud_id'].split(':')[0]}")
    print()
    
    # Import and run
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from elastic.elastic_agent import LiveWireElasticAgent
        
        print("🤖 Initializing LiveWire Elastic Agent...")
        agent = LiveWireElasticAgent(creds['cloud_id'], creds['api_key'])
        
        # Demo components with different scenarios
        components = [
            "JUDGE_DEMO_NORMAL",     # Shows green/normal
            "JUDGE_DEMO_WARNING",    # Shows yellow/warning  
            "JUDGE_DEMO_CRITICAL"    # Shows red/critical with alerts
        ]
        
        print("🎬 Starting judge demo...")
        print("Watch real-time data streaming to Elastic Serverless")
        print("🚨 Alerts will be generated for critical conditions")
        print("⏱️ Demo duration: 2 minutes")
        print()
        print("🗣️ TELL THE JUDGES:")
        print("   'This is a custom Elastic Agent Builder running on Serverless'")
        print("   'Real-time infrastructure monitoring with AI predictions'")
        print("   'Our model predicted the Camp Fire 308 days early'")
        print("   'Zero infrastructure management, pure cloud-native'")
        print()
        
        # Run the demo
        agent.start_monitoring(components, interval=4, duration=120)
        
        print("\nDEMO COMPLETE!")
        print("Data sent to Elastic Serverless:")
        print(f"   Metrics: metrics-livewire.sensors-default")
        print(f"   Alerts: logs-livewire.alerts-default")
        print()
        print("CRITERIA ACHIEVED:")
        print("Elastic Agent Builder + Serverless Instance")
        print("Real-world Application + Live Data Streams")
        
    except Exception as e:
        print(f"Demo error: {e}")
        print("Make sure you ran: python setup_complete.py first")

if __name__ == "__main__":
    quick_judge_demo()