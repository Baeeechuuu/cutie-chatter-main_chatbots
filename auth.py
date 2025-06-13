# auth.py - Backend Autentikasi untuk CutieChatter
import sqlite3
import hashlib
import secrets
import smtplib
import os
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

class AuthManager:
    def __init__(self, db_path="cutiechatter_users.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expires TIMESTAMP,
                profile_data TEXT DEFAULT '{}',
                chat_preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Chat data table (untuk user yang login)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id TEXT NOT NULL,
                chat_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
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
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "message": "Username atau email sudah terdaftar"}
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            # Generate verification token
            verification_token = self.generate_token()
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, verification_token, is_verified)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, verification_token, True))  # Auto-verified for demo
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ User registered: {username} ({email})")
            
            # In a real app, you'd send verification email here
            # self.send_verification_email(email, verification_token)
            
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find user by username or email
            cursor.execute('''
                SELECT id, username, email, password_hash, salt, is_verified
                FROM users 
                WHERE username = ? OR email = ?
            ''', (username_or_email, username_or_email))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {"success": False, "message": "Username/email atau password salah"}
            
            user_id, username, email, password_hash, salt, is_verified = user
            
            # Verify password
            if not self.verify_password(password, password_hash, salt):
                conn.close()
                return {"success": False, "message": "Username/email atau password salah"}
            
            # For demo, we'll skip email verification
            # if not is_verified:
            #     conn.close()
            #     return {"success": False, "message": "Akun belum diverifikasi. Periksa email Anda."}
            
            # Create session
            session_token = self.generate_token()
            expires_at = datetime.now() + timedelta(days=30)  # 30 days
            
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
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
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, s.expires_at, u.username, u.email
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.is_active = TRUE
            ''', (session_token,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"valid": False, "user": None}
            
            user_id, expires_at_str, username, email = result
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            
            if datetime.now() > expires_at:
                # Session expired, deactivate it
                cursor.execute('''
                    UPDATE sessions SET is_active = FALSE WHERE session_token = ?
                ''', (session_token,))
                conn.commit()
                conn.close()
                return {"valid": False, "user": None}
            
            conn.close()
            
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = FALSE WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "Logout berhasil"}
            
        except Exception as e:
            print(f"❌ Error logging out user: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def initiate_password_reset(self, email):
        """Initiate password reset process"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute("SELECT id, username FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                # Don't reveal whether email exists or not
                return {"success": True, "message": "Jika email terdaftar, link reset password telah dikirim."}
            
            user_id, username = user
            
            # Generate reset token
            reset_token = self.generate_token()
            expires_at = datetime.now() + timedelta(hours=1)  # 1 hour
            
            cursor.execute('''
                UPDATE users 
                SET reset_token = ?, reset_token_expires = ?
                WHERE id = ?
            ''', (reset_token, expires_at, user_id))
            
            conn.commit()
            conn.close()
            
            # In a real app, send reset email here
            # self.send_reset_email(email, username, reset_token)
            
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
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verify reset token
            cursor.execute('''
                SELECT id, username, reset_token_expires
                FROM users 
                WHERE reset_token = ?
            ''', (reset_token,))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {"success": False, "message": "Token reset tidak valid"}
            
            user_id, username, expires_at_str = user
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            
            if datetime.now() > expires_at:
                conn.close()
                return {"success": False, "message": "Token reset telah kadaluarsa"}
            
            # Hash new password
            password_hash, salt = self.hash_password(new_password)
            
            # Update password and clear reset token
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, salt = ?, reset_token = NULL, reset_token_expires = NULL
                WHERE id = ?
            ''', (password_hash, salt, user_id))
            
            # Deactivate all sessions for security
            cursor.execute('''
                UPDATE sessions SET is_active = FALSE WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Password reset successful for: {username}")
            
            return {"success": True, "message": "Password berhasil direset. Silakan login dengan password baru."}
            
        except Exception as e:
            print(f"❌ Error resetting password: {e}")
            return {"success": False, "message": f"Terjadi kesalahan: {str(e)}"}
    
    def save_user_chat_data(self, user_id, chat_data):
        """Save user's chat data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert chat data to JSON
            chat_data_json = json.dumps(chat_data)
            
            # Check if user chat data exists
            cursor.execute("SELECT id FROM user_chats WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute('''
                    UPDATE user_chats 
                    SET chat_data = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (chat_data_json, user_id))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO user_chats (user_id, chat_id, chat_data)
                    VALUES (?, ?, ?)
                ''', (user_id, f"user_{user_id}_chats", chat_data_json))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "Chat data saved"}
            
        except Exception as e:
            print(f"❌ Error saving chat data: {e}")
            return {"success": False, "message": f"Error saving data: {str(e)}"}
    
    def load_user_chat_data(self, user_id):
        """Load user's chat data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT chat_data FROM user_chats WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return {"success": True, "data": json.loads(result[0])}
            else:
                return {"success": True, "data": []}  # Empty chat data for new users
                
        except Exception as e:
            print(f"❌ Error loading chat data: {e}")
            return {"success": False, "message": f"Error loading data: {str(e)}", "data": []}
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return {"success": False, "message": "User not found"}
            
            username, email, created_at, last_login = user_data
            
            # Get chat statistics
            cursor.execute("SELECT chat_data FROM user_chats WHERE user_id = ?", (user_id,))
            chat_result = cursor.fetchone()
            
            chat_stats = {"total_chats": 0, "total_messages": 0}
            if chat_result:
                try:
                    chats = json.loads(chat_result[0])
                    chat_stats["total_chats"] = len(chats)
                    chat_stats["total_messages"] = sum(len(chat.get("messages", [])) for chat in chats)
                except:
                    pass
            
            conn.close()
            
            return {
                "success": True,
                "stats": {
                    "username": username,
                    "email": email,
                    "joined": created_at,
                    "last_login": last_login,
                    **chat_stats
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions 
                SET is_active = FALSE 
                WHERE expires_at < datetime('now') AND is_active = TRUE
            ''')
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                print(f"🧹 Cleaned up {rows_affected} expired sessions")
                
        except Exception as e:
            print(f"❌ Error cleaning up sessions: {e}")

# Test the auth manager
if __name__ == "__main__":
    print("🔧 Testing AuthManager...")
    
    auth = AuthManager()
    
    # Test registration
    result = auth.register_user("testuser", "test@example.com", "password123", "password123")
    print(f"Registration: {result}")
    
    # Test login
    result = auth.login_user("testuser", "password123")
    print(f"Login: {result}")
    
    if result["success"]:
        session_token = result["session_token"]
        
        # Test session verification
        verify_result = auth.verify_session(session_token)
        print(f"Session verification: {verify_result}")
        
        # Test logout
        logout_result = auth.logout_user(session_token)
        print(f"Logout: {logout_result}")
    
    print("✅ AuthManager test completed")