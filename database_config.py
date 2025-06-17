# database_config.py - Database Configuration for PostgreSQL (Supabase Compatible)
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables.")
except Exception as e:
    print(f"⚠️  Warning loading .env file: {e}")
    print("Using system environment variables instead.")

class DatabaseConfig:
    """PostgreSQL Database Configuration Manager - Supabase Compatible"""
    
    def __init__(self, host=None, port=None, database=None, user=None, password=None, **kwargs):
        # Load from environment variables first, then fall back to parameters
        self.host = os.getenv('DB_HOST', host or "localhost")
        self.port = int(os.getenv('DB_PORT', port or 5432))
        self.database = os.getenv('DB_NAME', database or "cutiechatter")
        self.user = os.getenv('DB_USER', user or "baechu")
        self.password = os.getenv('DB_PASSWORD', password or "baechu")
        self.sslmode = os.getenv('DB_SSLMODE', 'prefer')  # 'require' for Supabase
        
        # Check if we're using Supabase (based on host)
        self.is_supabase = 'supabase.com' in self.host
        
        if self.is_supabase:
            print(f"🔧 Configuring for Supabase: {self.host}")
        else:
            print(f"🔧 Configuring for local PostgreSQL: {self.host}")
    
    def get_connection_string(self):
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"
    
    def get_connection_params(self):
        """Get connection parameters as dictionary"""
        params = {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
        
        # Add SSL mode for secure connections (especially important for Supabase)
        if self.sslmode:
            params['sslmode'] = self.sslmode
            
        return params
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = psycopg2.connect(**self.get_connection_params())
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get database cursor with context manager"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor, conn
            finally:
                cursor.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    print(f"✅ PostgreSQL Connection successful")
                    print(f"   Database: {self.database}")
                    print(f"   Host: {self.host}:{self.port}")
                    print(f"   User: {self.user}")
                    print(f"   SSL Mode: {self.sslmode}")
                    if self.is_supabase:
                        print(f"   🚀 Connected to Supabase!")
                    print(f"   Version: {version[0]}")
                    return True
        except Exception as e:
            print(f"❌ PostgreSQL Connection failed: {e}")
            if self.is_supabase:
                print("💡 Supabase troubleshooting tips:")
                print("   1. Make sure your password is correct in the .env file")
                print("   2. Check if your Supabase project is active")
                print("   3. Verify the connection pooler is enabled")
                print("   4. Ensure your IP is whitelisted in Supabase settings")
            return False
    
    def create_database_if_not_exists(self):
        """Create database if it doesn't exist (not applicable for Supabase)"""
        if self.is_supabase:
            print("ℹ️  Database creation not needed for Supabase - using default 'postgres' database")
            return True
            
        try:
            # Connect to postgres database to create new database
            temp_params = self.get_connection_params()
            temp_params['database'] = 'postgres'
            
            conn = psycopg2.connect(**temp_params)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                    (self.database,)
                )
                exists = cursor.fetchone()
                
                if not exists:
                    cursor.execute(f'CREATE DATABASE "{self.database}"')
                    print(f"✅ Database '{self.database}' created successfully")
                else:
                    print(f"✅ Database '{self.database}' already exists")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return False

# Global database configuration instance
db_config = DatabaseConfig() 