#!/usr/bin/env python3
"""Simple API test to verify the fix works."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple():
    """Simple test of the API."""
    print("🧪 Simple API Test")
    print("=" * 30)
    
    try:
        print("Testing databases endpoint...")
        response = requests.get(f"{BASE_URL}/api/v1/lineage/public/databases", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} databases:")
            for db in data:
                print(f"   - {db}")
        else:
            print(f"❌ Error Response:")
            print(f"   Status: {response.status_code}")
            print(f"   Text: {response.text}")
            try:
                error_data = response.json()
                print(f"   JSON: {json.dumps(error_data, indent=2)}")
            except:
                pass
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Exception: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_simple()