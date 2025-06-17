# setup_supabase.py - Set up Supabase database and migrate data
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseSetup:
    """Set up Supabase database and optionally migrate from local PostgreSQL"""
    
    def __init__(self):
        # Local PostgreSQL configuration (for migration)
        self.local_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'cutiechatter',
            'user': 'baechu',
            'password': 'baechu'
        }
        
        # Supabase configuration (from environment variables)
        self.supabase_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 6543)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': os.getenv('DB_SSLMODE', 'require')
        }
        
        print("🚀 Supabase Setup Tool")
        print("=" * 50)
    
    def test_supabase_connection(self):
        """Test Supabase connection"""
        print("🔍 Testing Supabase connection...")
        
        try:
            conn = psycopg2.connect(**self.supabase_config)
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
            conn.close()
            print("✅ Supabase connection successful!")
            print(f"   Database: {self.supabase_config['database']}")
            print(f"   Host: {self.supabase_config['host']}")
            print(f"   User: {self.supabase_config['user']}")
            return True
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
            print("💡 Please check your .env file and Supabase credentials")
            return False
    
    def create_tables_on_supabase(self):
        """Create all necessary tables on Supabase"""
        print("\n🔧 Creating tables on Supabase...")
        
        try:
            conn = psycopg2.connect(**self.supabase_config)
            cursor = conn.cursor()
            
            # Users table
            print("  📋 Creating users table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(20) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_token VARCHAR(255),
                    reset_token VARCHAR(255),
                    reset_token_expires TIMESTAMP,
                    profile_data JSONB DEFAULT '{}',
                    chat_preferences JSONB DEFAULT '{}'
                )
            ''')
            
            # Sessions table
            print("  📋 Creating sessions table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Chat data table
            print("  📋 Creating user_chats table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    chat_id VARCHAR(255) NOT NULL,
                    chat_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            print("  📋 Creating indexes...")
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_chats_user_id ON user_chats(user_id)')
            
            conn.commit()
            print("✅ All tables created successfully on Supabase!")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    def test_local_connection(self):
        """Test local PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**self.local_config)
            conn.close()
            return True
        except Exception as e:
            print(f"ℹ️  Local PostgreSQL not available: {e}")
            return False
    
    def migrate_data_from_local(self):
        """Migrate data from local PostgreSQL to Supabase"""
        print("\n📦 Checking for local data to migrate...")
        
        if not self.test_local_connection():
            print("ℹ️  No local PostgreSQL database found. Skipping migration.")
            return True
        
        print("📦 Migrating data from local PostgreSQL to Supabase...")
        
        tables_to_migrate = ['users', 'sessions', 'user_chats']
        
        try:
            # Connect to both databases
            local_conn = psycopg2.connect(**self.local_config)
            supabase_conn = psycopg2.connect(**self.supabase_config)
            
            local_cursor = local_conn.cursor(cursor_factory=RealDictCursor)
            supabase_cursor = supabase_conn.cursor()
            
            total_migrated = 0
            
            for table in tables_to_migrate:
                print(f"\n  📋 Migrating table: {table}")
                
                # Get data from local database
                try:
                    local_cursor.execute(f"SELECT * FROM {table}")
                    rows = local_cursor.fetchall()
                except Exception as e:
                    print(f"    ⚠️  Table {table} not found in local database, skipping...")
                    continue
                
                if not rows:
                    print(f"    ℹ️  No data found in {table}")
                    continue
                
                # Clear existing data in Supabase (optional - remove if you want to append)
                try:
                    supabase_cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                    print(f"    🧹 Cleared existing data in {table}")
                except Exception as e:
                    print(f"    ℹ️  Could not clear table {table}: {e}")
                
                # Get column names
                columns = list(rows[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)
                
                # Insert data into Supabase
                insert_query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
                
                migrated_count = 0
                for row in rows:
                    try:
                        values = []
                        for col in columns:
                            value = row[col]
                            # Handle JSONB fields - convert dict/list to Json object
                            if col in ['profile_data', 'chat_preferences', 'chat_data']:
                                if isinstance(value, (dict, list)):
                                    value = Json(value)
                                elif isinstance(value, str):
                                    # If it's a string, try to parse it as JSON
                                    try:
                                        import json
                                        parsed_value = json.loads(value)
                                        value = Json(parsed_value)
                                    except:
                                        # If parsing fails, treat as regular string
                                        pass
                            values.append(value)
                        
                        supabase_cursor.execute(insert_query, values)
                        migrated_count += 1
                    except Exception as e:
                        print(f"    ⚠️  Error inserting row in {table}: {e}")
                        print(f"    📋 Row data: {dict(row)}")
                        # Rollback the current transaction and start a new one
                        supabase_conn.rollback()
                
                # Commit after each table
                try:
                    supabase_conn.commit()
                    print(f"    ✅ Migrated {migrated_count} rows from {table}")
                    total_migrated += migrated_count
                except Exception as e:
                    print(f"    ❌ Error committing {table}: {e}")
                    supabase_conn.rollback()
            
            # Close connections
            local_conn.close()
            supabase_conn.close()
            
            if total_migrated > 0:
                print(f"\n🎉 Migration completed! Total rows migrated: {total_migrated}")
            else:
                print(f"\nℹ️  No data was migrated")
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
    
    def verify_setup(self):
        """Verify that the setup was successful"""
        print("\n🔍 Verifying Supabase setup...")
        
        try:
            conn = psycopg2.connect(**self.supabase_config)
            cursor = conn.cursor()
            
            # Check if tables exist
            tables = ['users', 'sessions', 'user_chats']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📊 {table}: {count} rows")
            
            conn.close()
            print("✅ Supabase setup verification complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False
    
    def run_setup(self, migrate_data=True):
        """Run the complete Supabase setup process"""
        print("🚀 Starting Supabase setup process...")
        print("This will:")
        print("  1. Test Supabase connection")
        print("  2. Create tables on Supabase")
        if migrate_data:
            print("  3. Migrate data from local PostgreSQL (if available)")
        print("  4. Verify the setup")
        print()
        
        # Step 1: Test Supabase connection
        if not self.test_supabase_connection():
            print("❌ Setup aborted due to connection issues")
            return False
        
        # Step 2: Create tables
        if not self.create_tables_on_supabase():
            print("❌ Setup aborted due to table creation issues")
            return False
        
        # Step 3: Migrate data (optional)
        if migrate_data:
            if not self.migrate_data_from_local():
                print("⚠️  Data migration had issues, but continuing...")
        
        # Step 4: Verify setup
        if not self.verify_setup():
            print("⚠️  Setup verification had issues")
            return False
        
        print("\n🎉 Supabase setup completed successfully!")
        print("💡 Next steps:")
        print("   1. Run: python generate_dummy_data.py")
        print("   2. Test your application with Supabase")
        print("   3. Your app is now using cloud PostgreSQL!")
        
        return True

def main():
    """Main function"""
    print("🔧 CutieChatter Supabase Setup Tool")
    print("This tool will set up your Supabase database and migrate existing data")
    print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your Supabase credentials.")
        return
    
    # Check if password is set
    password = os.getenv('DB_PASSWORD')
    if not password or password in ['YOUR-PASSWORD-HERE', 'YOUR-ACTUAL-PASSWORD-HERE']:
        print("❌ Database password not configured!")
        print("Please update your .env file with your actual Supabase password.")
        return
    
    setup = SupabaseSetup()
    
    # Ask user if they want to migrate data
    print("Do you want to migrate data from local PostgreSQL? (y/n): ", end="")
    try:
        migrate = input().lower().startswith('y')
    except:
        migrate = True  # Default to yes if running in script
    
    setup.run_setup(migrate_data=migrate)

if __name__ == "__main__":
    main() 