#!/usr/bin/env python3
"""Test if the view exists and can be accessed."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.dependencies.database import DatabaseManager

def test_view_exists():
    """Test if APPLICABLE_ROLES view exists and can be accessed."""
    print("🔍 Testing View Existence and DDL Access")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        
        # Test 1: Check if the view exists
        print("\n1. Checking if APPLICABLE_ROLES view exists...")
        check_query = """
        SELECT TABLE_NAME, TABLE_SCHEMA, TABLE_CATALOG
        FROM SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_NAME = 'APPLICABLE_ROLES'
        AND TABLE_SCHEMA = 'INFORMATION_SCHEMA'
        AND TABLE_CATALOG = 'SNOWFLAKE_LEARNING_DB'
        """
        
        try:
            results = db_manager.execute_query(check_query)
            if results:
                print(f"✅ View exists! Found {len(results)} matching views:")
                for row in results:
                    view_name = getattr(row, 'TABLE_NAME', row[0] if len(row) > 0 else 'unknown')
                    schema_name = getattr(row, 'TABLE_SCHEMA', row[1] if len(row) > 1 else 'unknown')
                    db_name = getattr(row, 'TABLE_CATALOG', row[2] if len(row) > 2 else 'unknown')
                    print(f"   - {db_name}.{schema_name}.{view_name}")
            else:
                print("❌ View not found!")
                return
        except Exception as e:
            print(f"❌ Error checking view existence: {e}")
            return
        
        # Test 2: Try to get DDL with different qualifications
        print("\n2. Testing DDL retrieval methods...")
        
        # Method 1: Full qualification
        try:
            ddl_query1 = "SELECT GET_DDL('VIEW', 'SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.APPLICABLE_ROLES') as ddl"
            print(f"Trying: {ddl_query1}")
            result1 = db_manager.execute_query(ddl_query1)
            if result1 and len(result1) > 0:
                ddl = getattr(result1[0], 'ddl', result1[0][0] if len(result1[0]) > 0 else None)
                if ddl:
                    print("✅ Full qualification worked!")
                    print(f"DDL length: {len(ddl)} characters")
                    print(f"DDL preview: {ddl[:200]}...")
                    return
        except Exception as e:
            print(f"❌ Full qualification failed: {e}")
        
        # Method 2: Schema qualification
        try:
            ddl_query2 = "SELECT GET_DDL('VIEW', 'INFORMATION_SCHEMA.APPLICABLE_ROLES') as ddl"
            print(f"Trying: {ddl_query2}")
            result2 = db_manager.execute_query(ddl_query2)
            if result2 and len(result2) > 0:
                ddl = getattr(result2[0], 'ddl', result2[0][0] if len(result2[0]) > 0 else None)
                if ddl:
                    print("✅ Schema qualification worked!")
                    print(f"DDL length: {len(ddl)} characters")
                    print(f"DDL preview: {ddl[:200]}...")
                    return
        except Exception as e:
            print(f"❌ Schema qualification failed: {e}")
        
        # Method 3: No qualification
        try:
            ddl_query3 = "SELECT GET_DDL('VIEW', 'APPLICABLE_ROLES') as ddl"
            print(f"Trying: {ddl_query3}")
            result3 = db_manager.execute_query(ddl_query3)
            if result3 and len(result3) > 0:
                ddl = getattr(result3[0], 'ddl', result3[0][0] if len(result3[0]) > 0 else None)
                if ddl:
                    print("✅ No qualification worked!")
                    print(f"DDL length: {len(ddl)} characters")
                    print(f"DDL preview: {ddl[:200]}...")
                    return
        except Exception as e:
            print(f"❌ No qualification failed: {e}")
        
        print("❌ All DDL retrieval methods failed!")
        
        # Test 3: Check current database context
        print("\n3. Checking current database context...")
        try:
            context_query = "SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()"
            context_result = db_manager.execute_query(context_query)
            if context_result:
                current_db = context_result[0][0] if len(context_result[0]) > 0 else 'unknown'
                current_schema = context_result[0][1] if len(context_result[0]) > 1 else 'unknown'
                print(f"Current database: {current_db}")
                print(f"Current schema: {current_schema}")
        except Exception as e:
            print(f"❌ Error checking context: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_view_exists()