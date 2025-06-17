# test_postgresql_setup.py - Test PostgreSQL Setup
"""
Test script to verify PostgreSQL migration is working correctly.
Run this script to ensure everything is set up properly.
"""

import sys
import traceback
from database_config import db_config
from auth import AuthManager

def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing Database Connection...")
    
    try:
        if db_config.test_connection():
            print("  ✅ Database connection successful!")
            return True
        else:
            print("  ❌ Database connection failed!")
            return False
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False

def test_table_creation():
    """Test table creation and schema"""
    print("\n🛠️ Testing Table Creation...")
    
    try:
        auth = AuthManager()
        print("  ✅ Tables created successfully!")
        
        # Check if tables exist
        with db_config.get_cursor() as (cursor, conn):
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            expected_tables = ['users', 'sessions', 'user_chats']
            for table in expected_tables:
                if table in tables:
                    print(f"  ✅ Table '{table}' exists")
                else:
                    print(f"  ❌ Table '{table}' missing")
                    return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Table creation error: {e}")
        traceback.print_exc()
        return False

def test_basic_operations():
    """Test basic CRUD operations"""
    print("\n⚙️ Testing Basic Operations...")
    
    try:
        auth = AuthManager()
        
        # Test user registration
        print("  📝 Testing user registration...")
        result = auth.register_user(
            "testuser_postgres", 
            "test@postgresql.com", 
            "testpassword123", 
            "testpassword123"
        )
        
        if result["success"]:
            print("  ✅ User registration successful!")
            user_id = result["user_id"]
        else:
            print(f"  ❌ User registration failed: {result['message']}")
            return False
        
        # Test user login
        print("  🔑 Testing user login...")
        login_result = auth.login_user("testuser_postgres", "testpassword123")
        
        if login_result["success"]:
            print("  ✅ User login successful!")
            session_token = login_result["session_token"]
        else:
            print(f"  ❌ User login failed: {login_result['message']}")
            return False
        
        # Test session verification
        print("  🔍 Testing session verification...")
        session_result = auth.verify_session(session_token)
        
        if session_result["valid"]:
            print("  ✅ Session verification successful!")
        else:
            print("  ❌ Session verification failed!")
            return False
        
        # Test chat data operations
        print("  💬 Testing chat data operations...")
        test_chat_data = [
            {
                "id": "test_chat_1",
                "title": "Test Chat",
                "messages": [
                    {"type": "user", "content": "Hello PostgreSQL!"},
                    {"type": "assistant", "content": "Hello! PostgreSQL is working great!"}
                ]
            }
        ]
        
        save_result = auth.save_user_chat_data(user_id, test_chat_data)
        if save_result["success"]:
            print("  ✅ Chat data save successful!")
        else:
            print(f"  ❌ Chat data save failed: {save_result['message']}")
            return False
        
        load_result = auth.load_user_chat_data(user_id)
        if load_result["success"] and load_result["data"]:
            print("  ✅ Chat data load successful!")
        else:
            print(f"  ❌ Chat data load failed: {load_result}")
            return False
        
        # Test logout
        print("  🚪 Testing user logout...")
        logout_result = auth.logout_user(session_token)
        
        if logout_result["success"]:
            print("  ✅ User logout successful!")
        else:
            print(f"  ❌ User logout failed: {logout_result['message']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Basic operations error: {e}")
        traceback.print_exc()
        return False

def test_data_types():
    """Test PostgreSQL specific data types (JSONB, etc.)"""
    print("\n🗃️ Testing PostgreSQL Data Types...")
    
    try:
        with db_config.get_cursor() as (cursor, conn):
            # Test JSONB operations
            cursor.execute("""
                SELECT chat_data->>'id' as chat_id, 
                       jsonb_array_length(chat_data) as data_length
                FROM user_chats 
                WHERE user_id = (SELECT id FROM users WHERE username = 'testuser_postgres')
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                print("  ✅ JSONB operations working!")
                print(f"    - Chat ID: {result['chat_id']}")
                print(f"    - Data length: {result['data_length']}")
            else:
                print("  ⚠️ No data found for JSONB test (this might be OK)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Data types test error: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        with db_config.get_cursor() as (cursor, conn):
            # Delete test user and related data (CASCADE should handle the rest)
            cursor.execute("DELETE FROM users WHERE username = 'testuser_postgres'")
            conn.commit()
            print("  ✅ Test data cleaned up!")
        
    except Exception as e:
        print(f"  ⚠️ Cleanup error (might be OK): {e}")

def display_system_info():
    """Display system and database information"""
    print("\n📊 System Information:")
    
    try:
        with db_config.get_cursor() as (cursor, conn):
            # PostgreSQL version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()['version']
            print(f"  🐘 PostgreSQL Version: {version.split(',')[0]}")
            
            # Database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size = cursor.fetchone()['size']
            print(f"  💾 Database Size: {size}")
            
            # Current connections
            cursor.execute("""
                SELECT count(*) as connections 
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            connections = cursor.fetchone()['connections']
            print(f"  🔗 Active Connections: {connections}")
            
    except Exception as e:
        print(f"  ⚠️ Could not get system info: {e}")

def main():
    """Main test function"""
    print("🚀 PostgreSQL Setup Test for CutieChatter")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Table Creation", test_table_creation),
        ("Basic Operations", test_basic_operations),
        ("Data Types", test_data_types),
    ]
    
    for test_name, test_func in tests:
        if not test_func():
            all_tests_passed = False
            print(f"\n❌ {test_name} test failed!")
            break
    
    # Display system info
    display_system_info()
    
    # Cleanup
    cleanup_test_data()
    
    print("\n" + "=" * 50)
    
    if all_tests_passed:
        print("🎉 All tests passed! PostgreSQL setup is working correctly.")
        print("\n📋 Next steps:")
        print("  1. Run 'python generate_dummy_data.py' to create sample data")
        print("  2. Start your CutieChatter application")
        print("  3. Test user registration and login")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check database credentials in database_config.py")
        print("  3. Verify database 'cutiechatter' exists")
        print("  4. Check the migration_guide.md for detailed setup")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1) 