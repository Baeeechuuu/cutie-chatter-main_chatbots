import torch
import torch.nn as nn
import torchaudio
import soundfile as sf
import numpy as np
from transformers import AutoTokenizer
from pathlib import Path
import logging
import threading
import queue
import time
from typing import Dict, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSModel(nn.Module):
    """TTS Model for inference - same architecture as training"""
    
    def __init__(self, vocab_size: int, mel_dim: int = 80, hidden_dim: int = 256):
        super().__init__()
        
        self.vocab_size = vocab_size
        self.mel_dim = mel_dim
        self.hidden_dim = hidden_dim
        
        # Text encoder
        self.text_embedding = nn.Embedding(vocab_size, hidden_dim)
        self.text_encoder = nn.LSTM(hidden_dim, hidden_dim, batch_first=True, bidirectional=True)
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(hidden_dim * 2, num_heads=8, batch_first=True)
        
        # Decoder
        self.decoder_lstm = nn.LSTM(hidden_dim * 2 + mel_dim, hidden_dim, batch_first=True)
        self.mel_projection = nn.Linear(hidden_dim, mel_dim)
        
        # Stop token predictor
        self.stop_projection = nn.Linear(hidden_dim, 1)
        
        # Speaker embedding
        self.speaker_embedding = nn.Embedding(100, hidden_dim)
        
    def forward(self, text_tokens: torch.Tensor, mel_target: torch.Tensor = None, 
                speaker_id: torch.Tensor = None) -> Dict:
        
        batch_size, text_len = text_tokens.shape
        
        # Text encoding
        text_emb = self.text_embedding(text_tokens)
        
        # Add speaker embedding if provided
        if speaker_id is not None:
            speaker_emb = self.speaker_embedding(speaker_id).unsqueeze(1).expand(-1, text_len, -1)
            text_emb = text_emb + speaker_emb
            
        text_encoded, _ = self.text_encoder(text_emb)
        
        # Inference mode
        max_len = min(1000, text_len * 10)  # More reasonable max length
        mel_outputs = []
        stop_outputs = []
        
        decoder_input = torch.zeros(batch_size, 1, self.mel_dim, device=text_tokens.device)
        
        for i in range(max_len):
            # Apply attention
            attended, attention_weights = self.attention(decoder_input, text_encoded, text_encoded)
            
            # Decode one step
            decoder_input_combined = torch.cat([attended, decoder_input], dim=-1)
            decoder_output, _ = self.decoder_lstm(decoder_input_combined)
            
            mel_output = self.mel_projection(decoder_output)
            stop_output = self.stop_projection(decoder_output)
            
            mel_outputs.append(mel_output)
            stop_outputs.append(stop_output)
            
            # Update decoder input for next step
            decoder_input = mel_output
            
            # Check stop condition
            if torch.sigmoid(stop_output).item() > 0.5:
                break
        
        # Ensure we have at least some output
        if not mel_outputs:
            mel_outputs = [torch.randn(batch_size, 1, self.mel_dim, device=text_tokens.device)]
            stop_outputs = [torch.zeros(batch_size, 1, 1, device=text_tokens.device)]
        
        return {
            'mel_output': torch.cat(mel_outputs, dim=1),  # Fixed dimension
            'stop_output': torch.cat(stop_outputs, dim=1),
            'attention_weights': attention_weights
        }

