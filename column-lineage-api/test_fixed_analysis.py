#!/usr/bin/env python3
"""Test the fixed analysis endpoint."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_fixed_analysis():
    """Test the fixed analysis endpoint."""
    print("🧪 Testing Fixed Analysis Endpoint")
    print("=" * 50)
    
    # Test data - using a view that should exist
    test_request = {
        "view_names": ["APPLICABLE_ROLES"],  # This view exists in INFORMATION_SCHEMA
        "database_filter": "SNOWFLAKE_LEARNING_DB",
        "schema_filter": "INFORMATION_SCHEMA",
        "async_processing": False,  # Synchronous for testing
        "include_metadata": True,
        "max_views": 1
    }
    
    headers = {
        "Content-Type": "application/json",
        # Add your JWT token here
        "Authorization": "Bearer YOUR_TOKEN_HERE"  # Replace with actual token
    }
    
    try:
        print("1. Testing analysis with INFORMATION_SCHEMA view...")
        print(f"Request: {json.dumps(test_request, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/lineage/analyze",
            json=test_request,
            headers=headers,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis response:")
            print(f"   Job ID: {data.get('job_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            job_id = data.get('job_id')
            if job_id:
                print(f"\n2. Testing job status...")
                time.sleep(1)
                
                status_response = requests.get(
                    f"{BASE_URL}/api/v1/lineage/status/{job_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ Job status:")
                    print(f"   Status: {status_data.get('status')}")
                    print(f"   Total Views: {status_data.get('total_views')}")
                    print(f"   Processed: {status_data.get('processed_views')}")
                    print(f"   Results: {status_data.get('results_count')}")
                    
                    if status_data.get('status') == 'COMPLETED':
                        print(f"\n3. Testing results...")
                        results_response = requests.get(
                            f"{BASE_URL}/api/v1/lineage/results/{job_id}",
                            headers=headers,
                            timeout=30
                        )
                        
                        if results_response.status_code == 200:
                            results_data = results_response.json()
                            print(f"✅ Results retrieved:")
                            print(f"   Total Results: {results_data.get('total_results')}")
                            print(f"   Results Count: {len(results_data.get('results', []))}")
                        else:
                            print(f"❌ Results failed: {results_response.status_code}")
                            print(f"   Error: {results_response.text}")
                    
                else:
                    print(f"❌ Status failed: {status_response.status_code}")
                    print(f"   Error: {status_response.text}")
            
        elif response.status_code == 401:
            print("❌ Authentication required. Please add your JWT token to the headers.")
        else:
            print(f"❌ Analysis failed:")
            print(f"   Status: {response.status_code}")
            print(f"   Text: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Exception: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    test_fixed_analysis()