# auth_bridge.py - Bridge untuk integrasi autentikasi dengan cutie.py

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
import json
import os
from auth import AuthManager

class AuthBridge(QObject):
    """Bridge untuk komunikasi antara JavaScript auth dan Python backend"""
    
    # Signals untuk komunikasi dengan main app
    loginSuccessful = pyqtSignal(dict)  # Emit ketika login berhasil
    logoutRequested = pyqtSignal()      # Emit ketika logout
    redirectToMain = pyqtSignal()       # Emit untuk redirect ke main app

    authError = pyqtSignal(str)         # DITAMBAHKAN: Emit ketika error auth
    showAuthWindow = pyqtSignal()       # DITAMBAHKAN: Emit untuk show auth window
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = AuthManager()
        self.current_user = None
        self.current_session = None
        print("✅ AuthBridge initialized")
    
    # DITAMBAHKAN: Method login untuk JavaScript
    @pyqtSlot(str, str, result=str)
    def login(self, username, password):
        """Handle login request - alias for signIn"""
        return self.signIn(username, password)
    
    # DITAMBAHKAN: Method register untuk JavaScript
    @pyqtSlot(str, str, str, str, result=str)
    def register(self, username, email, password, confirm_password):
        """Handle register request - alias for signUp"""
        return self.signUp(username, email, password, confirm_password)
    
    # DITAMBAHKAN: Method continueAsGuest untuk JavaScript
    @pyqtSlot()
    def continueAsGuest(self):
        """Handle continue as guest request"""
        try:
            print("👤 Guest mode activated")
            
            # Clear any existing auth data
            self.current_user = None
            self.current_session = None
            
            # Set parent app to guest mode
            if hasattr(self.parent_app, 'is_guest_mode'):
                self.parent_app.is_guest_mode = True
                self.parent_app.current_user = None
            
            # Emit signal untuk redirect ke main app
            self.redirectToMain.emit()
            
        except Exception as e:
            print(f"❌ Error in continueAsGuest: {e}")
            self.authError.emit(f"Terjadi kesalahan: {str(e)}")
    
    @pyqtSlot(str, str, result=str)
    def signIn(self, username, password):
        """Handle sign in request"""
        try:
            print(f"🔐 Sign in attempt for: {username}")
            
            result = self.auth_manager.login_user(username, password)
            
            if result["success"]:
                # Store current user and session
                self.current_user = result["user"]
                self.current_session = result["session_token"]
                
                # Load user's chat data
                chat_data_result = self.auth_manager.load_user_chat_data(self.current_user["id"])
                if chat_data_result["success"]:
                    result["chat_data"] = chat_data_result["data"]
                else:
                    result["chat_data"] = []
                
                # Emit signal untuk main app
                self.loginSuccessful.emit({
                    "user": self.current_user,
                    "session": self.current_session,
                    "chat_data": result.get("chat_data", [])
                })
                
                print(f"✅ Sign in successful for: {username}")
            else:
                print(f"❌ Sign in failed for: {username} - {result['message']}")
                # DITAMBAHKAN: Emit auth error signal
                self.authError.emit(result["message"])
            
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error in signIn: {e}")
            error_msg = f"Terjadi kesalahan: {str(e)}"
            self.authError.emit(error_msg)
            return json.dumps({
                "success": False,
                "message": error_msg
            })
    
    @pyqtSlot(str, str, str, str, result=str)
    def signUp(self, username, email, password, confirm_password):
        """Handle sign up request"""
        try:
            print(f"📝 Sign up attempt for: {username} ({email})")
            
            result = self.auth_manager.register_user(username, email, password, confirm_password)
            
            if result["success"]:
                print(f"✅ Sign up successful for: {username}")
            else:
                print(f"❌ Sign up failed for: {username} - {result['message']}")
                # DITAMBAHKAN: Emit auth error signal
                self.authError.emit(result["message"])
            
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error in signUp: {e}")
            error_msg = f"Terjadi kesalahan: {str(e)}"
            self.authError.emit(error_msg)
            return json.dumps({
                "success": False,
                "message": error_msg
            })
    
    @pyqtSlot(str, result=str)
    def forgotPassword(self, email):
        """Handle forgot password request"""
        try:
            print(f"🔄 Password reset request for: {email}")
            
            result = self.auth_manager.initiate_password_reset(email)
            
            if result["success"]:
                print(f"✅ Password reset initiated for: {email}")
            else:
                print(f"❌ Password reset failed for: {email}")
                # DITAMBAHKAN: Emit auth error signal
                self.authError.emit(result["message"])
            
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error in forgotPassword: {e}")
            error_msg = f"Terjadi kesalahan: {str(e)}"
            self.authError.emit(error_msg)
            return json.dumps({
                "success": False,
                "message": error_msg
            })
    
    @pyqtSlot(str, str, str, result=str)
    def resetPassword(self, reset_token, new_password, confirm_password):
        """Handle password reset request"""
        try:
            print(f"🔑 Password reset attempt with token: {reset_token[:10]}...")
            
            result = self.auth_manager.reset_password(reset_token, new_password, confirm_password)
            
            if result["success"]:
                print("✅ Password reset successful")
            else:
                print(f"❌ Password reset failed: {result['message']}")
            
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error in resetPassword: {e}")
            return json.dumps({
                "success": False,
                "message": f"Terjadi kesalahan: {str(e)}"
            })
    
    @pyqtSlot(str, result=str)
    def verifySession(self, session_token):
        """Verify session token"""
        try:
            result = self.auth_manager.verify_session(session_token)
            
            if result["valid"]:
                self.current_user = result["user"]
                self.current_session = session_token
            
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error in verifySession: {e}")
            return json.dumps({
                "valid": False,
                "user": None
            })
    
    @pyqtSlot(result=str)
    def logout(self):
        """Handle logout request"""
        try:
            result = {"success": True, "message": "Logout berhasil"}
            
            if self.current_session:
                result = self.auth_manager.logout_user(self.current_session)
            
            # Clear current user and session
            self.current_user = None
            self.current_session = None
            
            # Set parent app to guest mode after logout
            if hasattr(self.parent_app, 'is_guest_mode'):
                self.parent_app.is_guest_mode = True
                self.parent_app.current_user = None
            
            # Emit signal untuk main app
            self.logoutRequested.emit()
            
            print("✅ Logout successful, guest mode activated")
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error in logout: {e}")
            return json.dumps({
                "success": False,
                "message": f"Terjadi kesalahan: {str(e)}"
            })
    
    @pyqtSlot(str)
    def saveChatData(self, chat_data_json):
        """Save user's chat data"""
        try:
            if not self.current_user:
                print("⚠️ No current user, cannot save chat data")
                return
            
            chat_data = json.loads(chat_data_json)
            result = self.auth_manager.save_user_chat_data(self.current_user["id"], chat_data)
            
            if result["success"]:
                print(f"💾 Chat data saved for user: {self.current_user['username']}")
            else:
                print(f"❌ Failed to save chat data: {result['message']}")
                
        except Exception as e:
            print(f"❌ Error saving chat data: {e}")
    
    @pyqtSlot(result=str)
    def loadChatData(self):
        """Load user's chat data"""
        try:
            if not self.current_user:
                return json.dumps({"success": False, "data": []})
            
            result = self.auth_manager.load_user_chat_data(self.current_user["id"])
            print(f"📂 Chat data loaded for user: {self.current_user['username']}")
            
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error loading chat data: {e}")
            return json.dumps({"success": False, "data": []})
    
    @pyqtSlot(result=str)
    def getCurrentUser(self):
        """Get current user info"""
        try:
            if self.current_user:
                return json.dumps({
                    "success": True,
                    "user": self.current_user,
                    "session": self.current_session
                })
            else:
                return json.dumps({
                    "success": False,
                    "user": None,
                    "session": None
                })
                
        except Exception as e:
            print(f"❌ Error getting current user: {e}")
            return json.dumps({
                "success": False,
                "user": None,
                "session": None
            })
    
    @pyqtSlot(result=str)
    def getUserStats(self):
        """Get user statistics"""
        try:
            if not self.current_user:
                return json.dumps({"success": False, "message": "No user logged in"})
            
            result = self.auth_manager.get_user_stats(self.current_user["id"])
            return json.dumps(result)
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return json.dumps({
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    @pyqtSlot()
    def redirectToMainApp(self):
        """Emit signal to redirect to main app"""
        print("🔄 Redirecting to main application...")
        self.redirectToMain.emit()
    
    @pyqtSlot()
    def show_auth_window(self):
        """Show authentication window"""
        try:
            print("🔐 Showing authentication window from JavaScript...")
            self.showAuthWindow.emit()
        except Exception as e:
            print(f"❌ Error showing auth window: {e}")
            self.authError.emit(f"Terjadi kesalahan: {str(e)}")
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.current_user is not None and self.current_session is not None
    
    def get_user_id(self):
        """Get current user ID"""
        return self.current_user["id"] if self.current_user else None
    
    def get_username(self):
        """Get current username"""
        return self.current_user["username"] if self.current_user else None
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            self.auth_manager.cleanup_expired_sessions()
        except Exception as e:
            print(f"❌ Error cleaning up sessions: {e}")