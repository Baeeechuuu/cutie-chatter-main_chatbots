# Enhanced cutie.py dengan WebEngine Integration

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QMessageBox
)
from PyQt6.QtCore import (
    Qt, 
    QThread,
    QSettings,
    QUrl,
    pyqtSlot,
    QObject,
    pyqtSignal
)
from PyQt6.QtGui import (
    QIcon
)

# Import WebEngine (PENTING!)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# Import dengan error handling yang lebih detail
print("🔍 Starting imports...")

try:
    from transformers import (
        AutoModelForSequenceClassification, 
        AutoModel,
        AutoTokenizer
    )
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers imported successfully")
except ImportError as e:
    print(f"❌ Warning: Transformers not available: {e}")
    TRANSFORMERS_AVAILABLE = False

try:
    import backends
    print(f"✅ backends module imported from: {backends.__file__}")
    
    # Check contents
    available_items = [item for item in dir(backends) if not item.startswith('_')]
    print(f"📋 Available in backends: {available_items}")
    
    from backends import (
        ChatWidget, 
        OllamaWorker, 
        OllamaOCRWorker
    )
    print("✅ ChatWidget, OllamaWorker, OllamaOCRWorker imported successfully")
    BACKENDS_AVAILABLE = True
except ImportError as e:
    print(f"❌ CRITICAL: Backends not available: {e}")
    print("❌ Make sure backends.py is in the same folder as this script!")
    BACKENDS_AVAILABLE = False

try:
    from ocr.docreader import FileSelector
    OCR_AVAILABLE = True
    print("✅ OCR module available")
except ImportError as e:
    print(f"⚠️ Warning: OCR module not available: {e}")
    OCR_AVAILABLE = False

try:
    from sentiment.sentient import (
        EmotionClassifier,
        L2S
    )
    from sentiment.memory.textsimilarity import TextSimilaritySearch
    SENTIMENT_AVAILABLE = True
    print("✅ Sentiment analysis available")
except ImportError as e:
    print(f"⚠️ Warning: Sentiment analysis not available: {e}")
    SENTIMENT_AVAILABLE = False

import os
import re
import sys
import json

try:
    import screeninfo
    SCREENINFO_AVAILABLE = True
    print("✅ screeninfo available")
except ImportError:
    print("⚠️ Warning: screeninfo not available, using default window size")
    SCREENINFO_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
    print("✅ PyTorch available")
except ImportError:
    print("⚠️ Warning: PyTorch not available, sentiment analysis disabled")
    TORCH_AVAILABLE = False

# Test Ollama connection
print("🔍 Testing Ollama connection...")
try:
    import ollama
    print("✅ ollama module imported")
    
    # Test server connection
    try:
        models = ollama.list()
        available_models = [m['name'] for m in models['models']]
        print(f"✅ Ollama server running! Available models: {available_models}")
        
        # Check for DeepSeek
        deepseek_models = [m for m in available_models if 'deepseek' in m.lower()]
        if deepseek_models:
            print(f"🤖 DeepSeek models found: {deepseek_models}")
        else:
            print("❌ No DeepSeek models found! Run: ollama pull deepseek-r1:1.5b")
            
    except Exception as e:
        print(f"❌ Ollama server connection failed: {e}")
        print("❌ Make sure to run: ollama serve")
        
except ImportError as e:
    print(f"❌ ollama module not available: {e}")
    print("❌ Install with: pip install ollama")

print(f"\n📊 Import Summary:")
print(f"   - Backends: {'✅' if BACKENDS_AVAILABLE else '❌'}")
print(f"   - Transformers: {'✅' if TRANSFORMERS_AVAILABLE else '❌'}")
print(f"   - PyTorch: {'✅' if TORCH_AVAILABLE else '❌'}")
print(f"   - OCR: {'✅' if OCR_AVAILABLE else '❌'}")
print(f"   - Sentiment: {'✅' if SENTIMENT_AVAILABLE else '❌'}")
print(f"   - Screeninfo: {'✅' if SCREENINFO_AVAILABLE else '❌'}")
print("")


class ChatBridge(QObject):
    """Bridge untuk komunikasi antara JavaScript dan Python"""
    
    # Signals
    messageReceived = pyqtSignal(str)
    responseReady = pyqtSignal(str)
    streamChunk = pyqtSignal(str)  # Signal untuk streaming
    streamFinished = pyqtSignal(str)  # Signal ketika streaming selesai
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.ollama_worker = None
        self.ollama_thread = None
    
    @pyqtSlot(str, result=str)
    def sendMessage(self, message):
        """Menerima pesan dari JavaScript - DEPRECATED, gunakan sendMessageStreaming"""
        print(f"WARNING: sendMessage called instead of sendMessageStreaming for: {message}")
        return "❌ ERROR: Using deprecated sendMessage. Use streaming instead."
    
    @pyqtSlot(str)
    def sendMessageStreaming(self, message):
        """Send message dengan streaming response LANGSUNG dari DeepSeek-R1"""
        try:
            print(f"🚀 Starting DeepSeek-R1 streaming for: {message}")
            
            if self.parent_app:
                # LANGSUNG ke DeepSeek-R1, TIDAK ADA fallback
                self.parent_app.process_message_streaming(message, self)
            else:
                self.streamFinished.emit("❌ ERROR: Parent app not available")
            
        except Exception as e:
            print(f"❌ Error in DeepSeek-R1 streaming: {e}")
            self.streamFinished.emit(f"❌ Error DeepSeek-R1: {str(e)}")
    
    @pyqtSlot(result=str)
    def getSystemInfo(self):
        """Memberikan info sistem ke JavaScript"""
        info = {
            "transformers_available": TRANSFORMERS_AVAILABLE,
            "backends_available": BACKENDS_AVAILABLE,
            "sentiment_available": SENTIMENT_AVAILABLE,
            "torch_available": TORCH_AVAILABLE
        }
        return json.dumps(info)


