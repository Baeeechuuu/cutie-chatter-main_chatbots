# web_ui/web_interface.py

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import os
from ..chat_bridge import ChatBridge


class WebInterface(QWidget):
    """Web-based interface untuk CutieChatter"""
    
    def __init__(self, parent_app=None):
        super().__init__()
        self.parent_app = parent_app
        self.setup_ui()
        
    def setup_ui(self):
        """Setup web interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view
        self.web_view = QWebEngineView()
        
        # Setup communication bridge
        self.bridge = ChatBridge(self.parent_app)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Connect signals if parent app has theme change
        if hasattr(self.parent_app, 'theme_changed'):
            self.parent_app.theme_changed.connect(self.on_theme_changed)
        
        # Load HTML
        html_path = os.path.join(
            os.path.dirname(__file__), 
            'assets', 
            'chat_ui.html'
        )
        
        # Create HTML if doesn't exist
        if not os.path.exists(html_path):
            os.makedirs(os.path.dirname(html_path), exist_ok=True)
            self.create_html_file(html_path)
        
        self.web_view.load(QUrl.fromLocalFile(html_path))
        
        # Add to layout
        layout.addWidget(self.web_view)
    
    def on_theme_changed(self, is_dark):
        """Handle theme change from parent app"""
        self.bridge.themeChanged.emit(is_dark)
    
    def create_html_file(self, html_path):
        """Create the HTML file for web UI"""
        html_content = self.get_html_content()
        
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML file created: {html_path}")
        except Exception as e:
            print(f"❌ Error creating HTML file: {e}")
    
    def get_html_content(self):
        """Get HTML content for the web UI"""
        return '''<!DOCTYPE html>
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

        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-sidebar: #202020;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --accent: #4a9eff;
            --user-msg-bg: #4a9eff;
            --ai-msg-bg: #2d2d2d;
            --border-color: #3a3a3a;
            --hover-bg: #353535;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
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
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .new-chat-btn {
            width: 100%;
            padding: 12px 16px;
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            transition: all 0.2s;
        }

        .new-chat-btn:hover {
            background: var(--hover-bg);
            border-color: var(--accent);
        }

        .search-btn {
            width: 100%;
            padding: 10px 16px;
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            transition: all 0.2s;
            margin-top: 10px;
        }

        .search-btn:hover {
            background: var(--hover-bg);
            color: var(--text-primary);
        }

        .chat-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }

        .chat-list-header {
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 10px 10px 5px;
            letter-spacing: 0.5px;
        }

        .chat-item {
            padding: 12px 16px;
            margin-bottom: 4px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-secondary);
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chat-item:hover {
            background: var(--hover-bg);
            color: var(--text-primary);
        }

        .chat-item.active {
            background: var(--hover-bg);
            color: var(--text-primary);
        }

        /* Main content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
        }

        .chat-header {
            padding: 20px 30px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .header-left h2 {
            font-size: 16px;
            font-weight: 500;
        }

        .model-selector {
            padding: 8px 16px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .model-selector:hover {
            background: var(--hover-bg);
        }

        /* Chat messages */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
        }

        .empty-state h1 {
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--accent), #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .empty-state p {
            color: var(--text-secondary);
            font-size: 16px;
        }

        .message {
            display: flex;
            gap: 12px;
            max-width: 850px;
            width: 100%;
            margin: 0 auto;
        }

        .message.user {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }

        .user .message-avatar {
            background: var(--user-msg-bg);
        }

        .assistant .message-avatar {
            background: #10a37f;
        }

        .message-content {
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 70%;
            line-height: 1.5;
            font-size: 15px;
        }

        .user .message-content {
            background: var(--user-msg-bg);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .assistant .message-content {
            background: var(--ai-msg-bg);
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
            border: 1px solid var(--border-color);
        }

        /* Input area */
        .input-area {
            padding: 20px 30px 30px;
            border-top: 1px solid var(--border-color);
        }

        .input-container {
            max-width: 850px;
            margin: 0 auto;
            position: relative;
        }

        .message-input {
            width: 100%;
            padding: 16px 50px 16px 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 12px;
            font-size: 15px;
            resize: none;
            outline: none;
            font-family: inherit;
            line-height: 1.5;
            min-height: 56px;
            max-height: 200px;
        }

        .message-input:focus {
            border-color: var(--accent);
        }

        .message-input::placeholder {
            color: var(--text-secondary);
        }

        .send-button {
            position: absolute;
            right: 8px;
            bottom: 8px;
            width: 36px;
            height: 36px;
            background: var(--accent);
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .send-button:hover {
            background: #3a8eef;
        }

        .send-button:disabled {
            background: var(--border-color);
            cursor: not-allowed;
        }

        /* Typing indicator */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 16px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--text-secondary);
            border-radius: 50%;
            animation: typing 1.4s ease-in-out infinite;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: scale(1);
                opacity: 0.7;
            }
            30% {
                transform: scale(1.3);
                opacity: 1;
            }
        }

        /* Loading spinner */
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--accent);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <button class="new-chat-btn" onclick="createNewChat()">
                    <span>✏️</span>
                    <span>Obrolan baru</span>
                </button>
                <button class="search-btn" onclick="searchChats()">
                    <span>🔍</span>
                    <span>Cari obrolan</span>
                </button>
            </div>
            <div class="chat-list">
                <div class="chat-list-header">OBROLAN</div>
                <div id="chatList"></div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="chat-header">
                <div class="header-left">
                    <span style="font-size: 20px;">👤</span>
                    <h2>Tutup sidebar</h2>
                </div>
                <div class="model-selector" id="modelSelector">
                    <span>DeepSeek-R1</span>
                    <span>▼</span>
                </div>
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
                    <button class="send-button" id="sendButton" onclick="sendMessage()">
                        ➤
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        // Global variables
        let bridge = null;
        let currentChatId = null;
        let chats = [];
        let isStreaming = false;
        let currentAssistantMessage = null;

        // Initialize WebChannel
        new QWebChannel(qt.webChannelTransport, function(channel) {
            bridge = channel.objects.bridge;
            console.log("✅ Bridge connected");
            
            // Connect signals
            bridge.streamChunk.connect(onStreamChunk);
            bridge.streamFinished.connect(onStreamFinished);
            bridge.errorOccurred.connect(onError);
            bridge.themeChanged.connect(onThemeChanged);
            
            // Initialize
            initialize();
        });

        function initialize() {
            // Get system info
            bridge.getSystemInfo(function(info) {
                const sysInfo = JSON.parse(info);
                console.log("System info:", sysInfo);
                updateModelName(sysInfo.model_name);
            });
            
            // Load chat history
            loadChatHistory();
            
            // Focus input
            document.getElementById('messageInput').focus();
        }

        function loadChatHistory() {
            bridge.getChatHistory(function(history) {
                const messages = JSON.parse(history);
                if (messages.length > 0) {
                    // Group messages by conversation
                    updateChatList();
                    displayMessages(messages);
                }
            });
        }

        function updateChatList() {
            const chatList = document.getElementById('chatList');
            chatList.innerHTML = '';
            
            // Add sample chats
            const sampleChats = [
                'Obrolan Baru',
                'Obrolan Baru',
                'Obrolan Baru',
                'tes'
            ];
            
            sampleChats.forEach((chat, index) => {
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                if (index === 3) chatItem.className += ' active';
                chatItem.textContent = chat;
                chatItem.onclick = () => selectChat(index);
                chatList.appendChild(chatItem);
            });
        }

        function selectChat(index) {
            // Update active state
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.classList.add('active');
        }

        function createNewChat() {
            // Clear messages
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.innerHTML = `
                <div class="empty-state">
                    <h1>Apa yang bisa saya bantu?</h1>
                    <p>Mulai percakapan baru dengan mengetik pesan di bawah</p>
                </div>
            `;
            
            // Clear chat in backend
            bridge.clearChat();
            
            // Focus input
            document.getElementById('messageInput').focus();
        }

        function searchChats() {
            // TODO: Implement search functionality
            console.log('Search chats');
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isStreaming) return;
            
            // Clear input
            input.value = '';
            autoResize(input);
            
            // Remove empty state if exists
            const emptyState = document.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            
            // Add user message to UI
            addMessage(message, 'user');
            
            // Add AI message placeholder
            addMessage('', 'assistant');
            
            // Disable send button
            isStreaming = true;
            document.getElementById('sendButton').disabled = true;
            
            // Send to backend
            bridge.sendMessage(message);
        }

        function addMessage(content, role) {
            const messagesDiv = document.getElementById('chatMessages');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const avatar = role === 'user' ? '👤' : '🤖';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${content || '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>'}</div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            
            if (role === 'assistant') {
                currentAssistantMessage = messageDiv.querySelector('.message-content');
            }
            
            // Scroll to bottom
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function onStreamChunk(chunk) {
            if (currentAssistantMessage) {
                // Remove typing indicator if present
                const typingIndicator = currentAssistantMessage.querySelector('.typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                
                // Append chunk
                currentAssistantMessage.innerHTML += chunk;
                
                // Scroll to bottom
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }

        function onStreamFinished(response) {
            isStreaming = false;
            document.getElementById('sendButton').disabled = false;
            currentAssistantMessage = null;
            
            // Focus back to input
            document.getElementById('messageInput').focus();
        }

        function onError(error) {
            console.error('Error:', error);
            
            if (currentAssistantMessage) {
                currentAssistantMessage.innerHTML = `<span style="color: #ff4444;">Error: ${error}</span>`;
            }
            
            isStreaming = false;
            document.getElementById('sendButton').disabled = false;
        }

        function onThemeChanged(isDark) {
            // Update theme if needed
            console.log('Theme changed:', isDark);
        }

        function displayMessages(messages) {
            const messagesDiv = document.getElementById('chatMessages');
            messagesDiv.innerHTML = '';
            
            messages.forEach(msg => {
                addMessage(msg.content, msg.role);
            });
        }

        function updateModelName(modelName) {
            const modelSelector = document.getElementById('modelSelector');
            if (modelName && modelName !== 'unknown') {
                modelSelector.innerHTML = `<span>${modelName}</span><span>▼</span>`;
            }
        }

        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function autoResize(textarea) {
            textarea.style.height = 'auto';
            const newHeight = Math.min(textarea.scrollHeight, 200);
            textarea.style.height = newHeight + 'px';
        }

        // Auto-focus on load
        window.onload = function() {
            document.getElementById('messageInput').focus();
        };
    </script>
</body>
</html>'''