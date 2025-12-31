#!/usr/bin/env python3
"""Test the analysis endpoint to make sure it works correctly."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_analysis_endpoint():
    """Test the analysis endpoint."""
    print("🧪 Testing Analysis Endpoint")
    print("=" * 40)
    
    # Test data
    test_request = {
        "database_filter": "SNOWFLAKE_LEARNING_DB",
        "schema_filter": "INFORMATION_SCHEMA",
        "async_processing": True,
        "include_metadata": True
    }
    
    headers = {
        "Content-Type": "application/json",
        # Add your JWT token here for authenticated endpoint
        # "Authorization": "Bearer YOUR_TOKEN_HERE"
    }
    
    try:
        print("1. Testing analysis endpoint...")
        print(f"Request: {json.dumps(test_request, indent=2)}")
        
        # Use public endpoint for testing (if available) or authenticated endpoint
        response = requests.post(
            f"{BASE_URL}/api/v1/lineage/analyze",
            json=test_request,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis started successfully!")
            print(f"Job ID: {data.get('job_id')}")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            
            job_id = data.get('job_id')
            if job_id:
                print(f"\n2. Testing job status endpoint...")
                time.sleep(1)  # Wait a moment
                
                status_response = requests.get(
                    f"{BASE_URL}/api/v1/lineage/status/{job_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ Job status retrieved!")
                    print(f"Status: {status_data.get('status')}")
                    print(f"Progress: {status_data.get('processed_views')}/{status_data.get('total_views')}")
                else:
                    print(f"❌ Job status failed: {status_response.status_code}")
                    print(f"Error: {status_response.text}")
            
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
    test_analysis_endpoint()