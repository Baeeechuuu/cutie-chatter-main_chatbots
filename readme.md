# CutieChatter - AI Chat Application with TTS

A beautiful PyQt6-based chat application featuring AI conversation, document processing, sentiment analysis, and **Text-to-Speech functionality** using Genshin Impact character voices.

## Features

### 🤖 AI Chat
- **DeepSeek Integration**: Powered by DeepSeek R1 models (1.5B to 627B parameters)
- **Streaming Responses**: Real-time message streaming
- **Conversation Memory**: Maintains chat history
- **Beautiful UI**: Modern, gradient-themed interface

### 🔊 Text-to-Speech (NEW!)
- **Genshin Impact Voices**: Train TTS models using Genshin character voices
- **Multi-Speaker Support**: Choose from 60+ Genshin Impact characters
- **Real-time Audio**: Convert AI responses to speech instantly
- **Custom Training**: Train your own TTS models with the provided scripts

### 📄 Document Processing
- **OCR Support**: Extract text from PDF documents
- **Document Chat**: Ask questions about uploaded documents
- **Multilingual Support**: Process documents in multiple languages

### 💭 Sentiment Analysis
- **Emotion Classification**: Analyze emotional content in conversations
- **Attachment Theory**: Track emotional connections over time
- **Text Similarity**: Measure conversation coherence

### 🎙️ Speech Recognition
- **Whisper Integration**: Convert speech to text
- **Real-time Processing**: Voice input support

## Installation

### Prerequisites
- Python 3.8+
- PyQt6
- CUDA (recommended for TTS training)

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd cutie-chatter-main

# Install dependencies
pip install -r requirements.txt

# For TTS functionality
cd model-train
pip install -r requirements.txt

# Login to Hugging Face (for TTS dataset access)
huggingface-cli login
```

## Usage

### Starting the Application
```bash
python run.py
```

### Training TTS Models
```bash
cd model-train
python train_tts.py
```

### TTS Features
1. **Train Your Model**: Use the Genshin voice dataset to train character-specific voices
2. **Play AI Responses**: Click the 🔊 Play button on any AI message
3. **Choose Speakers**: Select from 60+ Genshin Impact characters
4. **Real-time Audio**: Instant text-to-speech conversion

## TTS Model Training

The application includes a complete TTS training pipeline:

### Dataset
- **Source**: `nc33/genshin_voice_v13` from Hugging Face
- **Size**: 200 high-quality voice samples
- **Characters**: Multiple Genshin Impact characters
- **Languages**: English and Japanese

### Training Process
1. **Setup**: Login to Hugging Face and install dependencies
2. **Train**: Run the training script (2-4 hours on GPU)
3. **Deploy**: Model automatically integrates with the chat app
4. **Enjoy**: AI responses with Genshin character voices!

## Architecture

### Core Components
- **Chat Interface**: PyQt6-based modern UI
- **AI Backend**: Ollama integration with DeepSeek models
- **TTS Engine**: Custom Tacotron-like architecture
- **Audio Processing**: Griffin-Lim vocoder for speech synthesis
- **Sentiment Analysis**: Custom emotion classification models

### TTS Architecture
- **Text Encoder**: LSTM-based text processing
- **Attention**: Multi-head attention for alignment
- **Decoder**: Mel spectrogram generation
- **Vocoder**: Griffin-Lim audio synthesis
- **Speaker Embedding**: Multi-speaker support

## Configuration

### Supported Models
- deepseek-r1:1.5b (lightweight)
- deepseek-r1:7b (balanced)
- deepseek-r1:8b (recommended)
- deepseek-r1:14b (high quality)
- deepseek-r1:32b (maximum quality)

### TTS Settings
- Sample Rate: 22,050 Hz
- Mel Spectrograms: 80 bins
- Max Audio Length: 10 seconds
- Supported Characters: 60+ Genshin Impact voices

## File Structure
```
cutie-chatter-main/
├── run.py              # Main application entry
├── cutie.py            # Main window implementation
├── backends.py         # AI and TTS workers
├── tts/                # TTS engine and inference
│   ├── __init__.py
│   └── tts_engine.py   # TTS model and audio processing
├── model-train/        # TTS training pipeline
│   ├── tts_trainer.py  # Training script
│   ├── train_tts.py    # Simple training launcher
│   ├── requirements.txt
│   └── README.md       # Detailed TTS documentation
├── themes/             # UI styling
├── icons/              # UI icons (including audio controls)
├── sentiment/          # Emotion analysis
├── ocr/               # Document processing
└── stt/               # Speech-to-text
```

## License
GNU General Public License v3.0

## Contributing
Feel free to contribute to the project! Areas of interest:
- Improved TTS models (WaveGlow, HiFi-GAN)
- Additional character voices
- Performance optimizations
- UI/UX improvements
