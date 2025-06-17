# auth_postgresql.py - Backend Autentikasi untuk CutieChatter dengan PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import secrets
import smtplib
import os
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from database_config import db_config

class AuthManager:
    def __init__(self):
        # Test and create database if needed
        db_config.create_database_if_not_exists()
        db_config.test_connection()
        self.init_database()
        
    def init_database(self):
        """Initialize database tables"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                # Users table
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
                
                # Chat data table (untuk user yang login)
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
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_chats_user_id ON user_chats(user_id)')
                
                conn.commit()
                print("✅ Database initialized successfully")
                
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password minimal 6 karakter"
        if not re.search(r'[A-Za-z]', password):
            return False, "Password harus mengandung huruf"
        if not re.search(r'[0-9]', password):
            return False, "Password harus mengandung angka"
        return True, "Password valid"
    
    def validate_username(self, username):
        """Validate username"""
        if len(username) < 3:
            return False, "Username minimal 3 karakter"
        if len(username) > 20:
            return False, "Username maksimal 20 karakter"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username hanya boleh huruf, angka, dan underscore"
        return True, "Username valid"
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password, password_hash, salt):
        """Verify password against hash"""
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return computed_hash.hex() == password_hash
    
    def generate_token(self, length=32):
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def register_user(self, username, email, password, confirm_password):
        """Register new user"""
        try:
            # Validation
            if password != confirm_password:
                return {"success": False, "message": "Password dan konfirmasi password tidak sama"}
            
            username_valid, username_msg = self.validate_username(username)
            if not username_valid:
                return {"success": False, "message": username_msg}
            
            if not self.validate_email(email):
                return {"success": False, "message": "Format email tidak valid"}
            
            password_valid, password_msg = self.validate_password(password)
            if not password_valid:
                return {"success": False, "message": password_msg}
            
            with db_config.get_cursor() as (cursor, conn):
                # Check if username or email already exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                if cursor.fetchone():
                    return {"success": False, "message": "Username atau email sudah terdaftar"}
                
                # Hash password
                password_hash, salt = self.hash_password(password)
                
                # Generate verification token
                verification_token = self.generate_token()
                
                # Insert user
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, salt, verification_token, is_verified)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (username, email, password_hash, salt, verification_token, True))  # Auto-verified for demo
                
                user_id = cursor.fetchone()['id']
                conn.commit()
                
                print(f"✅ User registered: {username} ({email})")
                
                return {
                    "success": True, 
                    "message": "Akun berhasil dibuat! Silakan login.",
                    "user_id": user_id
                }
            
        except Exception as e:
            print(f"❌ Error registering user: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def login_user(self, username_or_email, password):
        """Login user"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                # Find user by username or email
                cursor.execute('''
                    SELECT id, username, email, password_hash, salt, is_verified
                    FROM users 
                    WHERE username = %s OR email = %s
                ''', (username_or_email, username_or_email))
                
                user = cursor.fetchone()
                if not user:
                    return {"success": False, "message": "Username/email atau password salah"}
                
                # Convert RealDictRow to dict and extract values
                user_dict = dict(user)
                user_id = user_dict['id']
                username = user_dict['username']
                email = user_dict['email']
                password_hash = user_dict['password_hash']
                salt = user_dict['salt']
                is_verified = user_dict['is_verified']
                
                # Verify password
                if not self.verify_password(password, password_hash, salt):
                    return {"success": False, "message": "Username/email atau password salah"}
                
                # Create session
                session_token = self.generate_token()
                expires_at = datetime.now() + timedelta(days=30)  # 30 days
                
                cursor.execute('''
                    INSERT INTO sessions (user_id, session_token, expires_at)
                    VALUES (%s, %s, %s)
                ''', (user_id, session_token, expires_at))
                
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
                ''', (user_id,))
                
                conn.commit()
                
                print(f"✅ User logged in: {username}")
                
                return {
                    "success": True,
                    "message": "Login berhasil!",
                    "session_token": session_token,
                    "user": {
                        "id": user_id,
                        "username": username,
                        "email": email
                    }
                }
            
        except Exception as e:
            print(f"❌ Error logging in user: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def verify_session(self, session_token):
        """Verify session token"""
        try:
            if not session_token:
                return {"valid": False, "user": None}
            
            with db_config.get_cursor() as (cursor, conn):
                cursor.execute('''
                    SELECT s.user_id, s.expires_at, u.username, u.email
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = %s AND s.is_active = TRUE
                ''', (session_token,))
                
                result = cursor.fetchone()
                if not result:
                    return {"valid": False, "user": None}
                
                # Convert RealDictRow to dict and extract values
                result_dict = dict(result)
                user_id = result_dict['user_id']
                expires_at = result_dict['expires_at']
                username = result_dict['username']
                email = result_dict['email']
                
                if datetime.now() > expires_at:
                    # Session expired, deactivate it
                    cursor.execute('''
                        UPDATE sessions SET is_active = FALSE WHERE session_token = %s
                    ''', (session_token,))
                    conn.commit()
                    return {"valid": False, "user": None}
                
                return {
                    "valid": True,
                    "user": {
                        "id": user_id,
                        "username": username,
                        "email": email
                    }
                }
            
        except Exception as e:
            print(f"❌ Error verifying session: {e}")
            return {"valid": False, "user": None}
    
    def logout_user(self, session_token):
        """Logout user (deactivate session)"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                cursor.execute('''
                    UPDATE sessions SET is_active = FALSE WHERE session_token = %s
                ''', (session_token,))
                
                conn.commit()
                
                return {"success": True, "message": "Logout berhasil"}
            
        except Exception as e:
            print(f"❌ Error logging out user: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def initiate_password_reset(self, email):
        """Initiate password reset process"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                # Check if email exists
                cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if not user:
                    # Don't reveal whether email exists or not
                    return {"success": True, "message": "Jika email terdaftar, link reset password telah dikirim."}
                
                # Convert RealDictRow to dict and extract values
                user_dict = dict(user)
                user_id = user_dict['id']
                username = user_dict['username']
                
                # Generate reset token
                reset_token = self.generate_token()
                expires_at = datetime.now() + timedelta(hours=1)  # 1 hour
                
                cursor.execute('''
                    UPDATE users 
                    SET reset_token = %s, reset_token_expires = %s
                    WHERE id = %s
                ''', (reset_token, expires_at, user_id))
                
                conn.commit()
                
                print(f"✅ Password reset initiated for: {email}")
                print(f"🔑 Reset token (for demo): {reset_token}")
                
                return {
                    "success": True, 
                    "message": "Jika email terdaftar, link reset password telah dikirim.",
                    "reset_token": reset_token  # Only for demo - remove in production
                }
            
        except Exception as e:
            print(f"❌ Error initiating password reset: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def reset_password(self, reset_token, new_password, confirm_password):
        """Reset password using token"""
        try:
            if new_password != confirm_password:
                return {"success": False, "message": "Password dan konfirmasi password tidak sama"}
            
            password_valid, password_msg = self.validate_password(new_password)
            if not password_valid:
                return {"success": False, "message": password_msg}
            
            with db_config.get_cursor() as (cursor, conn):
                # Verify reset token
                cursor.execute('''
                    SELECT id, username, reset_token_expires
                    FROM users 
                    WHERE reset_token = %s
                ''', (reset_token,))
                
                user = cursor.fetchone()
                if not user:
                    return {"success": False, "message": "Token reset tidak valid"}
                
                # Convert RealDictRow to dict and extract values
                user_dict = dict(user)
                user_id = user_dict['id']
                username = user_dict['username']
                expires_at = user_dict['reset_token_expires']
                
                if datetime.now() > expires_at:
                    return {"success": False, "message": "Token reset telah kadaluarsa"}
                
                # Hash new password
                password_hash, salt = self.hash_password(new_password)
                
                # Update password and clear reset token
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = %s, salt = %s, reset_token = NULL, reset_token_expires = NULL
                    WHERE id = %s
                ''', (password_hash, salt, user_id))
                
                # Deactivate all sessions for security
                cursor.execute('''
                    UPDATE sessions SET is_active = FALSE WHERE user_id = %s
                ''', (user_id,))
                
                conn.commit()
                
                print(f"✅ Password reset successful for: {username}")
                
                return {"success": True, "message": "Password berhasil direset. Silakan login dengan password baru."}
            
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def save_user_chat_data(self, user_id, chat_data):
        """Save user's chat data to database"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                # Check if user chat data exists
                cursor.execute("SELECT id FROM user_chats WHERE user_id = %s", (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute('''
                        UPDATE user_chats 
                        SET chat_data = %s, updated_at = CURRENT_TIMESTAMP 
                        WHERE user_id = %s
                    ''', (json.dumps(chat_data), user_id))
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO user_chats (user_id, chat_id, chat_data)
                        VALUES (%s, %s, %s)
                    ''', (user_id, f"user_{user_id}_chats", json.dumps(chat_data)))
                
                conn.commit()
                
                return {"success": True, "message": "Chat data saved"}
            
        except Exception as e:
            print(f"❌ Error saving chat data: {e}")
            return {"success": False, "message": f"Error saving data: {str(e)}"}
    
    def load_user_chat_data(self, user_id):
        """Load user's chat data from database"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                cursor.execute("SELECT chat_data FROM user_chats WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return {"success": True, "data": result['chat_data']}
                else:
                    return {"success": True, "data": []}  # Empty chat data for new users
                
        except Exception as e:
            print(f"❌ Error loading chat data: {e}")
            return {"success": False, "message": f"Error loading data: {str(e)}", "data": []}
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                cursor.execute('''
                    SELECT username, email, created_at, last_login
                    FROM users WHERE id = %s
                ''', (user_id,))
                
                user_data = cursor.fetchone()
                if not user_data:
                    return {"success": False, "message": "User not found"}
                
                username, email, created_at, last_login = user_data
                
                # Get chat statistics
                cursor.execute("SELECT chat_data FROM user_chats WHERE user_id = %s", (user_id,))
                chat_result = cursor.fetchone()
                
                chat_stats = {"total_chats": 0, "total_messages": 0}
                if chat_result and chat_result['chat_data']:
                    try:
                        chats = chat_result['chat_data']
                        if isinstance(chats, list):
                            chat_stats["total_chats"] = len(chats)
                            chat_stats["total_messages"] = sum(len(chat.get("messages", [])) for chat in chats)
                    except:
                        pass
                
                return {
                    "success": True,
                    "stats": {
                        "username": username,
                        "email": email,
                        "joined": created_at.isoformat() if created_at else None,
                        "last_login": last_login.isoformat() if last_login else None,
                        **chat_stats
                    }
                }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            with db_config.get_cursor() as (cursor, conn):
                cursor.execute('''
                    UPDATE sessions 
                    SET is_active = FALSE 
                    WHERE expires_at < NOW() AND is_active = TRUE
                ''')
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    print(f"🧹 Cleaned up {rows_affected} expired sessions")
                
        except Exception as e:
            print(f"❌ Error cleaning up sessions: {e}")

# Testing function
def test_auth_system():
    """Test the authentication system"""
    print("🧪 Testing PostgreSQL Authentication System...")
    
    auth = AuthManager()
    
    # Test user registration
    result = auth.register_user("testuser", "test@example.com", "password123", "password123")
    print(f"Registration: {result}")
    
    # Test login
    result = auth.login_user("testuser", "password123")
    print(f"Login: {result}")
    
    if result.get("success"):
        session_token = result["session_token"]
        
        # Test session verification
        result = auth.verify_session(session_token)
        print(f"Session verification: {result}")
        
        # Test logout
        result = auth.logout_user(session_token)
        print(f"Logout: {result}")
    
    print("✅ Authentication system test completed!")

if __name__ == "__main__":
    test_auth_system() 