#!/usr/bin/env python3
"""Test synchronous analysis to debug the issue."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_sync_analysis():
    """Test synchronous analysis to see what happens."""
    print("🧪 Testing Synchronous Analysis")
    print("=" * 40)
    
    # Test data - using synchronous processing
    test_request = {
        "database_filter": "SNOWFLAKE_LEARNING_DB",
        "schema_filter": "INFORMATION_SCHEMA",  # Try INFORMATION_SCHEMA first as it usually has views
        "async_processing": False,  # Synchronous for debugging
        "include_metadata": True
    }
    
    headers = {
        "Content-Type": "application/json",
        # Add your JWT token here
        "Authorization": "Bearer YOUR_TOKEN_HERE"  # Replace with actual token
    }
    
    try:
        print("Testing synchronous analysis...")
        print(f"Request: {json.dumps(test_request, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/lineage/analyze",
            json=test_request,
            headers=headers,
            timeout=60  # Longer timeout for sync processing
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis completed!")
            print(f"Job ID: {data.get('job_id')}")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
        elif response.status_code == 401:
            print("❌ Authentication required. Please add your JWT token to the headers.")
        else:
            print(f"❌ Analysis failed:")
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
    test_sync_analysis()