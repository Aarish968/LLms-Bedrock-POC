#!/usr/bin/env python3
"""Simple test using requests to verify API endpoints."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints."""
    print("🧪 Testing API endpoints...")
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    try:
        # Test health endpoint first
        print("\n1. Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Health check - Status: {response.status_code}")
        
        # Test databases endpoint
        print("\n2. Testing databases endpoint...")
        response = requests.get(f"{BASE_URL}/api/v1/lineage/public/databases", timeout=30)
        print(f"✅ Databases - Status: {response.status_code}")
        
        if response.status_code == 200:
            databases = response.json()
            print(f"   Found {len(databases)} databases: {databases}")
            
            if databases:
                first_db = databases[0]
                
                # Test schemas endpoint
                print(f"\n3. Testing schemas endpoint for database: {first_db}")
                response = requests.get(
                    f"{BASE_URL}/api/v1/lineage/public/schemas",
                    params={"database_filter": first_db},
                    timeout=30
                )
                print(f"✅ Schemas - Status: {response.status_code}")
                
                if response.status_code == 200:
                    schemas = response.json()
                    print(f"   Found {len(schemas)} schemas: {schemas[:5]}...")  # Show first 5
                    
                    if schemas:
                        first_schema = schemas[0]
                        
                        # Test views endpoint
                        print(f"\n4. Testing views endpoint for {first_db}.{first_schema}")
                        response = requests.get(
                            f"{BASE_URL}/api/v1/lineage/public/views",
                            params={
                                "database_filter": first_db,
                                "schema_filter": first_schema,
                                "limit": 5
                            },
                            timeout=30
                        )
                        print(f"✅ Views - Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            views = response.json()
                            print(f"   Found {len(views)} views")
                            for view in views:
                                print(f"   - {view['view_name']} ({view['column_count']} columns)")
                        else:
                            print(f"   Error: {response.text}")
                    else:
                        print("⚠️  No schemas found")
                else:
                    print(f"   Error: {response.text}")
            else:
                print("⚠️  No databases found")
        else:
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_api()