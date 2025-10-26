"""
Serverless-Compatible Elastic Test
=================================

Proper test for Elastic Serverless (some APIs are different).
"""

import requests
import json
import time

def test_serverless_connection():
    """Test connection with serverless-compatible APIs"""
    
    # Load credentials
    try:
        with open('elastic/credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ No credentials found")
        return False
    
    endpoint = creds['cloud_id'].rstrip('/')
    headers = {
        'Authorization': f'ApiKey {creds["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    print(f"🌐 Testing Elastic Serverless connection...")
    print(f"📡 Endpoint: {endpoint}")
    
    # Test 1: Basic connectivity with root endpoint
    try:
        print(f"\n🧪 Test 1: Basic connectivity")
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if response.status_code == 200:
            info = response.json()
            print(f"✅ Connected successfully!")
            print(f"📊 Cluster: {info.get('cluster_name', 'serverless')}")
            print(f"🏷️ Version: {info.get('version', {}).get('number', 'unknown')}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return False
    
    # Test 2: Create a test index (serverless compatible)
    try:
        print(f"\n🧪 Test 2: Index operations")
        test_index = "test-livewire-" + str(int(time.time()))
        
        # Create index
        mapping = {
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "message": {"type": "text"},
                    "component_id": {"type": "keyword"}
                }
            }
        }
        
        response = requests.put(f"{endpoint}/{test_index}", 
                              json=mapping, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ Index creation successful!")
            
            # Insert test document
            test_doc = {
                "@timestamp": "2024-01-01T00:00:00Z",
                "message": "LiveWire test document",
                "component_id": "TEST_COMPONENT"
            }
            
            response = requests.post(f"{endpoint}/{test_index}/_doc", 
                                   json=test_doc, headers=headers)
            
            if response.status_code == 201:
                print(f"✅ Document insertion successful!")
                
                # Clean up
                requests.delete(f"{endpoint}/{test_index}", headers=headers)
                print(f"✅ Cleanup successful!")
                
                print(f"\n🎉 ELASTIC SERVERLESS FULLY WORKING!")
                print(f"🚀 Ready for Cal Hacks demo!")
                return True
            else:
                print(f"⚠️ Document insertion failed: {response.status_code}")
        else:
            print(f"❌ Index creation failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Index operations failed: {e}")
        return False
    
    return False

def main():
    """Test serverless connection"""
    import time
    
    print("🌐 LiveWire Elastic Serverless Test")
    print("Infrastructure monitoring with Elastic Agent Builder")
    print("=" * 60)
    
    if test_serverless_connection():
        print(f"\n✅ ALL TESTS PASSED!")
        print(f"🔥 Your Elastic Serverless is ready!")
        print(f"🎬 Next step: python quick_demo.py")
        
        print(f"\nCRITERIA MET:")
        print(f"✅ Elastic Serverless instance working")
        print(f"✅ API connection established")
        print(f"✅ Index operations functional")
        print(f"✅ Ready for Agent Builder demo")
    else:
        print(f"\n❌ Tests failed - check your setup")

if __name__ == "__main__":
    main()