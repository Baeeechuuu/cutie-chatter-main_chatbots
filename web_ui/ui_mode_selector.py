# ui_mode_selector.py

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
import os
import sys

# Check if WebEngine is available
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from web_ui import WebInterface
    WEBENGINE_AVAILABLE = True
except ImportError:
    print("WebEngine not available. Web UI will be disabled.")
    WEBENGINE_AVAILABLE = False


class UIModeSelector:
    """Helper class to manage UI mode switching"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_mode = "desktop"
        self.web_interface = None
        self.original_central_widget = None
        
    def add_ui_switch_button(self, layout):
        """Add UI mode switch button to existing layout"""
        if not WEBENGINE_AVAILABLE:
            return None
            
        # Create UI switch button
        ui_switch_button = QPushButton(self.main_window)
        ui_switch_button.setObjectName("ui_switch_button")
        ui_switch_button.setText("🌐")
        ui_switch_button.setToolTip("Switch to Web UI")
        ui_switch_button.setStyleSheet("""
            QPushButton#ui_switch_button {
                background-color: #4a4a4a;
                font-size: 16px;
                min-width: 40px;
                min-height: 40px;
                border-radius: 20px;
            }
            QPushButton#ui_switch_button:hover {
                background-color: #5a5a5a;
            }
        """)
        
        ui_switch_button.clicked.connect(self.toggle_ui_mode)
        layout.addWidget(ui_switch_button)
        
        return ui_switch_button
    
    def toggle_ui_mode(self):
        """Toggle between desktop and web UI"""
        if self.current_mode == "desktop":
            self.switch_to_web_ui()
        else:
            self.switch_to_desktop_ui()
    
    def switch_to_web_ui(self):
        """Switch to web-based UI"""
        if not WEBENGINE_AVAILABLE:
            print("WebEngine not available!")
            return
            
        print("Switching to Web UI...")
        
        # Store original central widget
        self.original_central_widget = self.main_window.centralWidget()
        
        # Create web interface
        if not self.web_interface:
            self.web_interface = WebInterface(self.main_window)
        
        # Set web interface as central widget
        self.main_window.setCentralWidget(self.web_interface)
        
        # Update window title
        self.main_window.setWindowTitle("CutieChatter - Web UI")
        
        self.current_mode = "web"
        print("✅ Switched to Web UI")
    
    def switch_to_desktop_ui(self):
        """Switch back to desktop UI"""
        if not self.original_central_widget:
            print("No original widget to restore!")
            return
            
        print("Switching to Desktop UI...")
        
        # Restore original central widget
        self.main_window.setCentralWidget(self.original_central_widget)
        
        # Update window title
        self.main_window.setWindowTitle("CutieChatter")
        
        self.current_mode = "desktop"
        print("✅ Switched to Desktop UI")
    
    def is_web_mode(self):
        """Check if currently in web mode"""
        return self.current_mode == "web"
    
    def get_chat_widget(self):
        """Get the appropriate chat widget based on current mode"""
        if self.is_web_mode() and self.web_interface:
            return self.web_interface.bridge
        else:
            return getattr(self.main_window, 'chat_widget', None)