#!/usr/bin/env python3
"""Test script for the updated API endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_public_endpoints():
    """Test the public endpoints without authentication."""
    print("🧪 Testing public endpoints...")
    
    # Test databases endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/lineage/public/databases")
        print(f"✅ GET /public/databases - Status: {response.status_code}")
        if response.status_code == 200:
            databases = response.json()
            print(f"   Found {len(databases)} databases: {databases[:3]}...")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ GET /public/databases failed: {e}")
    
    # Test schemas endpoint (using first database if available)
    try:
        # First get databases
        db_response = requests.get(f"{BASE_URL}/api/v1/lineage/public/databases")
        if db_response.status_code == 200 and db_response.json():
            first_db = db_response.json()[0]
            
            response = requests.get(f"{BASE_URL}/api/v1/lineage/public/schemas", 
                                  params={"database_filter": first_db})
            print(f"✅ GET /public/schemas - Status: {response.status_code}")
            if response.status_code == 200:
                schemas = response.json()
                print(f"   Found {len(schemas)} schemas for {first_db}: {schemas[:3]}...")
            else:
                print(f"   Error: {response.text}")
        else:
            print("⚠️  No databases found, skipping schemas test")
    except Exception as e:
        print(f"❌ GET /public/schemas failed: {e}")
    
    # Test views endpoint (using first database and schema if available)
    try:
        # Get databases and schemas
        db_response = requests.get(f"{BASE_URL}/api/v1/lineage/public/databases")
        if db_response.status_code == 200 and db_response.json():
            first_db = db_response.json()[0]
            
            schema_response = requests.get(f"{BASE_URL}/api/v1/lineage/public/schemas", 
                                         params={"database_filter": first_db})
            if schema_response.status_code == 200 and schema_response.json():
                first_schema = schema_response.json()[0]
                
                response = requests.get(f"{BASE_URL}/api/v1/lineage/public/views", 
                                      params={
                                          "database_filter": first_db,
                                          "schema_filter": first_schema,
                                          "limit": 5
                                      })
                print(f"✅ GET /public/views - Status: {response.status_code}")
                if response.status_code == 200:
                    views = response.json()
                    print(f"   Found {len(views)} views for {first_db}.{first_schema}")
                    if views:
                        print(f"   Sample view: {views[0]['view_name']}")
                else:
                    print(f"   Error: {response.text}")
            else:
                print("⚠️  No schemas found, skipping views test")
        else:
            print("⚠️  No databases found, skipping views test")
    except Exception as e:
        print(f"❌ GET /public/views failed: {e}")

def test_with_auth(token):
    """Test authenticated endpoints."""
    print("\n🔐 Testing authenticated endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test databases endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/lineage/databases", headers=headers)
        print(f"✅ GET /databases - Status: {response.status_code}")
        if response.status_code == 200:
            databases = response.json()
            print(f"   Found {len(databases)} databases")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ GET /databases failed: {e}")

def main():
    """Main test function."""
    print("🚀 Testing Column Lineage API endpoints...")
    print("=" * 50)
    
    # Test public endpoints
    test_public_endpoints()
    
    # Test with auth if token provided
    token = input("\n🔑 Enter your JWT token (or press Enter to skip auth tests): ").strip()
    if token:
        test_with_auth(token)
    else:
        print("⏭️  Skipping authenticated endpoint tests")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    main()