class MelToAudio:
    """Convert mel spectrogram to audio using Griffin-Lim algorithm"""
    
    def __init__(self, sample_rate: int = 22050, n_fft: int = 1024, hop_length: int = 256):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        
        # Griffin-Lim transform
        self.griffin_lim = torchaudio.transforms.GriffinLim(
            n_fft=n_fft,
            hop_length=hop_length,
            n_iter=60,  # More iterations for better quality
            power=1.0
        )
        
        # Inverse mel transform
        self.inverse_mel = torchaudio.transforms.InverseMelScale(
            n_stft=n_fft // 2 + 1,
            n_mels=80,
            sample_rate=sample_rate,
            f_min=0.0,
            f_max=8000.0
        )
    
    def convert(self, mel_spectrogram: torch.Tensor) -> torch.Tensor:
        """Convert mel spectrogram to audio waveform"""
        try:
            logger.info(f"Converting mel spectrogram shape: {mel_spectrogram.shape}")
            
            # Ensure proper dimensions
            if mel_spectrogram.dim() == 2:
                mel_spectrogram = mel_spectrogram.unsqueeze(0)  # Add batch dimension
            
            # Ensure mel is in the right range (log mel to linear mel)
            mel_linear = torch.exp(torch.clamp(mel_spectrogram, max=10))  # Clamp to prevent overflow
            
            # Convert mel to spectrogram
            spectrogram = self.inverse_mel(mel_linear)
            
            # Ensure spectrogram is positive
            spectrogram = torch.clamp(spectrogram, min=1e-10)
            
            # Convert spectrogram to audio using Griffin-Lim
            audio = self.griffin_lim(spectrogram)
            
            # Remove batch dimension if present
            if audio.dim() == 2 and audio.shape[0] == 1:
                audio = audio.squeeze(0)
            
            logger.info(f"Generated audio shape: {audio.shape}")
            return audio
            
        except Exception as e:
            logger.error(f"Error converting mel to audio: {e}")
            # Return meaningful test audio instead of silence
            return self.generate_test_tone()
    
    def generate_test_tone(self, duration: float = 2.0, frequency: float = 440.0) -> torch.Tensor:
        """Generate a test tone for debugging"""
        t = torch.linspace(0, duration, int(self.sample_rate * duration))
        audio = 0.3 * torch.sin(2 * torch.pi * frequency * t)
        logger.info("Generated test tone as fallback")
        return audio

