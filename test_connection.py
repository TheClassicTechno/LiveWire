"""
Quick Elastic Serverless Connection Test
========================================

Test your Elastic Serverless credentials and connection.
"""

import requests
import json
import base64

def test_elastic_connection():
    """Test connection with your credentials"""
    
    # Load saved credentials
    try:
        with open('elastic/credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ No credentials found. Run setup_complete.py first")
        return False
    
    cloud_id = creds['cloud_id']
    api_key = creds['api_key']
    
    print(f"🧪 Testing connection to: {cloud_id}")
    
    # Parse endpoint
    if cloud_id.startswith('https://'):
        endpoint = cloud_id.rstrip('/')
    else:
        print(f"❌ Expected HTTPS URL, got: {cloud_id}")
        print(f"💡 Please use the full Elasticsearch endpoint URL from your Elastic Cloud console")
        return False
    
    # Setup headers
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test connection
    try:
        print(f"🔌 Testing: {endpoint}/_cluster/health")
        response = requests.get(f"{endpoint}/_cluster/health", headers=headers, timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Connection successful!")
            print(f"📊 Cluster status: {health.get('status', 'unknown')}")
            print(f"🌐 Cluster name: {health.get('cluster_name', 'unknown')}")
            
            # Test basic index creation
            test_index = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "message": {"type": "text"}
                    }
                }
            }
            
            print(f"\n🧪 Testing index creation...")
            response = requests.put(f"{endpoint}/test-livewire-connection", 
                                  json=test_index, headers=headers)
            
            if response.status_code in [200, 400]:  # 400 if index exists
                print(f"✅ Index operations working!")
                
                # Clean up test index
                requests.delete(f"{endpoint}/test-livewire-connection", headers=headers)
                
                print(f"\n🎉 ELASTIC SERVERLESS IS READY!")
                print(f"🚀 You can now run: python quick_demo.py")
                return True
            else:
                print(f"⚠️ Index creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        elif response.status_code == 401:
            print(f"❌ Authentication failed!")
            print(f"💡 Check your API Key - it may be incorrect")
            return False
        elif response.status_code == 403:
            print(f"❌ Access forbidden!")
            print(f"💡 Check your API Key permissions")
            return False
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - check the endpoint URL")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    """Test Elastic connection"""
    print("🔌 LiveWire Elastic Serverless Connection Test")
    print("=" * 50)
    
    if test_elastic_connection():
        print(f"\n✅ SUCCESS! Ready for Cal Hacks demo!")
    else:
        print(f"\n❌ Connection failed. Please check:")
        print(f"1. Use the full HTTPS URL from Elastic Cloud console")
        print(f"2. Verify your API Key is correct")
        print(f"3. Check internet connection")

if __name__ == "__main__":
    main()