class CutieTheCutest(QMainWindow):
    def __init__(self, model_name="deepseek-r1:1.5b"):
        super().__init__()
        self.setWindowTitle("CutieChatter - Desktop Web Hybrid")
        
        # Initialize settings untuk menyimpan preferensi tema
        self.settings = QSettings("CutieChatter", "ThemeSettings")
        self.is_dark_theme = self.settings.value("dark_theme", True, type=bool)
        
        # Safe window geometry setup
        self.setup_window_geometry()
        
        # Initialize variables
        self.model_name = model_name
        self.conversation_history = [
            {
                'role': 'system',
                'content': """You're CutieChatter, your directive should be :
                            1. Playful.
                            2. Personally engaging with the user.
                            3. Maintain a consistent personal tone.
                            4. Avoid responding using double quotation marks.
                            5. Generate natural responses.
                            """
            }
        ]
        self.is_ollama_thread_running = False
        self.ollama_thread = None
        self.ollama_worker = None
        
        # Initialize sentiment analysis components
        self.classifier = None
        self.ModelForSentimentScoring = None
        self.ModelForCS = None
        self.tokenizer = None
        
        # Vector Memory for Attachment Mechanism
        self.ai_features_metadata = []
        self.ai_text_metadata = []
        self.user_features_metadata = []
        self.user_text_metadata = []
        self.cosine_of_text_metadata = []
        
        # Setup Web Engine
        self.setup_web_engine()
        
        # Load models (with error handling)
        self.load_models()

    def setup_window_geometry(self):
        """Setup window geometry with safe fallbacks"""
        try:
            if SCREENINFO_AVAILABLE:
                self.screen_dimension = screeninfo.get_monitors()
                if self.screen_dimension:
                    # Use primary monitor
                    primary_monitor = self.screen_dimension[0]
                    WIN_W = primary_monitor.width
                    WIN_H = primary_monitor.height
                    
                    # Calculate safe window size (80% of screen)
                    window_width = min(int(WIN_W * 0.8), 1400)
                    window_height = min(int(WIN_H * 0.8), 900)
                    
                    # Center the window
                    x = (WIN_W - window_width) // 2
                    y = (WIN_H - window_height) // 2
                    
                    self.setGeometry(x, y, window_width, window_height)
                else:
                    # Fallback if no monitors detected
                    self.setGeometry(100, 100, 1200, 800)
            else:
                # Fallback if screeninfo not available
                self.setGeometry(100, 100, 1200, 800)
                
        except Exception as e:
            print(f"Error setting window geometry: {e}")
            # Safe fallback
            self.setGeometry(100, 100, 1200, 800)

    def setup_web_engine(self):
        """Setup Web Engine untuk load HTML interface"""
        try:
            # Create WebEngine view
            self.web_view = QWebEngineView()
            
            # Setup communication bridge
            self.bridge = ChatBridge(self)
            self.channel = QWebChannel()
            self.channel.registerObject("bridge", self.bridge)
            self.web_view.page().setWebChannel(self.channel)
            
            # Load HTML file
            html_path = os.path.join(os.path.dirname(__file__), "ui_chatbot.html")
            
            if os.path.exists(html_path):
                self.web_view.load(QUrl.fromLocalFile(html_path))
                print(f"Loading HTML from: {html_path}")
            else:
                print(f"HTML file not found: {html_path}")
                self.create_html_file(html_path)
                self.web_view.load(QUrl.fromLocalFile(html_path))
            
            # Set sebagai central widget
            self.setCentralWidget(self.web_view)
            
        except Exception as e:
            print(f"Error setting up web engine: {e}")
            self.show_error_message("WebEngine Error", f"Could not setup web interface: {e}")

    def create_html_file(self, html_path):
        """Create HTML file jika tidak ada"""
        html_content = '''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CutieChatter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #212121;
            color: #fff;
            height: 100vh;
            overflow: hidden;
        }

        .container {
            display: flex;
            height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: #171717;
            border-right: 1px solid #333;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
        }

        .sidebar.hidden {
            width: 0;
            overflow: hidden;
        }

        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid #333;
        }

        .new-chat-btn {
            width: 100%;
            background: transparent;
            border: 1px solid #333;
            color: #fff;
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            transition: all 0.2s;
        }

        .new-chat-btn:hover {
            background: #2a2a2a;
        }

        .search-btn {
            width: 100%;
            background: transparent;
            border: 1px solid #333;
            color: #fff;
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            transition: all 0.2s;
            margin-top: 8px;
        }

        .search-btn:hover {
            background: #2a2a2a;
        }

        .chat-history {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }

        .chat-history h3 {
            color: #8e8ea0;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 16px;
            font-weight: 500;
        }

        .chat-item {
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chat-item:hover {
            background: #2a2a2a;
        }

        .chat-item.active {
            background: #2a2a2a;
        }

        .chat-item-title {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 14px;
            flex: 1;
        }

        .chat-item-menu {
            opacity: 0;
            transition: opacity 0.2s;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
        }

        .chat-item:hover .chat-item-menu {
            opacity: 1;
        }

        .chat-item-menu:hover {
            background: #333;
        }

        /* Main Chat Area */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid #333;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .toggle-sidebar {
            background: transparent;
            border: none;
            color: #fff;
            cursor: pointer;
            padding: 8px;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .toggle-sidebar:hover {
            background: #333;
        }

        .model-selector {
            background: transparent;
            border: 1px solid #333;
            color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .message {
            display: flex;
            gap: 16px;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.assistant {
            justify-content: flex-start;
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }

        .user .message-avatar {
            background: #2563eb;
        }

        .assistant .message-avatar {
            background: #10a37f;
        }

        .message-content {
            background: #2a2a2a;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 70%;
            word-wrap: break-word;
            line-height: 1.5;
        }

        .user .message-content {
            background: #2563eb;
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: 40px;
        }

        .empty-state h1 {
            font-size: 32px;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .empty-state p {
            color: #8e8ea0;
            font-size: 16px;
        }

        /* Input Area */
        .input-area {
            padding: 20px;
            border-top: 1px solid #333;
        }

        .input-container {
            max-width: 800px;
            margin: 0 auto;
            position: relative;
        }

        .message-input {
            width: 100%;
            background: #2a2a2a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 16px 50px 16px 16px;
            color: #fff;
            font-size: 16px;
            resize: none;
            min-height: 24px;
            max-height: 120px;
            outline: none;
            transition: all 0.2s;
        }

        .message-input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
        }

        .send-button {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: #2563eb;
            border: none;
            border-radius: 8px;
            width: 32px;
            height: 32px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .send-button:hover {
            background: #1d4ed8;
        }

        .send-button:disabled {
            background: #333;
            cursor: not-allowed;
        }

        /* Search Modal */
        .search-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .search-modal.show {
            display: flex;
        }

        .search-modal-content {
            background: #2a2a2a;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 70%;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .search-modal-header {
            padding: 20px;
            border-bottom: 1px solid #333;
        }

        .search-input {
            width: 100%;
            background: #171717;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px 16px;
            color: #fff;
            font-size: 16px;
            outline: none;
        }

        .search-results {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }

        .search-result-item {
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 8px;
            transition: all 0.2s;
        }

        .search-result-item:hover {
            background: #333;
        }

        .search-result-title {
            font-size: 14px;
            margin-bottom: 4px;
        }

        .search-result-preview {
            font-size: 12px;
            color: #8e8ea0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Context Menu */
        .context-menu {
            position: absolute;
            background: #2a2a2a;
            border: 1px solid #333;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            z-index: 1000;
            display: none;
            min-width: 150px;
        }

        .context-menu-item {
            padding: 12px 16px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .context-menu-item:hover {
            background: #333;
        }

        .context-menu-item.danger {
            color: #ef4444;
        }

        .context-menu-item.danger:hover {
            background: rgba(239, 68, 68, 0.1);
        }

        /* Loading animation */
        .typing-indicator {
            display: flex;
            gap: 4px;
            align-items: center;
            padding: 8px 0;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: #8e8ea0;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes typing {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <button class="new-chat-btn" onclick="createNewChat()">
                    <span>✏️</span>
                    <span>Obrolan baru</span>
                </button>
                <button class="search-btn" onclick="openSearchModal()">
                    <span>🔍</span>
                    <span>Cari obrolan</span>
                </button>
            </div>
            <div class="chat-history">
                <h3>Obrolan</h3>
                <div id="chatHistoryList">
                    <!-- Chat history items will be dynamically added here -->
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="chat-header">
                <button class="toggle-sidebar" onclick="toggleSidebar()">
                    <span id="sidebarToggleText">📦 Tutup sidebar</span>
                </button>
                <select class="model-selector">
                    <option>DeepSeek-R1</option>
                    <option>GPT-4</option>
                    <option>Claude-3</option>
                </select>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="empty-state">
                    <h1>Apa yang bisa saya bantu?</h1>
                    <p>Mulai percakapan baru dengan mengetik pesan di bawah</p>
                </div>
            </div>

            <div class="input-area">
                <div class="input-container">
                    <textarea 
                        class="message-input" 
                        id="messageInput" 
                        placeholder="Ketik pesan Anda..."
                        rows="1"
                        onkeydown="handleKeyDown(event)"
                        oninput="autoResize(this)"
                    ></textarea>
                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                        <span>➤</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Search Modal -->
    <div class="search-modal" id="searchModal" onclick="closeSearchModal(event)">
        <div class="search-modal-content" onclick="event.stopPropagation()">
            <div class="search-modal-header">
                <input 
                    type="text" 
                    class="search-input" 
                    id="searchInput" 
                    placeholder="Cari obrolan..." 
                    oninput="searchChats()"
                >
            </div>
            <div class="search-results" id="searchResults">
                <!-- Search results will be shown here -->
            </div>
        </div>
    </div>

    <!-- Context Menu -->
    <div class="context-menu" id="contextMenu">
        <div class="context-menu-item" onclick="renameChat()">
            <span>✏️</span>
            <span>Rename</span>
        </div>
        <div class="context-menu-item danger" onclick="deleteChat()">
            <span>🗑️</span>
            <span>Delete</span>
        </div>
    </div>

    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        // Global variables
        let chats = JSON.parse(localStorage.getItem('chats')) || [];
        let currentChatId = null;
        let sidebarVisible = true;
        let selectedChatForContext = null;
        let bridge = null;
        let currentAIMessageElement = null;
        let isStreaming = false;

        // Initialize WebChannel communication
        new QWebChannel(qt.webChannelTransport, function(channel) {
            bridge = channel.objects.bridge;
            console.log("✅ Bridge connected:", bridge);
            
            // List available methods
            console.log("📋 Available bridge methods:", Object.getOwnPropertyNames(bridge));
            
            // Connect streaming signals
            if (bridge.streamChunk) {
                bridge.streamChunk.connect(function(chunk) {
                    console.log("📥 Received chunk from DeepSeek-R1:", chunk);
                    appendToCurrentAIMessage(chunk);
                });
                console.log("✅ streamChunk signal connected");
            } else {
                console.error("❌ streamChunk signal not available!");
            }
            
            if (bridge.streamFinished) {
                bridge.streamFinished.connect(function(response) {
                    console.log("✅ DeepSeek-R1 response finished:", response);
                    finishAIMessage(response);
                });
                console.log("✅ streamFinished signal connected");
            } else {
                console.error("❌ streamFinished signal not available!");
            }
            
            if (bridge.sendMessageStreaming) {
                console.log("✅ sendMessageStreaming method available");
            } else {
                console.error("❌ sendMessageStreaming method not available!");
            }
        });

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            loadChatHistory();
            if (chats.length > 0) {
                loadChat(chats[0].id);
            }
        });

        // Sidebar functions
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const toggleText = document.getElementById('sidebarToggleText');
            
            sidebarVisible = !sidebarVisible;
            
            if (sidebarVisible) {
                sidebar.classList.remove('hidden');
                toggleText.textContent = '📦 Tutup sidebar';
            } else {
                sidebar.classList.add('hidden');
                toggleText.textContent = '📦 Buka bar samping';
            }
        }

        // Chat management functions
        function createNewChat() {
            const newChat = {
                id: Date.now().toString(),
                title: 'Obrolan Baru',
                messages: [],
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };

            chats.unshift(newChat);
            saveChatHistory();
            loadChatHistory();
            loadChat(newChat.id);
        }

        function loadChat(chatId) {
            currentChatId = chatId;
            const chat = chats.find(c => c.id === chatId);
            
            if (!chat) return;

            // Update active state in sidebar
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            document.getElementById(`chat-${chatId}`)?.classList.add('active');

            // Load messages
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = '';

            if (chat.messages.length === 0) {
                messagesContainer.innerHTML = `
                    <div class="empty-state">
                        <h1>Apa yang bisa saya bantu?</h1>
                        <p>Mulai percakapan baru dengan mengetik pesan di bawah</p>
                    </div>
                `;
            } else {
                chat.messages.forEach(message => {
                    addMessageToChat(message.content, message.role, false);
                });
            }
        }

        function loadChatHistory() {
            const historyList = document.getElementById('chatHistoryList');
            historyList.innerHTML = '';

            chats.forEach(chat => {
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                chatItem.id = `chat-${chat.id}`;
                chatItem.onclick = () => loadChat(chat.id);
                
                chatItem.innerHTML = `
                    <div class="chat-item-title" title="${chat.title}">${chat.title}</div>
                    <div class="chat-item-menu" onclick="showContextMenu(event, '${chat.id}')">⋮</div>
                `;
                
                historyList.appendChild(chatItem);
            });
        }

        function saveChatHistory() {
            localStorage.setItem('chats', JSON.stringify(chats));
        }

        // Message functions
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isStreaming) return;

            // Ensure we have a current chat
            if (!currentChatId) {
                createNewChat();
            }

            // Add user message
            addMessageToChat(message, 'user');
            input.value = '';
            autoResize(input);

            // Update chat title if it's the first message
            const currentChat = chats.find(c => c.id === currentChatId);
            if (currentChat && currentChat.messages.length === 1) {
                currentChat.title = message.length > 30 ? message.substring(0, 30) + '...' : message;
                loadChatHistory();
            }

            // Add typing indicator and start AI response
            addTypingIndicator();
            startAIResponse();

            // Send to Python backend
            if (bridge) {
                if (!bridge.sendMessageStreaming) {
                    console.error("❌ CRITICAL: sendMessageStreaming method not available!");
                    removeTypingIndicator();
                    finishAIMessage("❌ ERROR: sendMessageStreaming tidak tersedia");
                    return;
                }
                
                isStreaming = true;
                
                console.log("🚀 Calling bridge.sendMessageStreaming with:", message);
                try {
                    bridge.sendMessageStreaming(message);
                    console.log("✅ bridge.sendMessageStreaming called successfully");
                } catch (error) {
                    console.error("❌ Error calling bridge.sendMessageStreaming:", error);
                    removeTypingIndicator();
                    finishAIMessage("❌ ERROR calling sendMessageStreaming: " + error);
                }
            } else {
                console.error("❌ CRITICAL: Bridge tidak tersedia!");
                removeTypingIndicator();
                finishAIMessage("❌ ERROR: Bridge tidak tersedia. Restart aplikasi.");
            }
        }

        function startAIResponse() {
            removeTypingIndicator();
            
            // Create AI message container
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.id = 'current-ai-message';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content" id="ai-message-content"></div>
            `;

            messagesContainer.appendChild(messageDiv);
            currentAIMessageElement = document.getElementById('ai-message-content');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function appendToCurrentAIMessage(chunk) {
            if (currentAIMessageElement) {
                currentAIMessageElement.innerHTML += chunk;
                
                // Scroll to bottom
                const messagesContainer = document.getElementById('chatMessages');
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }

        function finishAIMessage(fullResponse) {
            isStreaming = false;
            
            // Clean up current message element
            if (currentAIMessageElement) {
                currentAIMessageElement = null;
            }

            // Save to chat history
            if (currentChatId) {
                const currentChat = chats.find(c => c.id === currentChatId);
                if (currentChat) {
                    currentChat.messages.push({
                        role: 'assistant',
                        content: fullResponse,
                        timestamp: new Date().toISOString()
                    });
                    currentChat.updatedAt = new Date().toISOString();
                    saveChatHistory();
                }
            }

            console.log("AI response finished:", fullResponse);
        }

        function addMessageToChat(content, role, saveToHistory = true) {
            const messagesContainer = document.getElementById('chatMessages');
            
            // Remove empty state if present
            const emptyState = messagesContainer.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const avatar = role === 'user' ? '👤' : '🤖';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${content}</div>
            `;

            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // Save to chat history
            if (saveToHistory && currentChatId) {
                const currentChat = chats.find(c => c.id === currentChatId);
                if (currentChat) {
                    currentChat.messages.push({
                        role: role,
                        content: content,
                        timestamp: new Date().toISOString()
                    });
                    currentChat.updatedAt = new Date().toISOString();
                    saveChatHistory();
                }
            }
        }

        function addTypingIndicator() {
            const messagesContainer = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typing-indicator';
            
            typingDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `;

            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function removeTypingIndicator() {
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }

        function generateAIResponse(userMessage) {
            // TIDAK ADA fallback response - ini seharusnya tidak pernah dipanggil
            console.error("generateAIResponse called - this should not happen!");
            return "❌ ERROR: generateAIResponse called instead of using DeepSeek-R1";
        }

        // Search functions
        function openSearchModal() {
            document.getElementById('searchModal').classList.add('show');
            document.getElementById('searchInput').focus();
            searchChats(); // Show all chats initially
        }

        function closeSearchModal(event) {
            if (event.target === document.getElementById('searchModal')) {
                document.getElementById('searchModal').classList.remove('show');
                document.getElementById('searchInput').value = '';
            }
        }

        function searchChats() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const resultsContainer = document.getElementById('searchResults');
            
            const filteredChats = chats.filter(chat => 
                chat.title.toLowerCase().includes(searchTerm) ||
                chat.messages.some(msg => msg.content.toLowerCase().includes(searchTerm))
            );

            resultsContainer.innerHTML = '';

            if (filteredChats.length === 0) {
                resultsContainer.innerHTML = '<div style="text-align: center; color: #8e8ea0; padding: 20px;">Tidak ada hasil ditemukan</div>';
                return;
            }

            filteredChats.forEach(chat => {
                const resultItem = document.createElement('div');
                resultItem.className = 'search-result-item';
                resultItem.onclick = () => {
                    loadChat(chat.id);
                    closeSearchModal({ target: document.getElementById('searchModal') });
                };

                const preview = chat.messages.length > 0 
                    ? chat.messages[chat.messages.length - 1].content 
                    : 'Belum ada pesan';

                resultItem.innerHTML = `
                    <div class="search-result-title">${chat.title}</div>
                    <div class="search-result-preview">${preview}</div>
                `;

                resultsContainer.appendChild(resultItem);
            });
        }

        // Context menu functions
        function showContextMenu(event, chatId) {
            event.stopPropagation();
            selectedChatForContext = chatId;
            
            const contextMenu = document.getElementById('contextMenu');
            contextMenu.style.display = 'block';
            contextMenu.style.left = event.pageX + 'px';
            contextMenu.style.top = event.pageY + 'px';
        }

        function hideContextMenu() {
            document.getElementById('contextMenu').style.display = 'none';
            selectedChatForContext = null;
        }

        function renameChat() {
            if (!selectedChatForContext) return;
            
            const chat = chats.find(c => c.id === selectedChatForContext);
            if (!chat) return;

            const newTitle = prompt('Nama baru untuk obrolan:', chat.title);
            if (newTitle && newTitle.trim()) {
                chat.title = newTitle.trim();
                saveChatHistory();
                loadChatHistory();
            }
            
            hideContextMenu();
        }

        function deleteChat() {
            if (!selectedChatForContext) return;
            
            if (confirm('Apakah Anda yakin ingin menghapus obrolan ini?')) {
                chats = chats.filter(c => c.id !== selectedChatForContext);
                saveChatHistory();
                loadChatHistory();
                
                if (currentChatId === selectedChatForContext) {
                    if (chats.length > 0) {
                        loadChat(chats[0].id);
                    } else {
                        currentChatId = null;
                        document.getElementById('chatMessages').innerHTML = `
                            <div class="empty-state">
                                <h1>Apa yang bisa saya bantu?</h1>
                                <p>Mulai percakapan baru dengan mengetik pesan di bawah</p>
                            </div>
                        `;
                    }
                }
            }
            
            hideContextMenu();
        }

        // Input handling
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }

        // Event listeners
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.context-menu') && !event.target.closest('.chat-item-menu')) {
                hideContextMenu();
            }
        });

        // Close search modal with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                const searchModal = document.getElementById('searchModal');
                if (searchModal.classList.contains('show')) {
                    closeSearchModal({ target: searchModal });
                }
            }
        });
    </script>
</body>
</html>'''
        
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML file created: {html_path}")
        except Exception as e:
            print(f"Error creating HTML file: {e}")

    def process_message_sync(self, message):
        """Process pesan secara synchronous untuk WebChannel"""
        try:
            print(f"Processing message sync: {message}")
            
            # Add to conversation history
            self.conversation_history.append({'role': 'user', 'content': message})
            
            # Sentiment analysis (if available)
            if self.classifier is not None:
                try:
                    user_sentiment_score = self.GetSentimentOnPrimary(message)
                    print(f"User Sentiment Score: {user_sentiment_score}")
                    self.user_text_metadata.append(message)
                    self.user_features_metadata.append(user_sentiment_score)
                except Exception as e:
                    print(f"Error in sentiment analysis: {e}")
            
            # HANYA menggunakan DeepSeek-R1:1.5b model, TIDAK ADA fallback dummy response
            response = self.generate_ollama_response_sync(message)
            
            # Add AI response to conversation history
            self.conversation_history.append({'role': 'assistant', 'content': response})
            
            # AI sentiment analysis
            if self.classifier is not None:
                try:
                    ai_sentiment_score = self.GetSentimentOnPrimary(response)
                    print(f"AI Sentiment Score: {ai_sentiment_score}")
                    self.ai_text_metadata.append(response)
                    self.ai_features_metadata.append(ai_sentiment_score)
                except Exception as e:
                    print(f"Error in AI sentiment analysis: {e}")
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return f"Maaf, terjadi kesalahan saat berkomunikasi dengan DeepSeek-R1: {str(e)}"

    def process_message_streaming(self, message, bridge):
        """Process pesan dengan streaming response LANGSUNG dari DeepSeek-R1"""
        try:
            print(f"🤖 Processing with DeepSeek-R1 streaming: {message}")
            
            # Add to conversation history
            self.conversation_history.append({'role': 'user', 'content': message})
            
            # Sentiment analysis (if available)
            if self.classifier is not None:
                try:
                    user_sentiment_score = self.GetSentimentOnPrimary(message)
                    print(f"User Sentiment Score: {user_sentiment_score}")
                    self.user_text_metadata.append(message)
                    self.user_features_metadata.append(user_sentiment_score)
                except Exception as e:
                    print(f"Error in sentiment analysis: {e}")
            
            # LANGSUNG ke DeepSeek-R1 streaming, TIDAK ADA fallback
            print(f"🔄 Starting DeepSeek-R1 OllamaWorker with model: {self.model_name}")
            self.start_ollama_streaming(bridge)
            
        except Exception as e:
            print(f"❌ CRITICAL Error in DeepSeek-R1 processing: {e}")
            bridge.streamFinished.emit(f"❌ CRITICAL: Tidak dapat memproses dengan DeepSeek-R1: {str(e)}")

    def start_ollama_streaming(self, bridge):
        """Start Ollama worker LANGSUNG dari DeepSeek-R1:1.5b - FIXED VERSION"""
        try:
            print(f"🚀 STARTING DeepSeek-R1 streaming with model: {self.model_name}")
            
            # PAKSA gunakan backends, error jika tidak ada
            if not BACKENDS_AVAILABLE:
                error_msg = f"❌ CRITICAL: backends module tidak tersedia!"
                print(error_msg)
                bridge.streamFinished.emit(error_msg)
                return
            
            # Import OllamaWorker PAKSA dari backends yang benar
            try:
                from backends import OllamaWorker
                print("✅ OllamaWorker imported successfully from backends.py")
            except ImportError as e:
                error_msg = f"❌ CRITICAL: Cannot import OllamaWorker: {e}"
                print(error_msg)
                bridge.streamFinished.emit(error_msg)
                return
            
            # Stop existing worker jika ada
            if hasattr(self, 'ollama_thread') and self.ollama_thread and self.ollama_thread.isRunning():
                print("🛑 Stopping existing DeepSeek-R1 thread")
                self.ollama_thread.quit()
                self.ollama_thread.wait(3000)
            
            # Reset thread status
            self.is_ollama_thread_running = False
            
            # Check jika masih ada thread yang running
            if self.is_ollama_thread_running:
                print("⚠️ Thread already running, aborting")
                return

            # Disconnect previous worker signals
            if hasattr(self, 'ollama_worker') and self.ollama_worker:
                try:
                    self.ollama_worker.chunk_received.disconnect()
                    self.ollama_worker.finished.disconnect()
                    print("🔌 Disconnected previous worker signals")
                except:
                    pass

            print(f"🎯 Creating OllamaWorker with:")
            print(f"   - Model: {self.model_name}")
            print(f"   - Last message: {self.conversation_history[-1]['content']}")
            print(f"   - History length: {len(self.conversation_history)}")
            
            # Set status SEBELUM membuat thread
            self.is_ollama_thread_running = True
            
            # Create worker dan thread seperti di backends.py original
            self.ollama_thread = QThread()
            self.ollama_worker = OllamaWorker(
                self.conversation_history[-1]['content'],  # user_message
                self.conversation_history.copy(),          # conversation_history  
                self.model_name                           # model_name
            )
            
            # Move worker to thread
            self.ollama_worker.moveToThread(self.ollama_thread)
            print("📦 Moved OllamaWorker to thread")
            
            # Connect signals - PENTING: connect sebelum start!
            def on_chunk_received(chunk):
                print(f"📥 Chunk received: {chunk[:50]}...")
                bridge.streamChunk.emit(chunk)
            
            def on_finished(response):
                print(f"✅ Response finished, length: {len(response)}")
                self.on_ollama_response_complete_web(response, bridge)
            
            self.ollama_worker.chunk_received.connect(on_chunk_received)
            self.ollama_worker.finished.connect(on_finished)
            self.ollama_thread.started.connect(self.ollama_worker.run)
            
            print("🔗 Connected all signals")
            
            # START THREAD
            self.ollama_thread.start()
            
            print(f"🟢 DeepSeek-R1 streaming STARTED successfully!")
            
        except Exception as e:
            error_msg = f"❌ CRITICAL ERROR starting DeepSeek-R1: {e}"
            print(error_msg)
            print(f"   - BACKENDS_AVAILABLE: {BACKENDS_AVAILABLE}")
            print(f"   - Model name: {self.model_name}")
            print(f"   - Exception details: {type(e).__name__}: {e}")
            
            # Reset status on error
            self.is_ollama_thread_running = False
            bridge.streamFinished.emit(error_msg)

    def on_ollama_response_complete_web(self, response, bridge):
        """Handle completion of Ollama response untuk web interface - FIXED"""
        try:
            print(f"🏁 Ollama response complete, cleaning response...")
            
            # Clean response menggunakan TextCleaner dari backends
            try:
                from backends import TextCleaner
                text_cleaner = TextCleaner(response)
                cleaned_response = text_cleaner.response_only(response)
                print(f"✅ Response cleaned: {len(cleaned_response)} chars")
                final_response = cleaned_response
            except Exception as cleaning_error:
                print(f"⚠️ Error cleaning response: {cleaning_error}")
                final_response = response
            
            # Add to conversation history
            if final_response.strip():  # Only add non-empty responses
                self.conversation_history.append({'role': 'assistant', 'content': final_response})
                print(f"📝 Added to conversation history")

            # Sentiment analysis (if available) - dari original code
            if self.classifier is not None and SENTIMENT_AVAILABLE:
                try:
                    self.ai_sentiment_score = self.GetSentimentOnPrimary(final_response)
                    print(f"📊 AI Sentiment Score: {self.ai_sentiment_score}")
                    
                    self.ai_text_metadata.append(final_response)
                    self.ai_features_metadata.append(self.ai_sentiment_score)
                    
                    # Calculate text similarity if models are available
                    if self.ModelForCS is not None and len(self.user_text_metadata) > 0:
                        try:
                            from sentiment.memory.textsimilarity import TextSimilaritySearch
                            text_similarity_search = TextSimilaritySearch(
                                self.ModelForCS, 
                                self.tokenizer, 
                                self.device
                            )
                            
                            # Get similarity between latest user and AI messages
                            latest_user_text = self.user_text_metadata[-1] if self.user_text_metadata else ""
                            similarity_score = text_similarity_search.calculate_similarity(
                                latest_user_text, 
                                final_response
                            )
                            
                            self.cosine_of_text_metadata.append(similarity_score)
                            print(f"🔗 Text Similarity Score: {similarity_score}")
                            
                        except Exception as e:
                            print(f"⚠️ Error calculating text similarity: {e}")
                            
                except Exception as e:
                    print(f"⚠️ Error in AI sentiment analysis: {e}")
            else:
                print("📊 AI sentiment analysis disabled - classifier not available")

            # Clean up thread seperti original
            if hasattr(self, 'ollama_thread') and self.ollama_thread:
                print("🧹 Cleaning up thread...")
                self.ollama_thread.quit()
                self.ollama_thread.wait(3000)  # Wait max 3 seconds
                self.ollama_thread = None

            if hasattr(self, 'ollama_worker'):
                self.ollama_worker = None
                
            self.is_ollama_thread_running = False
            
            # Emit signal untuk web interface dengan cleaned response
            bridge.streamFinished.emit(final_response)
            print(f"✅ Web interface notified with final response")
                
        except Exception as e:
            error_msg = f"❌ Error in response completion: {e}"
            print(error_msg)
            self.is_ollama_thread_running = False
            bridge.streamFinished.emit(error_msg)

    def run_ollama_chat(self):
        """Run Ollama chat with error handling - dari original code"""
        if not BACKENDS_AVAILABLE:
            print("Backends not available - cannot run Ollama chat")
            return
            
        if self.is_ollama_thread_running:
            return

        # Disconnect previous worker signals
        if hasattr(self, 'ollama_worker') and self.ollama_worker:
            try:
                self.ollama_worker.chunk_received.disconnect()
                self.ollama_worker.finished.disconnect()
            except:
                pass

        self.is_ollama_thread_running = True

        try:
            from backends import OllamaWorker
            
            self.ollama_thread = QThread()
            self.ollama_worker = OllamaWorker(
                self.conversation_history[-1]['content'], 
                self.conversation_history, 
                self.model_name
            )
            
            self.ollama_worker.moveToThread(self.ollama_thread)

            # Connect signals - untuk desktop mode jika ada
            if hasattr(self, 'chat_widget'):
                self.ollama_worker.chunk_received.connect(self.chat_widget.append_to_ai_message)
                
            self.ollama_worker.finished.connect(self.on_ollama_response_complete)
            self.ollama_thread.started.connect(self.ollama_worker.run)
            self.ollama_thread.start()
            
        except Exception as e:
            print(f"Error starting Ollama chat: {e}")
            self.is_ollama_thread_running = False

    def on_ollama_response_complete(self, response):
        """Handle completion of Ollama response - dari original code"""
        self.conversation_history.append({'role': 'assistant', 'content': response})

        # Sentiment analysis (if available)
        if self.classifier is not None and SENTIMENT_AVAILABLE:
            try:
                self.ai_sentiment_score = self.GetSentimentOnPrimary(response)
                print(f"AI Sentiment Score: {self.ai_sentiment_score}")
                
                self.ai_text_metadata.append(response)
                self.ai_features_metadata.append(self.ai_sentiment_score)
                
                # Calculate text similarity if models are available
                if self.ModelForCS is not None and len(self.user_text_metadata) > 0:
                    try:
                        from sentiment.memory.textsimilarity import TextSimilaritySearch
                        text_similarity_search = TextSimilaritySearch(
                            self.ModelForCS, 
                            self.tokenizer, 
                            self.device
                        )
                        
                        # Get similarity between latest user and AI messages
                        latest_user_text = self.user_text_metadata[-1] if self.user_text_metadata else ""
                        similarity_score = text_similarity_search.calculate_similarity(
                            latest_user_text, 
                            response
                        )
                        
                        self.cosine_of_text_metadata.append(similarity_score)
                        print(f"Text Similarity Score: {similarity_score}")
                        
                    except Exception as e:
                        print(f"Error calculating text similarity: {e}")
                        
            except Exception as e:
                print(f"Error in AI sentiment analysis: {e}")
        else:
            print("AI sentiment analysis disabled - classifier not available")

        # Clean up thread
        if self.ollama_thread:
            self.ollama_thread.quit()
            self.ollama_thread.wait()
            self.ollama_thread = None

        self.ollama_worker = None
        self.is_ollama_thread_running = False

    def naked_text(self, text):
        """Clean text from HTML and special markers"""
        text = re.sub(r'<\s*/\s*div\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '', text)
        text = re.sub(r'<\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        return text

    def process_message(self, message):
        """Process pesan dari web interface dengan DeepSeek-R1:1.5b"""
        try:
            print(f"Processing message with DeepSeek-R1: {message}")
            
            # Add to conversation history
            self.conversation_history.append({'role': 'user', 'content': message})
            
            # Sentiment analysis (if available)
            if self.classifier is not None:
                try:
                    user_sentiment_score = self.GetSentimentOnPrimary(message)
                    print(f"User Sentiment Score: {user_sentiment_score}")
                    self.user_text_metadata.append(message)
                    self.user_features_metadata.append(user_sentiment_score)
                except Exception as e:
                    print(f"Error in sentiment analysis: {e}")
            
            # HANYA menggunakan DeepSeek-R1:1.5b, TIDAK ADA fallback
            response = self.generate_ollama_response_sync(message)
            
            # Add AI response to conversation history
            self.conversation_history.append({'role': 'assistant', 'content': response})
            
            # AI sentiment analysis
            if self.classifier is not None:
                try:
                    ai_sentiment_score = self.GetSentimentOnPrimary(response)
                    print(f"AI Sentiment Score: {ai_sentiment_score}")
                    self.ai_text_metadata.append(response)
                    self.ai_features_metadata.append(ai_sentiment_score)
                except Exception as e:
                    print(f"Error in AI sentiment analysis: {e}")
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return f"Maaf, terjadi kesalahan saat berkomunikasi dengan DeepSeek-R1: {str(e)}"

    def generate_ollama_response_sync(self, message):
        """Generate response menggunakan DeepSeek-R1:1.5b secara synchronous"""
        try:
            # Pastikan ollama module tersedia
            try:
                import ollama
            except ImportError:
                raise Exception("Ollama Python library tidak tersedia. Install dengan: pip install ollama")
            
            import multiprocessing
            
            # Setup parameters sama seperti di OllamaWorker
            num_threads = multiprocessing.cpu_count() / 2
            
            print(f"🤖 Menghubungi DeepSeek-R1 model: {self.model_name}")
            print(f"📝 Conversation history length: {len(self.conversation_history)}")
            
            # Call Ollama API secara synchronous dengan DeepSeek-R1
            response = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=False,  # Non-streaming untuk WebChannel
                options={
                    "num_thread": num_threads,
                    "temperature": 1.2,
                    "top_n": 50,
                    "top_k": 1.4,
                    "f16_kv": True,
                    "num_ctx": 1024,
                    "num_batch": 32,
                    "num_prediction": 12
                }
            )
            
            # Extract response content dari DeepSeek-R1
            full_content = response['message']['content']
            
            # Clean response menggunakan TextCleaner dari backend
            try:
                from backends import TextCleaner
                text_cleaner = TextCleaner(full_content)
                cleaned_response = text_cleaner.response_only(full_content)
                print(f"✅ DeepSeek-R1 response received: {len(cleaned_response)} characters")
                return cleaned_response
            except Exception as cleaning_error:
                print(f"⚠️ Error cleaning response, returning raw: {cleaning_error}")
                return full_content
            
        except Exception as e:
            error_msg = f"❌ Error saat berkomunikasi dengan DeepSeek-R1: {str(e)}"
            print(error_msg)
            
            # Berikan pesan error yang informatif
            if "Connection" in str(e) or "refused" in str(e):
                return "🚫 Tidak dapat terhubung ke Ollama. Pastikan Ollama server sudah berjalan dengan menjalankan 'ollama serve' di terminal."
            elif "not found" in str(e) or "model" in str(e).lower():
                                    return f"🚫 Model DeepSeek-R1 ({self.model_name}) tidak ditemukan. Jalankan 'ollama pull {self.model_name}' untuk mendownload model."
            else:
                return f"🚫 Error DeepSeek-R1: {str(e)}"

    def show_error_message(self, title, message):
        """Show error message to user"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
        except Exception as e:
            print(f"Error showing message box: {e}")
            print(f"Error: {title} - {message}")

    def load_models(self):
        """Load AI models with comprehensive error handling"""
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            print("Sentiment analysis disabled - required libraries not available")
            return
            
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {self.device}")
            
            # Try multiple model paths
            model_paths = [
                # Local model path
                os.path.join(os.path.dirname(__file__), "CoreDynamics", "models", "stardust_6"),
                # Alternative local path
                r"C:\Users\Aldrich\Downloads\cutie-chatter-main\cutie-chatter-main\CoreDynamics\models\stardust_6",
                # Fallback to Hugging Face model
                "cardiffnlp/twitter-roberta-base-emotion"
            ]
            
            model_loaded = False
            for model_path in model_paths:
                try:
                    print(f"Trying to load model from: {model_path}")
                    
                    # Check if local path exists and has required files
                    if os.path.exists(model_path) and os.path.isdir(model_path):
                        required_files = ["config.json"]
                        if not all(os.path.exists(os.path.join(model_path, f)) for f in required_files):
                            print(f"Missing required files in {model_path}")
                            continue
                    
                    # Load tokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        use_fast=True,
                        model_max_length=512,
                        trust_remote_code=True
                    )
                    
                    # Fix padding token issue
                    if self.tokenizer.pad_token is None:
                        if self.tokenizer.eos_token is not None:
                            self.tokenizer.pad_token = self.tokenizer.eos_token
                            print("Set pad_token to eos_token")
                        elif self.tokenizer.unk_token is not None:
                            self.tokenizer.pad_token = self.tokenizer.unk_token
                            print("Set pad_token to unk_token")
                        else:
                            self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                            print("Added new pad_token: [PAD]")
                    
                    # Load sentiment model
                    self.ModelForSentimentScoring = AutoModelForSequenceClassification.from_pretrained(
                        model_path,
                        num_labels=6,
                        trust_remote_code=True
                    ).to(self.device)
                    
                    # Resize embeddings if needed
                    if hasattr(self.tokenizer, 'pad_token') and self.tokenizer.pad_token == '[PAD]':
                        self.ModelForSentimentScoring.resize_token_embeddings(len(self.tokenizer))
                    
                    # Initialize classifier
                    if SENTIMENT_AVAILABLE:
                        self.classifier = EmotionClassifier(
                            self.ModelForSentimentScoring,
                            self.tokenizer,
                            self.device,
                            composite_dictionary=None
                        )
                    
                    # Load similarity model
                    try:
                        self.ModelForCS = AutoModel.from_pretrained(
                            model_path,
                            trust_remote_code=True
                        ).to(self.device)
                        
                        if hasattr(self.tokenizer, 'pad_token') and self.tokenizer.pad_token == '[PAD]':
                            self.ModelForCS.resize_token_embeddings(len(self.tokenizer))
                            
                    except Exception as e:
                        print(f"Could not load CS model from {model_path}: {e}")
                        # Fallback for similarity model
                        try:
                            self.ModelForCS = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2").to(self.device)
                        except:
                            print("Could not load fallback similarity model")
                            self.ModelForCS = None
                    
                    print(f"Successfully loaded model from: {model_path}")
                    model_loaded = True
                    break
                    
                except Exception as e:
                    print(f"Failed to load model from {model_path}: {e}")
                    continue
            
            if not model_loaded:
                print("Could not load any model - sentiment analysis will be disabled")
                self.classifier = None
                self.ModelForSentimentScoring = None
                self.ModelForCS = None
                self.tokenizer = None
                
        except Exception as e:
            print(f"Error in model loading setup: {e}")
            self.classifier = None
            self.ModelForSentimentScoring = None
            self.ModelForCS = None
            self.tokenizer = None

    def naked_text(self, text):
        """Clean text from HTML and special markers"""
        text = re.sub(r'<\s*/\s*div\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '', text)
        text = re.sub(r'<\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        return text

    def GetSentimentOnPrimary(self, text):
        """Get sentiment analysis for given text"""
        if self.classifier is None:
            print("Classifier not available")
            return None
            
        try:
            # Clean the text
            cleaned_text = self.naked_text(text)
            
            # Get sentiment prediction
            sentiment_result = self.classifier.predict_emotion(cleaned_text)
            
            # Convert to appropriate format (adjust based on your classifier output)
            if isinstance(sentiment_result, dict):
                return sentiment_result
            elif isinstance(sentiment_result, list):
                return sentiment_result[0] if sentiment_result else None
            else:
                return sentiment_result
                
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return None

    def get_memory_stats(self):
        """Get current memory usage statistics"""
        try:
            stats = {
                'conversation_length': len(self.conversation_history),
                'user_metadata_count': len(self.user_text_metadata),
                'ai_metadata_count': len(self.ai_text_metadata),
                'similarity_scores_count': len(self.cosine_of_text_metadata)
            }
            
            if TORCH_AVAILABLE:
                import torch
                if torch.cuda.is_available():
                    stats['gpu_memory_allocated'] = torch.cuda.memory_allocated()
                    stats['gpu_memory_reserved'] = torch.cuda.memory_reserved()
                    
            return stats
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {}

    def clear_conversation_history(self):
        """Clear conversation history and metadata"""
        try:
            # Keep only the system message
            self.conversation_history = [self.conversation_history[0]] if self.conversation_history else []
            
            # Clear metadata
            self.ai_features_metadata.clear()
            self.ai_text_metadata.clear()
            self.user_features_metadata.clear()
            self.user_text_metadata.clear()
            self.cosine_of_text_metadata.clear()
            
            # Clear chat widget if possible
            if hasattr(self, 'chat_widget') and self.chat_widget:
                if hasattr(self.chat_widget, 'clear_chat'):
                    self.chat_widget.clear_chat()
                elif hasattr(self.chat_widget, 'clear'):
                    self.chat_widget.clear()
                    
            print("Conversation history cleared")
            
        except Exception as e:
            print(f"Error clearing conversation history: {e}")

    def animate_submit_button(self):
        """Add animation effect to submit button"""
        try:
            # Create a simple scale animation
            if hasattr(self, 'submit_button'):
                self.animation = QPropertyAnimation(self.submit_button, b"geometry")
                current_geometry = self.submit_button.geometry()
                
                # Scale down
                smaller_geometry = current_geometry.adjusted(2, 2, -2, -2)
                self.animation.setDuration(100)
                self.animation.setStartValue(current_geometry)
                self.animation.setEndValue(smaller_geometry)
                self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
                
                # Scale back up
                def scale_back():
                    self.animation2 = QPropertyAnimation(self.submit_button, b"geometry")
                    self.animation2.setDuration(100)
                    self.animation2.setStartValue(smaller_geometry)
                    self.animation2.setEndValue(current_geometry)
                    self.animation2.setEasingCurve(QEasingCurve.Type.InOutQuad)
                    self.animation2.start()
                
                self.animation.finished.connect(scale_back)
                self.animation.start()
            
        except Exception as e:
            print(f"Error in button animation: {e}")

    def keyPressEvent(self, event):
        """Handle key press events"""
        try:
            # Handle Ctrl+Enter or Shift+Enter to send message
            if (event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter):
                if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                    # For web interface, we don't have prompt_box, so this won't trigger
                    if hasattr(self, 'prompt_box') and self.prompt_box and self.prompt_box.hasFocus():
                        self.on_submit()
                        return
            
            # Handle Ctrl+T to toggle theme (if we implement themes later)
            elif event.key() == Qt.Key.Key_T and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if hasattr(self, 'toggle_theme'):
                    self.toggle_theme()
                return
                
            # Handle Escape to minimize
            elif event.key() == Qt.Key.Key_Escape:
                self.setWindowState(self.windowState() | Qt.WindowState.WindowMinimized)
                return
                
        except Exception as e:
            print(f"Error in key press event: {e}")
            
        super().keyPressEvent(event)

    def on_submit(self):
        """Handle message submission - untuk compatibility dengan original code"""
        # This method is for backward compatibility if needed
        # The main interaction now happens through web interface
        print("on_submit called - using web interface instead")
        pass

    def run_ocr_chat(self):
        """Run OCR chat with error handling - placeholder dari original"""
        if not BACKENDS_AVAILABLE:
            print("Backends not available - cannot run OCR chat")
            return
            
        if self.is_ollama_thread_running:
            return

        # Placeholder untuk OCR functionality
        print("OCR chat functionality - would implement OllamaOCRWorker here")

    def on_submit_ocr(self):
        """Handle OCR submission - placeholder dari original"""
        if not OCR_AVAILABLE or not BACKENDS_AVAILABLE:
            print("OCR functionality not available")
            return
        
        # Placeholder untuk OCR functionality  
        print("OCR submit functionality")

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Save current theme setting
            self.settings.setValue("dark_theme", self.is_dark_theme)
            
            # Clean up models to free memory
            if hasattr(self, 'ModelForSentimentScoring') and self.ModelForSentimentScoring is not None:
                del self.ModelForSentimentScoring
                
            if hasattr(self, 'ModelForCS') and self.ModelForCS is not None:
                del self.ModelForCS
                
            if hasattr(self, 'tokenizer') and self.tokenizer is not None:
                del self.tokenizer
                
            # Clear CUDA cache if using GPU
            if TORCH_AVAILABLE:
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except:
                    pass
                    
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
        event.accept()


def main():
    """Main function to run the application"""
    import sys
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("CutieChatter")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("CutieChatter")
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create main window
        model_name = "deepseek-r1:1.5b"  # Default model
        if len(sys.argv) > 1:
            model_name = sys.argv[1]
            
        window = CutieTheCutest(model_name=model_name)
        window.show()
        
        print(f"CutieChatter started with model: {model_name}")
        print("Available features:")
        print(f"  - Transformers: {'✓' if TRANSFORMERS_AVAILABLE else '✗'}")
        print(f"  - Backends: {'✓' if BACKENDS_AVAILABLE else '✗'}")
        print(f"  - OCR: {'✓' if OCR_AVAILABLE else '✗'}")
        print(f"  - Sentiment Analysis: {'✓' if SENTIMENT_AVAILABLE else '✗'}")
        print(f"  - PyTorch: {'✓' if TORCH_AVAILABLE else '✗'}")
        print(f"  - Screen Info: {'✓' if SCREENINFO_AVAILABLE else '✗'}")
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()