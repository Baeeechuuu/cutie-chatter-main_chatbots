# web_ui/chat_bridge.py

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import json
import sys
import os

# Add parent directory to path to import backends
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backends import OllamaWorker
    BACKENDS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import OllamaWorker from backends: {e}")
    BACKENDS_AVAILABLE = False


class ChatBridge(QObject):
    """Bridge untuk komunikasi antara JavaScript dan Python"""
    
    # Signals untuk komunikasi dengan JavaScript
    messageReceived = pyqtSignal(str)
    responseReady = pyqtSignal(str)
    streamChunk = pyqtSignal(str)
    streamFinished = pyqtSignal(str)
    themeChanged = pyqtSignal(bool)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.ollama_worker = None
        self.ollama_thread = None
        self.is_streaming = False
        
    @pyqtSlot(str)
    def sendMessage(self, message):
        """Terima pesan dari JavaScript dan proses dengan Ollama"""
        try:
            print(f"📥 Received message from web: {message}")
            
            if not self.parent_app:
                self.errorOccurred.emit("Parent application not available")
                return
                
            if not BACKENDS_AVAILABLE:
                self.errorOccurred.emit("Backends module not available")
                return
                
            # Process message dengan streaming
            self.processMessageStreaming(message)
            
        except Exception as e:
            print(f"❌ Error in sendMessage: {e}")
            self.errorOccurred.emit(str(e))
    
    def processMessageStreaming(self, message):
        """Process message dengan streaming response"""
        try:
            if self.is_streaming:
                print("⚠️ Already streaming, please wait...")
                return
                
            # Add to conversation history
            self.parent_app.conversation_history.append({
                'role': 'user', 
                'content': message
            })
            
            # Sentiment analysis if available
            if hasattr(self.parent_app, 'classifier') and self.parent_app.classifier:
                try:
                    sentiment = self.parent_app.GetSentimentOnPrimary(message)
                    print(f"📊 User sentiment: {sentiment}")
                    self.parent_app.user_text_metadata.append(message)
                    self.parent_app.user_features_metadata.append(sentiment)
                except Exception as e:
                    print(f"Sentiment analysis error: {e}")
            
            # Start Ollama streaming
            self.startOllamaStreaming()
            
        except Exception as e:
            print(f"❌ Error in processMessageStreaming: {e}")
            self.errorOccurred.emit(str(e))
            self.streamFinished.emit("")
    
    def startOllamaStreaming(self):
        """Start Ollama worker for streaming response"""
        try:
            # Stop existing worker if any
            if self.ollama_thread and self.ollama_thread.isRunning():
                print("🛑 Stopping existing thread...")
                self.ollama_thread.quit()
                self.ollama_thread.wait(2000)
            
            # Disconnect previous signals
            if self.ollama_worker:
                try:
                    self.ollama_worker.chunk_received.disconnect()
                    self.ollama_worker.finished.disconnect()
                except:
                    pass
            
            self.is_streaming = True
            
            # Create new worker and thread
            self.ollama_thread = QThread()
            self.ollama_worker = OllamaWorker(
                self.parent_app.conversation_history[-1]['content'],
                self.parent_app.conversation_history.copy(),
                self.parent_app.model_name
            )
            
            # Move worker to thread
            self.ollama_worker.moveToThread(self.ollama_thread)
            
            # Connect signals
            self.ollama_worker.chunk_received.connect(self.onChunkReceived)
            self.ollama_worker.finished.connect(self.onResponseComplete)
            self.ollama_thread.started.connect(self.ollama_worker.run)
            
            # Start thread
            self.ollama_thread.start()
            print("🚀 Ollama streaming started")
            
        except Exception as e:
            print(f"❌ Error starting Ollama: {e}")
            self.is_streaming = False
            self.errorOccurred.emit(str(e))
            self.streamFinished.emit("")
    
    def onChunkReceived(self, chunk):
        """Handle chunk received from Ollama"""
        # Emit to JavaScript
        self.streamChunk.emit(chunk)
    
    def onResponseComplete(self, full_response):
        """Handle complete response from Ollama"""
        try:
            # Clean response
            cleaned_response = self.cleanResponse(full_response)
            
            # Add to conversation history
            self.parent_app.conversation_history.append({
                'role': 'assistant',
                'content': cleaned_response
            })
            
            # Sentiment analysis for AI response
            if hasattr(self.parent_app, 'classifier') and self.parent_app.classifier:
                try:
                    ai_sentiment = self.parent_app.GetSentimentOnPrimary(cleaned_response)
                    print(f"🤖 AI sentiment: {ai_sentiment}")
                    self.parent_app.ai_text_metadata.append(cleaned_response)
                    self.parent_app.ai_features_metadata.append(ai_sentiment)
                except Exception as e:
                    print(f"AI sentiment analysis error: {e}")
            
            # Clean up thread
            if self.ollama_thread:
                self.ollama_thread.quit()
                self.ollama_thread.wait()
                self.ollama_thread = None
            
            self.ollama_worker = None
            self.is_streaming = False
            
            # Emit finished signal
            self.streamFinished.emit(cleaned_response)
            print("✅ Response complete")
            
        except Exception as e:
            print(f"❌ Error in response completion: {e}")
            self.is_streaming = False
            self.errorOccurred.emit(str(e))
    
    def cleanResponse(self, text):
        """Clean response text"""
        if hasattr(self.parent_app, 'naked_text'):
            return self.parent_app.naked_text(text)
        return text
    
    @pyqtSlot(result=str)
    def getSystemInfo(self):
        """Get system information for JavaScript"""
        try:
            info = {
                "model_name": self.parent_app.model_name if self.parent_app else "unknown",
                "dark_theme": self.parent_app.is_dark_theme if hasattr(self.parent_app, 'is_dark_theme') else True,
                "backends_available": BACKENDS_AVAILABLE,
                "sentiment_available": hasattr(self.parent_app, 'classifier') and self.parent_app.classifier is not None
            }
            return json.dumps(info)
        except Exception as e:
            print(f"Error getting system info: {e}")
            return json.dumps({"error": str(e)})
    
    @pyqtSlot()
    def toggleTheme(self):
        """Toggle theme from JavaScript"""
        if self.parent_app and hasattr(self.parent_app, 'toggle_theme'):
            self.parent_app.toggle_theme()
    
    @pyqtSlot(result=str)
    def getChatHistory(self):
        """Get conversation history for JavaScript"""
        try:
            if self.parent_app:
                # Filter out system messages for display
                history = [msg for msg in self.parent_app.conversation_history if msg['role'] != 'system']
                return json.dumps(history)
            return json.dumps([])
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return json.dumps([])
    
    @pyqtSlot()
    def clearChat(self):
        """Clear chat history"""
        if self.parent_app and hasattr(self.parent_app, 'clear_conversation_history'):
            self.parent_app.clear_conversation_history()