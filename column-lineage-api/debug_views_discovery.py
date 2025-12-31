#!/usr/bin/env python3
"""Debug script to check view discovery."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.dependencies.database import DatabaseManager

def debug_views_discovery():
    """Debug view discovery to see what's happening."""
    print("🔍 Debugging Views Discovery")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        
        # Test 1: Check if there are any views in SNOWFLAKE_LEARNING_DB.PUBLIC
        print("\n1. Testing views in SNOWFLAKE_LEARNING_DB.PUBLIC...")
        query1 = """
        SELECT 
            TABLE_NAME as view_name,
            TABLE_SCHEMA as schema_name,
            TABLE_CATALOG as database_name
        FROM SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_CATALOG = 'SNOWFLAKE_LEARNING_DB'
        AND TABLE_SCHEMA = 'PUBLIC'
        ORDER BY TABLE_NAME
        LIMIT 10
        """
        
        try:
            results1 = db_manager.execute_query(query1)
            print(f"✅ Found {len(results1)} views in SNOWFLAKE_LEARNING_DB.PUBLIC")
            for row in results1:
                print(f"   - {getattr(row, 'view_name', row[0] if len(row) > 0 else 'unknown')}")
        except Exception as e:
            print(f"❌ Query 1 failed: {e}")
        
        # Test 2: Check views in INFORMATION_SCHEMA
        print("\n2. Testing views in SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA...")
        query2 = """
        SELECT 
            TABLE_NAME as view_name,
            TABLE_SCHEMA as schema_name,
            TABLE_CATALOG as database_name
        FROM SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_CATALOG = 'SNOWFLAKE_LEARNING_DB'
        AND TABLE_SCHEMA = 'INFORMATION_SCHEMA'
        ORDER BY TABLE_NAME
        LIMIT 10
        """
        
        try:
            results2 = db_manager.execute_query(query2)
            print(f"✅ Found {len(results2)} views in SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA")
            for row in results2:
                print(f"   - {getattr(row, 'view_name', row[0] if len(row) > 0 else 'unknown')}")
        except Exception as e:
            print(f"❌ Query 2 failed: {e}")
        
        # Test 3: Check all schemas in SNOWFLAKE_LEARNING_DB
        print("\n3. Checking all schemas in SNOWFLAKE_LEARNING_DB...")
        query3 = """
        SELECT DISTINCT SCHEMA_NAME
        FROM SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.SCHEMATA
        WHERE CATALOG_NAME = 'SNOWFLAKE_LEARNING_DB'
        ORDER BY SCHEMA_NAME
        """
        
        try:
            results3 = db_manager.execute_query(query3)
            print(f"✅ Found {len(results3)} schemas in SNOWFLAKE_LEARNING_DB:")
            for row in results3:
                schema_name = None
                for attr in ['SCHEMA_NAME', 'schema_name']:
                    try:
                        schema_name = getattr(row, attr, None)
                        if schema_name:
                            break
                    except AttributeError:
                        continue
                if not schema_name:
                    try:
                        schema_name = row[0]
                    except (IndexError, TypeError):
                        schema_name = 'unknown'
                print(f"   - {schema_name}")
        except Exception as e:
            print(f"❌ Query 3 failed: {e}")
        
        # Test 4: Check views in each schema
        print("\n4. Checking view counts per schema...")
        query4 = """
        SELECT 
            TABLE_SCHEMA,
            COUNT(*) as view_count
        FROM SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_CATALOG = 'SNOWFLAKE_LEARNING_DB'
        GROUP BY TABLE_SCHEMA
        ORDER BY view_count DESC
        """
        
        try:
            results4 = db_manager.execute_query(query4)
            print(f"✅ View counts by schema:")
            for row in results4:
                schema = getattr(row, 'TABLE_SCHEMA', row[0] if len(row) > 0 else 'unknown')
                count = getattr(row, 'view_count', row[1] if len(row) > 1 else 0)
                print(f"   - {schema}: {count} views")
        except Exception as e:
            print(f"❌ Query 4 failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_views_discovery()