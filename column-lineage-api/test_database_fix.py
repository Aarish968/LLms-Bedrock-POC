#!/usr/bin/env python3
"""Test the fixed database queries."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_fixed_endpoints():
    """Test the fixed API endpoints."""
    print("🧪 Testing Fixed Database Endpoints")
    print("=" * 50)
    
    try:
        # Test databases endpoint
        print("\n1. Testing databases endpoint...")
        response = requests.get(f"{BASE_URL}/api/v1/lineage/public/databases", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            databases = response.json()
            print(f"✅ Found {len(databases)} databases:")
            for db in databases:
                print(f"   - {db}")
            
            if databases:
                # Test with the first database
                test_db = databases[0]
                print(f"\n2. Testing schemas for database: {test_db}")
                
                response = requests.get(
                    f"{BASE_URL}/api/v1/lineage/public/schemas",
                    params={"database_filter": test_db},
                    timeout=30
                )
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    schemas = response.json()
                    print(f"✅ Found {len(schemas)} schemas:")
                    for schema in schemas[:10]:  # Show first 10
                        print(f"   - {schema}")
                    
                    if schemas:
                        # Test with the first schema
                        test_schema = schemas[0]
                        print(f"\n3. Testing views for {test_db}.{test_schema}")
                        
                        response = requests.get(
                            f"{BASE_URL}/api/v1/lineage/public/views",
                            params={
                                "database_filter": test_db,
                                "schema_filter": test_schema,
                                "limit": 5
                            },
                            timeout=30
                        )
                        print(f"Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            views = response.json()
                            print(f"✅ Found {len(views)} views:")
                            for view in views:
                                print(f"   - {view['view_name']} ({view['column_count']} columns)")
                        else:
                            print(f"❌ Views error: {response.text}")
                    else:
                        print("⚠️  No schemas found")
                else:
                    print(f"❌ Schemas error: {response.text}")
            else:
                print("⚠️  No databases found")
        else:
            print(f"❌ Databases error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main test function."""
    print("🚀 Testing Fixed Snowflake Database Queries")
    print("Make sure your server is running on localhost:8000")
    print()
    
    # Wait a moment
    time.sleep(1)
    
    test_fixed_endpoints()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    main()