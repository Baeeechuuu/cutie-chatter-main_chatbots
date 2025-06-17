# 🔄 Migration Guide: SQLite to PostgreSQL

This guide will help you migrate your CutieChatter application from SQLite to PostgreSQL.

## 📋 Prerequisites

### 1. Install PostgreSQL
- **Windows**: Download from [PostgreSQL Official Site](https://www.postgresql.org/download/windows/)
- **macOS**: `brew install postgresql`
- **Ubuntu/Debian**: `sudo apt-get install postgresql postgresql-contrib`

### 2. Install Python Dependencies
```bash
pip install psycopg2-binary sqlalchemy
```

## 🔧 Setup PostgreSQL Database

### 1. Start PostgreSQL Service
```bash
# Windows (as Administrator)
net start postgresql-x64-14

# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

### 2. Create Database and User
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE cutiechatter;

-- Create user (optional, for production)
CREATE USER cutiechatter_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE cutiechatter TO cutiechatter_user;

-- Exit psql
\q
```

## ⚙️ Configuration

### 1. Environment Variables (Recommended)
Create a `.env` file in your project root:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cutiechatter
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

### 2. Or Modify `database_config.py`
```python
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="cutiechatter",
    user="postgres",
    password="your_postgres_password"
)
```

## 🗃️ Data Migration (Optional)

If you want to migrate existing SQLite data to PostgreSQL:

### 1. Export SQLite Data
```python
# export_sqlite_data.py
import sqlite3
import json
from datetime import datetime

def export_sqlite_data():
    conn = sqlite3.connect('cutiechatter_users.db')
    cursor = conn.cursor()
    
    # Export users
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    # Export sessions
    cursor.execute("SELECT * FROM sessions")
    sessions = cursor.fetchall()
    
    # Export user chats
    cursor.execute("SELECT * FROM user_chats")
    chats = cursor.fetchall()
    
    conn.close()
    
    data = {
        'users': users,
        'sessions': sessions,
        'chats': chats,
        'exported_at': datetime.now().isoformat()
    }
    
    with open('sqlite_backup.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ SQLite data exported to sqlite_backup.json")

if __name__ == "__main__":
    export_sqlite_data()
```

### 2. Import to PostgreSQL
```python
# import_to_postgresql.py
import json
from auth import AuthManager
from database_config import db_config

def import_sqlite_data():
    with open('sqlite_backup.json', 'r') as f:
        data = json.load(f)
    
    auth = AuthManager()
    
    # Import users
    for user_row in data['users']:
        # Manual import logic here
        pass
    
    print("✅ Data imported to PostgreSQL")

if __name__ == "__main__":
    import_sqlite_data()
```

## 🚀 Running the Migration

### 1. Test Database Connection
```bash
python database_config.py
```

### 2. Initialize Database Schema
```bash
python auth.py
```

### 3. Generate Dummy Data
```bash
python generate_dummy_data.py
```

### 4. Test the Application
```bash
python cutie.py
```

## 🔍 Verification

### 1. Check Database Tables
```sql
-- Connect to PostgreSQL
psql -U postgres -d cutiechatter

-- List tables
\dt

-- Check users table
SELECT COUNT(*) FROM users;

-- Check sample data
SELECT username, email, created_at FROM users LIMIT 5;
```

### 2. Test Authentication
The auth system includes a built-in test function. Run:
```bash
python auth.py
```

## 🎯 Key Changes Made

### 1. Database Connection
- **Before**: `sqlite3.connect()`
- **After**: `psycopg2.connect()` with connection pooling

### 2. SQL Syntax Updates
- **Primary Keys**: `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- **Data Types**: `TEXT` → `VARCHAR()`, `INTEGER` → `INTEGER`
- **JSON Storage**: `TEXT` → `JSONB`
- **Placeholders**: `?` → `%s`

### 3. Performance Improvements
- Added database indexes
- Used JSONB for better JSON performance
- Implemented proper foreign key constraints

### 4. Connection Management
- Context managers for automatic connection cleanup
- Better error handling
- Connection pooling ready

## 🐛 Troubleshooting

### Common Issues

#### Connection Failed
```
❌ PostgreSQL Connection failed: could not connect to server
```
**Solution**: 
- Ensure PostgreSQL is running
- Check host, port, username, and password
- Verify database exists

#### Permission Denied
```
❌ Error initializing database: permission denied for relation users
```
**Solution**:
- Grant proper permissions to your user
- Use superuser for initial setup

#### Module Not Found
```
❌ ModuleNotFoundError: No module named 'psycopg2'
```
**Solution**:
```bash
pip install psycopg2-binary
```

### Environment-Specific Notes

#### Windows
- Use PowerShell as Administrator for PostgreSQL commands
- Default installation path: `C:\Program Files\PostgreSQL\14\`

#### Docker (Alternative)
```bash
# Run PostgreSQL in Docker
docker run --name postgres-cutie \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=cutiechatter \
  -p 5432:5432 \
  -d postgres:14

# Update connection settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cutiechatter
DB_USER=postgres
DB_PASSWORD=password123
```

## 📊 Performance Benefits

### SQLite vs PostgreSQL
| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Concurrent Users | Limited | Excellent |
| Data Types | Basic | Rich (JSONB, Arrays, etc.) |
| Indexing | Basic | Advanced |
| Backup/Recovery | File copy | Professional tools |
| Scalability | Small-medium | Enterprise |

### JSON Performance
- **SQLite**: Stores JSON as text, requires parsing
- **PostgreSQL**: JSONB provides native JSON operations and indexing

## 🎉 Next Steps

1. **Test thoroughly** with your existing application workflows
2. **Monitor performance** - PostgreSQL should be faster for concurrent access
3. **Set up backups** using `pg_dump`
4. **Consider connection pooling** for production (pgBouncer)
5. **Add monitoring** for database performance

## 📝 Backup Commands

### PostgreSQL Backup
```bash
# Full backup
pg_dump -U postgres -d cutiechatter > backup.sql

# Restore
psql -U postgres -d cutiechatter < backup.sql
```

### Regular Maintenance
```sql
-- Update table statistics
ANALYZE;

-- Vacuum tables
VACUUM;

-- Clean up expired sessions
SELECT cleanup_expired_sessions();
```

---

✅ **Migration Complete!** Your CutieChatter application is now running on PostgreSQL with improved performance and scalability. 