class FallbackTTS:
    """Fallback TTS using system TTS or simple audio generation"""
    
    def __init__(self):
        self.sample_rate = 22050
        
    def generate_speech_audio(self, text: str, output_path: str) -> bool:
        """Generate speech audio using fallback methods"""
        
        # Method 1: Try pyttsx3
        if self._try_pyttsx3(text, output_path):
            return True
        
        # Method 2: Try gTTS
        if self._try_gtts(text, output_path):
            return True
        
        # Method 3: Generate tone-based "speech"
        return self._generate_tone_speech(text, output_path)
    
    def _try_pyttsx3(self, text: str, output_path: str) -> bool:
        """Try using pyttsx3 for TTS"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            
            # Convert to WAV format
            temp_file = output_path.replace('.wav', '_temp.wav')
            engine.save_to_file(text, temp_file)
            engine.runAndWait()
            
            # Check if file was created and has content
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1000:
                # Move to final location
                import shutil
                shutil.move(temp_file, output_path)
                logger.info("Generated audio using pyttsx3")
                return True
                
        except Exception as e:
            logger.warning(f"pyttsx3 failed: {e}")
        
        return False
    
    def _try_gtts(self, text: str, output_path: str) -> bool:
        """Try using Google TTS"""
        try:
            from gtts import gTTS
            from pydub import AudioSegment
            
            # Generate TTS
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save as MP3 first
            mp3_file = output_path.replace('.wav', '.mp3')
            tts.save(mp3_file)
            
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_file)
            audio.export(output_path, format="wav")
            
            # Clean up MP3
            os.remove(mp3_file)
            
            logger.info("Generated audio using gTTS")
            return True
            
        except Exception as e:
            logger.warning(f"gTTS failed: {e}")
        
        return False
    
    def _generate_tone_speech(self, text: str, output_path: str) -> bool:
        """Generate tone-based representation of speech"""
        try:
            # Create different tones for different characters
            duration = max(1.0, min(len(text) * 0.1, 5.0))  # 0.1s per character, max 5s
            
            # Generate multiple tones to simulate speech
            t = torch.linspace(0, duration, int(self.sample_rate * duration))
            audio = torch.zeros_like(t)
            
            # Add multiple frequency components
            base_freq = 200  # Base frequency
            
            for i, char in enumerate(text[:20]):  # Limit to first 20 characters
                char_freq = base_freq + (ord(char) % 100) * 2  # Variable frequency based on character
                start_time = i * duration / len(text)
                end_time = (i + 1) * duration / len(text)
                
                start_idx = int(start_time * self.sample_rate)
                end_idx = int(end_time * self.sample_rate)
                
                if end_idx > len(t):
                    end_idx = len(t)
                
                if start_idx < end_idx:
                    char_t = t[start_idx:end_idx]
                    char_audio = 0.2 * torch.sin(2 * torch.pi * char_freq * char_t)
                    audio[start_idx:end_idx] += char_audio
            
            # Add some envelope to make it sound more natural
            envelope = torch.exp(-t / duration * 2)  # Exponential decay
            audio = audio * envelope
            
            # Save audio
            torchaudio.save(output_path, audio.unsqueeze(0), self.sample_rate)
            
            logger.info("Generated tone-based speech audio")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate tone speech: {e}")
            return False

class TTSEngine:
    """Main TTS Engine class with improved error handling"""
    
    def __init__(self, model_path: str, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = Path(model_path) if model_path else None
        
        # Initialize fallback TTS
        self.fallback_tts = FallbackTTS()
        
        # Initialize tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            self.tokenizer = None
        
        # Initialize mel to audio converter
        self.mel_to_audio = MelToAudio()
        
        # Load model
        self.model = None
        self.model_loaded = False
        if self.model_path:
            self.load_model()
        
        # Speaker mapping
        self.speaker_mapping = self._create_speaker_mapping()
        
        logger.info(f"TTS Engine initialized on device: {self.device}")
    
    def _create_speaker_mapping(self) -> Dict[str, int]:
        """Create mapping from speaker names to IDs"""
        speakers = [
            "Paimon", "Traveler", "Venti", "Zhongli", "Childe", "Albedo",
            "Ganyu", "Xiao", "Keqing", "Mona", "Jean", "Diluc", "Kaeya",
            "Lisa", "Amber", "Barbara", "Fischl", "Noelle", "Bennett",
            "Razor", "Chongyun", "Xingqiu", "Sucrose", "Diona", "Tartaglia",
            "Xinyan", "Rosaria", "Hu Tao", "Yanfei", "Eula", "Kazuha",
            "Ayaka", "Yoimiya", "Sayu", "Kokomi", "Gorou", "Thoma",
            "Itto", "Yae Miko", "Ayato", "Yelan", "Shinobu", "Heizou",
            "Collei", "Tighnari", "Dori", "Candace", "Nilou", "Nahida",
            "Layla", "Faruzan", "Wanderer", "Alhaitham", "Yaoyao", "Baizhu",
            "Kaveh", "Kirara", "Lynette", "Lyney", "Freminet", "Furina",
            "Charlotte", "Neuvillette", "Wriothesley", "Xianyun", "Gaming",
            "Chevreuse", "Chiori", "Arlecchino"
        ]
        
        mapping = {}
        for i, speaker in enumerate(speakers):
            mapping[speaker.lower()] = i % 100
        
        mapping["default"] = 0
        return mapping
    
    def load_model(self):
        """Load the trained TTS model"""
        try:
            if not self.model_path or not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Will use fallback TTS methods")
                return
            
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Get vocab size from the checkpoint or use default
            vocab_size = checkpoint.get('vocab_size', 50257)
            
            # Initialize model
            self.model = TTSModel(vocab_size=vocab_size, mel_dim=80, hidden_dim=256)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            self.model_loaded = True
            logger.info("TTS model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading TTS model: {e}")
            logger.info("Will use fallback TTS methods")
            self.model_loaded = False
    
    def text_to_speech(self, text: str, speaker: str = "default", output_path: str = None) -> str:
        """Convert text to speech and return audio file path"""
        
        # Generate output path if not provided
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")
        
        logger.info(f"Converting text to speech: '{text[:50]}...'")
        
        # Try neural TTS if model is loaded
        if self.model_loaded and self.model and self.tokenizer:
            try:
                if self._neural_tts(text, speaker, output_path):
                    return output_path
            except Exception as e:
                logger.warning(f"Neural TTS failed: {e}")
        
        # Use fallback TTS
        logger.info("Using fallback TTS methods")
        if self.fallback_tts.generate_speech_audio(text, output_path):
            return output_path
        
        # Last resort: generate silence with warning
        logger.error("All TTS methods failed, generating silence")
        try:
            silence = torch.zeros(1, 22050)  # 1 second of silence
            torchaudio.save(output_path, silence, 22050)
            return output_path
        except:
            return None
    
    def _neural_tts(self, text: str, speaker: str, output_path: str) -> bool:
        """Try neural TTS conversion"""
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            
            # Tokenize text
            tokens = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            )
            
            text_tokens = tokens['input_ids'].to(self.device)
            
            # Get speaker ID
            speaker_id = torch.tensor([self.speaker_mapping.get(speaker.lower(), 0)], device=self.device)
            
            # Generate mel spectrogram
            with torch.no_grad():
                outputs = self.model(text_tokens, speaker_id=speaker_id)
                mel_output = outputs['mel_output']
            
            # Convert mel to audio
            audio = self.mel_to_audio.convert(mel_output.squeeze(0))
            
            # Ensure audio is in the right format
            if audio.dim() == 1:
                audio = audio.unsqueeze(0)  # Add channel dimension
            
            # Normalize audio to prevent clipping
            max_val = torch.max(torch.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.8  # Scale to 80% of max to prevent clipping
            
            # Save using torchaudio
            torchaudio.save(output_path, audio.cpu(), 22050)
            
            # Verify file was created with content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"Neural TTS audio saved to: {output_path}")
                return True
            else:
                logger.warning("Neural TTS generated empty or invalid file")
                return False
                
        except Exception as e:
            logger.error(f"Error in neural TTS conversion: {e}")
            return False
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better TTS output"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit text length
        words = text.split()
        if len(words) > 50:
            text = ' '.join(words[:50]) + "..."
        
        # Ensure text is not empty
        if not text.strip():
            text = "Hello, this is a test message."
        
        return text
    
    def get_available_speakers(self) -> list:
        """Get list of available speakers"""
        return list(self.speaker_mapping.keys())

class TTSWorker(QObject):
    """Qt Worker for TTS processing with better error handling"""
    
    audio_ready = pyqtSignal(str)  # Signal emitted when audio is ready
    error_occurred = pyqtSignal(str)  # Signal emitted when error occurs
    progress_update = pyqtSignal(str)  # Signal for progress updates
    
    def __init__(self, tts_engine: TTSEngine, text: str, speaker: str = "default"):
        super().__init__()
        self.tts_engine = tts_engine
        self.text = text
        self.speaker = speaker
    
    def run(self):
        """Run TTS conversion in a separate thread"""
        try:
            self.progress_update.emit("Starting TTS conversion...")
            logger.info(f"Starting TTS conversion for text: {self.text[:50]}...")
            
            # Convert text to speech
            audio_path = self.tts_engine.text_to_speech(self.text, self.speaker)
            
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                if file_size > 1000:  # Check if file has content
                    self.progress_update.emit("TTS conversion completed")
                    self.audio_ready.emit(audio_path)
                    logger.info("TTS conversion completed successfully")
                else:
                    error_msg = f"Generated audio file is too small ({file_size} bytes)"
                    logger.warning(error_msg)
                    self.error_occurred.emit(error_msg)
            else:
                error_msg = "Failed to generate audio file"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                
        except Exception as e:
            error_msg = f"TTS conversion error: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)