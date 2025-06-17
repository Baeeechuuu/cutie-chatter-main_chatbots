# test_supabase_connection.py - Test Supabase connection
from database_config import db_config
from auth import AuthManager
import os

def test_supabase_connection():
    """Test the Supabase connection and basic operations"""
    print("🧪 Testing Supabase Connection")
    print("=" * 40)
    
    # Check environment variables
    print("📋 Configuration Check:")
    print(f"  Host: {os.getenv('DB_HOST')}")
    print(f"  Port: {os.getenv('DB_PORT')}")
    print(f"  Database: {os.getenv('DB_NAME')}")
    print(f"  User: {os.getenv('DB_USER')}")
    print(f"  SSL Mode: {os.getenv('DB_SSLMODE')}")
    
    password = os.getenv('DB_PASSWORD')
    if password in [None, '', 'YOUR-PASSWORD-HERE', 'YOUR-ACTUAL-PASSWORD-HERE']:
        print("❌ Please update your .env file with your actual Supabase password!")
        return False
    else:
        print(f"  Password: {'*' * len(password)} (configured)")
    
    print("\n🔍 Testing database connection...")
    
    # Test connection
    if not db_config.test_connection():
        return False
    
    print("\n🔧 Testing table creation...")
    
    # Test authentication system initialization
    try:
        auth = AuthManager()
        print("✅ Authentication system initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing auth system: {e}")
        return False
    
    print("\n🧪 Testing basic operations...")
    
    # Test user registration
    try:
        test_result = auth.register_user(
            "supabase_test_user", 
            "test@supabase.example.com", 
            "password123", 
            "password123"
        )
        print(f"Registration test: {test_result}")
        
        if test_result["success"]:
            # Test login
            login_result = auth.login_user("supabase_test_user", "password123")
            print(f"Login test: {login_result}")
            
            if login_result["success"]:
                print("✅ All tests passed! Supabase is working correctly.")
                return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    return False

if __name__ == "__main__":
    if test_supabase_connection():
        print("\n🎉 Supabase migration successful!")
        print("Your application is now connected to Supabase.")
    else:
        print("\n❌ Supabase connection issues detected.")
        print("Please check your .env configuration and Supabase settings.") 