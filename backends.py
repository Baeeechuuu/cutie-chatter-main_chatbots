from PyQt6.QtWidgets import (
    QVBoxLayout, 
    QWidget, 
    QScrollArea, 
    QFrame, 
    QLabel,
    QGraphicsOpacityEffect,
    QApplication,
    QPushButton,
    QHBoxLayout
)
from PyQt6.QtCore import (
    Qt, 
    QPropertyAnimation,
    QObject,
    QMetaObject,
    pyqtSignal,
    QUrl,
    QThread
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QIcon
from ocr.docreader import TextExtractor
from transformers import TextIteratorStreamer
import multiprocessing, ollama, re, sys, os, subprocess, random, torch
import torch.nn.functional as F
from threading import Thread
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from torch.autograd.functional import hessian

# Import TTS components
try:
    from tts.tts_engine import TTSEngine, TTSWorker
    TTS_AVAILABLE = True
except ImportError:
    print("TTS module not available. TTS functionality will be disabled.")
    TTS_AVAILABLE = False

'''
    Chat Widget with TTS Support
'''

class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.current_ai_message = None
        self.current_ai_message_widget = None
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("chat_frame")
        self.chat_frame = QFrame(self)
        self.chat_frame.setObjectName("chat_frame")
        self.chat_layout = QVBoxLayout(self.chat_frame)
        self.chat_frame.setLayout(self.chat_layout)
        self.scroll_area.setWidget(self.chat_frame)
        self.layout().addWidget(self.scroll_area)
        
        # TTS setup
        self.tts_engine = None
        self.media_player = None
        self.audio_output = None
        self.setup_tts()

    def setup_tts(self):
        """Setup TTS engine and audio player"""
        if TTS_AVAILABLE:
            try:
                # Initialize TTS engine
                model_path = "./model-train/model_checkpoints/best_model.pt"
                self.tts_engine = TTSEngine(model_path)
                
                # Setup audio player
                self.media_player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.media_player.setAudioOutput(self.audio_output)
                
                print("TTS system initialized successfully")
            except Exception as e:
                print(f"Error initializing TTS: {e}")
                self.tts_engine = None

    def add_user_message(self, message):
        label = QLabel(f"{message}", self)
        label.setWordWrap(True)
        label.setObjectName("user_response")
        self.chat_layout.addWidget(label)
        self.scroll_to_bottom()

    def start_ai_message(self):
        # Create container widget for AI message and TTS button
        self.current_ai_message_widget = QWidget(self)
        ai_message_layout = QVBoxLayout(self.current_ai_message_widget)
        ai_message_layout.setContentsMargins(0, 0, 0, 5)
        
        # Create the text label
        self.current_ai_message = QLabel(self)
        self.current_ai_message.setWordWrap(True)
        self.current_ai_message.setObjectName("ai_response")
        self.current_ai_message.setTextFormat(Qt.TextFormat.RichText)
        
        # Create TTS controls container
        tts_container = QWidget(self)
        tts_layout = QHBoxLayout(tts_container)
        tts_layout.setContentsMargins(0, 5, 0, 0)
        tts_layout.addStretch()  # Push button to the right
        
        # Create TTS button
        if self.tts_engine:
            self.tts_button = QPushButton("🔊 Play", self)
            self.tts_button.setObjectName("tts_button")
            self.tts_button.setMaximumWidth(100)
            self.tts_button.clicked.connect(self.play_ai_message)
            tts_layout.addWidget(self.tts_button)
        
        # Add to layout
        ai_message_layout.addWidget(self.current_ai_message)
        ai_message_layout.addWidget(tts_container)
        
        self.chat_layout.addWidget(self.current_ai_message_widget)
        self.fade_in(self.current_ai_message_widget)
        self.scroll_to_bottom()

    def append_to_ai_message(self, processed_text):
        if not processed_text or not self.current_ai_message:
            return

        current_text = self.current_ai_message.text()
        self.current_ai_message.setText(current_text + processed_text)
        self.scroll_to_bottom()

    def play_ai_message(self):
        """Play the current AI message using TTS"""
        if not self.tts_engine or not self.current_ai_message:
            return
        
        try:
            # Get the text content without HTML tags
            text = self.current_ai_message.text()
            text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
            
            if not text.strip():
                return
            
            # Update button state
            self.tts_button.setText("🎵 Playing...")
            self.tts_button.setEnabled(False)
            
            # Create TTS worker
            self.tts_worker = TTSWorker(self.tts_engine, text)
            self.tts_worker.audio_ready.connect(self.play_audio)
            self.tts_worker.error_occurred.connect(self.tts_error)
            
            # Start TTS in separate thread
            self.tts_thread = Thread(target=self.tts_worker.run)
            self.tts_thread.start()
            
        except Exception as e:
            print(f"Error playing TTS: {e}")
            self.tts_button.setText("🔊 Play")
            self.tts_button.setEnabled(True)

    def play_audio(self, audio_path):
        """Play the generated audio file"""
        try:
            if self.media_player and os.path.exists(audio_path):
                # Set up media player
                self.media_player.setSource(QUrl.fromLocalFile(audio_path))
                self.media_player.mediaStatusChanged.connect(self.audio_finished)
                self.media_player.play()
            else:
                self.tts_error("Audio file not found")
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.tts_error(str(e))

    def audio_finished(self, status):
        """Handle audio playback finished"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.tts_button.setText("🔊 Play")
            self.tts_button.setEnabled(True)

    def tts_error(self, error_msg):
        """Handle TTS errors"""
        print(f"TTS Error: {error_msg}")
        self.tts_button.setText("🔊 Error")
        self.tts_button.setEnabled(True)
    
    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        self.scroll_area.setObjectName("scroll_area")

    def fade_in(self, widget):
        self.effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(2000)   
        self.animation.setStartValue(0.0)   
        self.animation.setEndValue(1.0)   
        self.animation.start()

'''
    Text Cleaner Class - FIXED VERSION
'''

class TextCleaner():
    def __init__(self, text):
        self.text_to_be_cleaned = text

    def replace_italic_text(self, text):
        return re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    def replace_think_tags(self, text):
        text = re.sub(r'<\s*/\s*div\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*button\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '</think', text)
        text = re.sub(r'<\s*/\s*br\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*Compose\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*think\s*>', '<span style="font-style: italic; font-weight: 200;">', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '</span><br><br>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        return text
    
    def response_only(self, text):
        """Extract only the response content, removing thinking sections - FIXED FOR DEEPSEEK"""
        if not text:
            return text
        
        # DeepSeek-R1 specific: Find the actual response after thinking
        # Look for common patterns that indicate end of thinking
        patterns = [
            r'</think>\s*',
            r'<think>.*?</think>',  # Remove think blocks
            r'Alright,.*?\n\n',
            r'I should.*?\n\n',
            r'Let me.*?\n\n',
            r'Hmm.*?\n\n',
            r'Okay.*?\n\n',
            r'I want to.*?\n\n',
            r'I need to.*?\n\n',
            r'Actually.*?\n\n',
        ]
        
        cleaned_text = text
        
        # First, try to find </think> tag and get everything after it
        think_end = cleaned_text.find('</think>')
        if think_end != -1:
            cleaned_text = cleaned_text[think_end + 8:].strip()
            return cleaned_text
        
        # If no </think>, try to remove thinking patterns
        for pattern in patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        # If text still looks like thinking, try to extract the last meaningful sentence
        if any(keyword in cleaned_text.lower()[:50] for keyword in ['let me', 'i should', 'hmm', 'alright', 'actually']):
            sentences = cleaned_text.split('. ')
            # Find the last sentence that doesn't look like thinking
            for i in range(len(sentences) - 1, -1, -1):
                sentence = sentences[i].strip()
                if sentence and not any(keyword in sentence.lower() for keyword in ['let me', 'i should', 'hmm']):
                    cleaned_text = sentence
                    if not cleaned_text.endswith('.'):
                        cleaned_text += '.'
                    break
        
        # Final cleanup
        cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)  # Remove any HTML tags
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace
        cleaned_text = cleaned_text.strip()
        
        # If we end up with very short text, it might be an error
        if len(cleaned_text) < 10 and len(text) > 100:
            # Return a simple greeting as fallback
            return "Halo! Ada yang bisa saya bantu?"
        
        return cleaned_text

    def process_content(self, text):
        """Process content for display"""
        if not text:
            return text
        processed = self.text_to_be_cleaned.replace('\n', '<br>')
        processed = self.replace_italic_text(processed)
        processed = self.replace_think_tags(processed)
        return processed

'''
    Ollama Worker For direct conversation - FINAL FIXED VERSION
'''

class OllamaWorker(QObject):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, user_message, conversation_history, model_name):
        super().__init__()
        self.user_message = user_message
        self.conversation_history = conversation_history.copy()
        self.num_threads = max(1, multiprocessing.cpu_count() // 2)
        self.model_name = model_name

    def run(self):
        try:
            print(f"🤖 OllamaWorker running: {self.model_name}")
            print(f"📝 Conversation history length: {len(self.conversation_history)}")
            
            # Test connection first
            try:
                ollama.list()
            except Exception as e:
                error_msg = f"❌ Ollama tidak bisa diakses: {str(e)}"
                print(error_msg)
                self.chunk_received.emit(error_msg)
                self.finished.emit(error_msg)
                return
            
            # Check if this is DeepSeek model
            is_deepseek = 'deepseek' in self.model_name.lower()
            
            # Start streaming with appropriate options
            stream = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=True,
                options={
                    "num_thread": self.num_threads,
                    "temperature": 0.7 if is_deepseek else 1.1,
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_ctx": 2048,
                    "num_batch": 512,
                    "repeat_penalty": 1.1,
                    "stop": ["</think>", "\nHuman:", "\nUser:"] if is_deepseek else []
                }
            )
            
            full_content = ''
            received_chunks = 0
            buffer = ''
            response_started = False
            
            print("🚀 Starting streaming...")
            
            for chunk in stream:
                try:
                    content = chunk.get('message', {}).get('content', '')
                    
                    if content:
                        full_content += content
                        received_chunks += 1
                        
                        if is_deepseek:
                            buffer += content
                            
                            # Check if we should start showing response
                            if not response_started:
                                if '</think>' in buffer or len(buffer) > 1000:
                                    # Extract actual response
                                    text_cleaner = TextCleaner(buffer)
                                    actual_response = text_cleaner.response_only(buffer)
                                    
                                    if actual_response and len(actual_response) > 10:
                                        response_started = True
                                        self.chunk_received.emit(actual_response)
                                        buffer = ''  # Clear buffer
                            else:
                                # We're in the response part, emit directly
                                self.chunk_received.emit(content)
                        else:
                            # Non-DeepSeek models - process normally
                            try:
                                processor = TextCleaner(content)
                                processed = processor.process_content(content)
                                self.chunk_received.emit(processed)
                            except:
                                self.chunk_received.emit(content)
                        
                        # Log progress every 10 chunks
                        if received_chunks % 10 == 0:
                            print(f"📥 Received {received_chunks} chunks...")
                    
                    # Check if done
                    if chunk.get('done', False):
                        print("✅ Stream completed")
                        break
                        
                except Exception as chunk_error:
                    print(f"⚠️ Chunk error: {chunk_error}")
                    continue
            
            print(f"🏁 Total: {received_chunks} chunks, {len(full_content)} chars")
            
            # Final processing for DeepSeek
            if is_deepseek:
                text_cleaner = TextCleaner(full_content)
                final_response = text_cleaner.response_only(full_content)
                
                # If we never started response, emit the cleaned version now
                if not response_started and final_response:
                    self.chunk_received.emit(final_response)
            else:
                final_response = full_content
            
            # Emit the complete response
            if final_response and final_response.strip():
                self.finished.emit(final_response)
            else:
                self.finished.emit("Halo! Ada yang bisa saya bantu?")

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            print(f"❌ OllamaWorker error: {e}")
            import traceback
            traceback.print_exc()
            self.chunk_received.emit(error_msg)
            self.finished.emit(error_msg)

'''
    OCR Worker for Document Extraction
'''

class OllamaOCRWorker(QObject):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    request_file_dialog = pyqtSignal()

    def __init__(self, user_message, conversation_history, model_name):
        super().__init__()
        self.user_message = user_message
        self.conversation_history = conversation_history.copy()
        self.num_threads = multiprocessing.cpu_count() 
        self.text_extractor = TextExtractor()
        self.file_path = None
        self.model_name = model_name

    def set_file_path(self, path):
        self.file_path = path
        if self.file_path:
            self.process_file()

    def run(self):
        self.request_file_dialog.emit()

    def process_file(self):
        try:
            if not self.file_path:
                self.chunk_received.emit("No file selected.")
                self.finished.emit("")
                return
            
            pdf_name = os.path.basename(self.file_path)
            
            if not os.path.exists(self.file_path):
                self.chunk_received.emit("The file does not exist.")
                self.finished.emit("")
                return
            
            extracted_text = self.text_extractor.extract_text_from_pdf(self.file_path)
            
            if not extracted_text:
                self.chunk_received.emit("Failed to extract text from PDF.")
                self.finished.emit("")
                return

            self.conversation_history.append({
                'role': 'user', 
                'content': f"File : {pdf_name}, Content : {extracted_text}"
            })

            stream = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=True,
                options={
                    "num_thread": self.num_threads,
                    "temperature": 2.52,
                    "top_n": 121,
                    "f16_kv": True,
                    "num_ctx": 1024*2,
                    "num_batch": 8,
                    "num_prediction": 1024*2
                }
            )            
            full_content = ''
            for chunk in stream:
                content = chunk['message']['content']
                full_content += content
                string_processor = TextCleaner(content)
                processed_content = string_processor.process_content(content)
                self.chunk_received.emit(processed_content)
            
            self.finished.emit(full_content)

        except Exception as e:
            print(f"Error in OllamaOCRWorker: {e}")
            self.chunk_received.emit(f"Error processing document: {str(e)}")
            self.finished.emit("")

'''
    QWEN WORKER [Research]
'''

class QwenWorker(QObject):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, model, tokenizer, user_message, conversation_history, vector_amplification=48, max_new_tokens=64, context_length=1024, emotion_vectors=None):
        super().__init__()

        self.max_new_tokens = max_new_tokens
        self.context_length = context_length
        self.conversation_history = conversation_history.copy()
        self.user_message = user_message
        self.tokenizer = tokenizer
        self.model = model
        self.model.config.output_attentions = True
        self.device = self.model.device
        self.injection_vectors = emotion_vectors
        self.response_started = False
        self.hook_handles = []
        self.num_amplification = vector_amplification
        self.bias_embedding = None
        if self.injection_vectors is not None:
            self._precompute_bias_embedding()

    def _precompute_bias_embedding(self):
        try:
            amplified_injection_vectors = [vec for vec in self.injection_vectors for _ in range(self.num_amplification)]

            batch_inputs = self.tokenizer(
                amplified_injection_vectors,   
                return_tensors="pt", 
                padding=True, 
                truncation=True
            )
            input_ids = batch_inputs.input_ids.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.base_model(input_ids=input_ids)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                self.bias_embedding = torch.max(embeddings, dim=0)[0]
                print(self.bias_embedding)
                self.bias_embedding = F.normalize(self.bias_embedding, p=2, dim=-1)

        except Exception as e:
            print(f"Error precomputing bias_embedding: {e}")
            self.bias_embedding = None

    def run(self, bias=3.5, hs_scaling=3.5):
        try:
            return self.generate_response(bias, hs_scaling)
        except Exception as e:
            print(f"Error in run: {e}")
            self.finished.emit("")
            return ""
            
    def generate_response(self, bias, hs_scaling):
        self.inputs = self.tokenizer(
            self._format_conversation(self.conversation_history),
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.context_length,
            return_attention_mask=True
        )

        input_ids = self.inputs.input_ids.to(self.device)
        attention_mask = self.inputs.attention_mask.to(self.device)

        if self.injection_vectors is not None and self.bias_embedding is not None:
            self._setup_emotion_hooks(bias, hs_scaling)

        try:
            streamer = TextIteratorStreamer(self.tokenizer)
            
            generation_kwargs = {
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'max_new_tokens': self.max_new_tokens,
                'num_return_sequences': 1,
                'pad_token_id': self.tokenizer.pad_token_id,
                'do_sample': True,
                'temperature': 1.0,
                'no_repeat_ngram_size': 5,
                'repetition_penalty': 1.1,
                'streamer': streamer,
                'top_k': 10,
                'top_p': 0.15,
                'early_stopping': True,
                'min_length': 1,
                'forced_bos_token_id': self.tokenizer.bos_token_id,
                'forced_eos_token_id': self.tokenizer.eos_token_id,
                'output_attentions': True
            }
            assistant_pattern = re.compile(r'<\|assistant\|>\n')
            
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()

            full_content = []
            for new_text in streamer:
                content = new_text.get('content', '') if isinstance(new_text, dict) else new_text

                if not self.response_started:
                    match = assistant_pattern.search(content)
                    if match:
                        content = content[match.end():]
                        self.response_started = True
                    else:
                        continue

                if content:   
                    full_content.append(content)
                    cleaned_content = self._clean_response(content)
                    if cleaned_content:
                        self.chunk_received.emit(cleaned_content)

            self._cleanup_hooks()
    
            cleaned_full_content = self._clean_response(''.join(full_content))
            self.finished.emit(cleaned_full_content)
            return cleaned_full_content

        except Exception as e:
            print(f"Error in generate_response: {e}")
            self._cleanup_hooks()
            self.finished.emit("")
            return ""

    def compute_pca(self, dataloader, num_samples=1000, variance_threshold=0.95):
        """Compute PCA parameters using hidden states from the dataloader"""
        hidden_states = []
        hook_handles = []
        layers = self.model.model.layers
        target_modules = []
        for i in range(len(layers)):
            if i % 2 == 0:
                target_modules.append(layers[i].mlp)
            else:
                target_modules.append(layers[i].self_attn)

        def hook(module, input, output):
            hidden_states.append(output[0].cpu())   

        for module in target_modules:
            handle = module.register_forward_hook(hook)
            hook_handles.append(handle)

        self.model.eval()
        with torch.no_grad():
            for batch in dataloader:
                inputs = batch[0].to(self.device)
                self.model(inputs)
                if len(hidden_states) >= num_samples:
                    break

        for handle in hook_handles:
            handle.remove()

        hidden_states = torch.cat(hidden_states, dim=0)
        hidden_states = hidden_states.view(-1, hidden_states.size(-1))   
        mu = hidden_states.mean(dim=0)
        centered = hidden_states - mu
        cov = torch.matmul(centered.T, centered) / (centered.size(0) - 1)
        eigenvalues, eigenvectors = torch.linalg.eigh(cov)
        sorted_indices = torch.argsort(eigenvalues, descending=True)
        eigenvectors = eigenvectors[:, sorted_indices]
        eigenvalues = eigenvalues[sorted_indices]
        total_var = eigenvalues.sum()
        var_ratio = eigenvalues.cumsum(0) / total_var
        k = (var_ratio < variance_threshold).sum() + 1
        V = eigenvectors[:, :k]
        self.pca_mu = mu.to(self.device)
        self.pca_V = V.to(self.device)

    def _setup_emotion_hooks(self, bias, hs_scaling):
        """Set up emotion injection hooks with PCA-based steering"""
        try:
            bias_embedding = self.bias_embedding.to(dtype=torch.float16)
            bias_embedding = F.normalize(bias_embedding, p=2, dim=-1)
            if not hasattr(self, 'pca_mu') or not hasattr(self, 'pca_V'):
                raise ValueError("PCA parameters not computed. Call compute_pca() first.")

            @torch.no_grad()
            def pca_steering_hook(module, input, output):
                hidden_states = output[0]  
                batch, seq, dim = hidden_states.shape
                h_flat = hidden_states.view(-1, dim)
                centered = h_flat - self.pca_mu
                h_pca = torch.matmul(centered, self.pca_V)
                bias_centered = bias_embedding - self.pca_mu
                bias_pca = torch.matmul(bias_centered, self.pca_V)
                std = h_flat.std(dim=-1, keepdim=True)
                global_std = h_flat.std()
                alpha = torch.sigmoid((std / global_std) * hs_scaling)
                expanded_bias = bias_pca.unsqueeze(0).unsqueeze(0).expand(batch, seq, -1)
                modified_pca = h_pca.view(batch, seq, -1) + alpha * (bias * expanded_bias.to(hidden_states.device))
                reconstructed_centered = torch.matmul(modified_pca.view(-1, modified_pca.size(-1)), self.pca_V.T)
                reconstructed = reconstructed_centered + self.pca_mu
                modified_hidden = reconstructed.view(batch, seq, dim)

                return (modified_hidden,) + output[1:]

            layers = self.model.model.layers
            for i in range(min(len(layers), 24)):  
                target_layer = layers[i]
                hook_target = target_layer.mlp if i % 2 == 0 else target_layer.self_attn
                self.hook_handles.append(hook_target.register_forward_hook(pca_steering_hook))

        except Exception as e:
            print(f"Error in PCA-based emotion setup: {e}")
            self._cleanup_hooks()

    def _cleanup_hooks(self):
        """Clean up all hook handles"""
        for handle in self.hook_handles:
            handle.remove()
        self.hook_handles = []

    @torch.no_grad()
    def get_embeddings(self, text):
        """Get embeddings for a single text input"""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        input_ids = inputs.input_ids.to(self.device)
        outputs = self.model.base_model(input_ids=input_ids)
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings

    def _format_conversation(self, messages):
        """Format the conversation history"""
        parts = []
        for message in messages:
            parts.append(f"<|{message['role']}|>\n{message['content']}\n")
        parts.append("<|assistant|>\n")
        return "".join(parts)

    def _clean_response(self, text):
        """Clean response text by removing special tokens and emojis"""
        text = re.sub(r'<\|[^|]+\|>', '', text)
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # Emoticons
            u"\U0001F300-\U0001F5FF"  # Symbols & Pictographs
            u"\U0001F680-\U0001F6FF"  # Transport & Map Symbols
            u"\U0001F700-\U0001F77F"  # Alchemical Symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251"  # Enclosed Characters
            "]+", flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
        
        return text