#!/usr/bin/env python3
"""Debug script to understand column name issues."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.dependencies.database import DatabaseManager

def debug_database_query():
    """Debug the database query to understand column names."""
    print("🔍 Debugging Database Query Column Names")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        
        # Test the query
        query = """
        SELECT DATABASE_NAME
        FROM INFORMATION_SCHEMA.DATABASES
        ORDER BY DATABASE_NAME
        """
        
        print(f"Executing query: {query}")
        results = db_manager.execute_query(query)
        
        if results:
            print(f"\n✅ Query returned {len(results)} rows")
            
            # Debug first row
            first_row = results[0]
            print(f"\n🔍 First row type: {type(first_row)}")
            print(f"🔍 First row dir: {dir(first_row)}")
            
            # Try different access methods
            print(f"\n🧪 Testing different access methods:")
            
            # Method 1: Direct attribute access
            try:
                value = first_row.DATABASE_NAME
                print(f"✅ first_row.DATABASE_NAME = {value}")
            except AttributeError as e:
                print(f"❌ first_row.DATABASE_NAME failed: {e}")
            
            # Method 2: Lowercase attribute
            try:
                value = first_row.database_name
                print(f"✅ first_row.database_name = {value}")
            except AttributeError as e:
                print(f"❌ first_row.database_name failed: {e}")
            
            # Method 3: Index access
            try:
                value = first_row[0]
                print(f"✅ first_row[0] = {value}")
            except (IndexError, TypeError) as e:
                print(f"❌ first_row[0] failed: {e}")
            
            # Method 4: Mapping access
            if hasattr(first_row, '_mapping'):
                mapping = first_row._mapping
                print(f"✅ Row mapping keys: {list(mapping.keys())}")
                for key in mapping.keys():
                    print(f"   {key} = {mapping[key]}")
            else:
                print("❌ No _mapping attribute")
            
            # Method 5: Keys method
            if hasattr(first_row, 'keys'):
                keys = first_row.keys()
                print(f"✅ Row keys: {list(keys)}")
            else:
                print("❌ No keys method")
                
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database_query()