#!/usr/bin/env python3
"""
Test script to debug Snowflake connection issues.
Run this script to test your Snowflake connection independently.
"""

import os
import sys
from urllib.parse import quote_plus

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import snowflake.connector
    except ImportError:
        missing_deps.append("snowflake-connector-python")
    
    try:
        from snowflake.sqlalchemy import URL
    except ImportError:
        missing_deps.append("snowflake-sqlalchemy")
    
    try:
        from sqlalchemy import create_engine
    except ImportError:
        missing_deps.append("sqlalchemy")
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        missing_deps.append("python-dotenv")
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nPlease install them using:")
        print(f"   pip install {' '.join(missing_deps)}")
        return False
    
    return True

def test_snowflake_connection():
    """Test Snowflake connection with detailed debugging."""
    
    print("=== Snowflake Connection Test ===")
    
    # Check dependencies first
    if not check_dependencies():
        return False
    
    # Import after dependency check
    from dotenv import load_dotenv
    from sqlalchemy import create_engine
    import snowflake.connector
    
    # Load environment variables
    load_dotenv()
    
    # Get Snowflake credentials
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    role = os.getenv("SNOWFLAKE_ROLE")
    
    print(f"Account: {account}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Schema: {schema}")
    print(f"Warehouse: {warehouse}")
    print(f"Role: {role}")
    print(f"Password length: {len(password) if password else 0} characters")
    print()
    
    if not all([account, user, password, database]):
        print("❌ Missing required Snowflake credentials!")
        missing = []
        if not account: missing.append("SNOWFLAKE_ACCOUNT")
        if not user: missing.append("SNOWFLAKE_USER") 
        if not password: missing.append("SNOWFLAKE_PASSWORD")
        if not database: missing.append("SNOWFLAKE_DATABASE")
        print(f"Missing: {', '.join(missing)}")
        return False
    
    # Test 1: Direct snowflake-connector-python connection
    print("=== Test 1: Direct Snowflake Connector ===")
    try:
        print("Attempting direct connection...")
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role,
            application="column-lineage-api-test",
            login_timeout=60,
            network_timeout=60
        )
        
        print("Connection established, testing query...")
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Direct connection successful! Snowflake version: {version}")
        
        # Test BASE_VIEW table
        try:
            print("Testing BASE_VIEW table access...")
            cursor.execute("SELECT COUNT(*) FROM PUBLIC.BASE_VIEW")
            count = cursor.fetchone()[0]
            print(f"✅ BASE_VIEW table found with {count} records")
            
            if count > 0:
                cursor.execute("SELECT SR_NO, TABLE_NAME FROM PUBLIC.BASE_VIEW LIMIT 5")
                print("\nSample data:")
                for row in cursor.fetchall():
                    print(f"  SR_NO: {row[0]}, TABLE_NAME: {row[1]}")
        except Exception as table_error:
            print(f"❌ BASE_VIEW table test failed: {table_error}")
            print("This might be because the table doesn't exist or you don't have permissions")
        
        cursor.close()
        conn.close()
        
    except snowflake.connector.errors.DatabaseError as db_error:
        print(f"❌ Direct connection failed - Database Error: {db_error}")
        print(f"Error code: {db_error.errno}")
        print(f"SQL state: {db_error.sqlstate}")
        return False
    except snowflake.connector.errors.ProgrammingError as prog_error:
        print(f"❌ Direct connection failed - Programming Error: {prog_error}")
        print("This usually means incorrect credentials or permissions")
        return False
    except Exception as e:
        print(f"❌ Direct connection failed - General Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Common troubleshooting
        print("\n🔍 Troubleshooting suggestions:")
        print("1. Check if your Snowflake account identifier is correct")
        print("   - It should be in format: <account_locator> or <account_locator>.<region>")
        print("   - Example: xy12345 or xy12345.us-east-1")
        print("2. Verify your username and password are correct")
        print("3. Check if your user has the required role permissions")
        print("4. Ensure the warehouse is running and accessible")
        print("5. Verify the database and schema exist")
        print("6. Check if your IP is whitelisted (if network policies are enabled)")
        print("7. Try logging into Snowflake web interface with the same credentials")
        
        return False
    
    # Test 2: SQLAlchemy connection
    print("\n=== Test 2: SQLAlchemy Connection ===")
    try:
        # URL encode password to handle special characters
        encoded_password = quote_plus(password)
        
        # Construct Snowflake URL
        snowflake_url = (
            f"snowflake://{user}:{encoded_password}"
            f"@{account}.snowflakecomputing.com/"
            f"{database}/{schema}"
            f"?warehouse={warehouse}&role={role}"
        )
        
        print(f"URL format: snowflake://{user}:***@{account}.snowflakecomputing.com/{database}/{schema}?warehouse={warehouse}&role={role}")
        
        # Create engine
        engine = create_engine(
            snowflake_url,
            echo=False,  # Disable SQL echo for cleaner output
            connect_args={
                "application": "column-lineage-api-test",
                "client_session_keep_alive": True,
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT CURRENT_VERSION()")
            version = result.fetchone()[0]
            print(f"✅ SQLAlchemy connection successful! Snowflake version: {version}")
            
            # Test BASE_VIEW table
            try:
                result = conn.execute("SELECT COUNT(*) FROM PUBLIC.BASE_VIEW")
                count = result.fetchone()[0]
                print(f"✅ BASE_VIEW table accessible via SQLAlchemy with {count} records")
            except Exception as e:
                print(f"❌ BASE_VIEW table test via SQLAlchemy failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_snowflake_connection()
    sys.exit(0 if success else 1)