#!/usr/bin/env python3
"""Test script to verify the SQL fix for Snowflake column names."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.v1.services.lineage_service import LineageService

async def test_database_queries():
    """Test the database and schema queries."""
    print("🧪 Testing Snowflake SQL queries...")
    
    service = LineageService()
    
    try:
        print("\n1. Testing get_available_databases()...")
        databases = await service.get_available_databases()
        print(f"✅ Found {len(databases)} databases: {databases}")
        
        if databases:
            first_db = databases[0]
            print(f"\n2. Testing get_available_schemas() for database: {first_db}")
            schemas = await service.get_available_schemas(first_db)
            print(f"✅ Found {len(schemas)} schemas: {schemas}")
            
            if schemas:
                first_schema = schemas[0]
                print(f"\n3. Testing get_available_views() for {first_db}.{first_schema}")
                views = await service.get_available_views(
                    schema_filter=first_schema,
                    database_filter=first_db,
                    limit=5
                )
                print(f"✅ Found {len(views)} views")
                for view in views[:3]:  # Show first 3 views
                    print(f"   - {view.view_name} ({view.column_count} columns)")
            else:
                print("⚠️  No schemas found")
        else:
            print("⚠️  No databases found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_queries())