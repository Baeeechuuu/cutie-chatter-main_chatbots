Cutie Chatter Chatbot
A comprehensive chatbot application with multiple backend integrations, text-to-speech capabilities, and web interface.
🚀 Features

Multi-Backend Support: PostgreSQL and Supabase integration
Text-to-Speech (TTS): Audio output capabilities
Sentiment Analysis: Built-in sentiment processing
OCR Integration: Optical Character Recognition
Web Interface: HTML-based user interface
Model Checkpoints: Support for various AI models
Authentication System: Secure user authentication
Database Migration: Automated database setup and migration

📁 Project Structure
CUTIE-CHATTER-MAIN_CHATBOTS/
├── __pycache__/              # Python cache files
├── analysis/                 # Data analysis modules
├── background/               # Background processing
├── build/                    # Built application files
├── dist/                     # Distribution files
├── icons/                    # Application icons
├── model_checkpoints/        # AI model checkpoints
├── ocr/                      # OCR processing modules
├── pre-prod/                 # Pre-production files
├── sentiment/                # Sentiment analysis
├── stt/                      # Speech-to-Text modules
├── temp_audio/               # Temporary audio files
├── themes/                   # UI themes
├── training_logs/            # Model training logs
├── tts/                      # Text-to-Speech modules
├── web_ui/                   # Web interface files
├── auth_bridge.py            # Authentication bridge
├── auth_postgresql.py        # PostgreSQL authentication
├── auth.html                 # Authentication page
├── auth.py                   # Main authentication module
├── backend2.py               # Secondary backend
├── backends.py               # Backend configurations
├── chat_bridge.py            # Chat bridge module
├── cutie.py                  # Main application entry point
├── CutieChatbot.spec         # PyInstaller specification
├── cutiechatter_users.db     # User database
├── database_config.py        # Database configuration
├── dataset_patch.py          # Dataset patching utilities
├── demo_output.wav           # Demo audio file
├── demo_tts.py               # TTS demonstration
├── generate_dummy_data.py    # Test data generation
├── migration_guide.md        # Database migration guide
├── readme.md                 # This file
├── requirements.txt          # Python dependencies
├── run.py                    # Application runner
├── setup_supabase.py         # Supabase setup
├── SUPABASE_MIGRATION_GUIDE.md # Supabase migration guide
├── tempCodeRunnerFile.py     # Temporary code files
├── test_postgresql_setup.py  # PostgreSQL testing
├── test_supabase_connection.py # Supabase testing
├── tts_training.log          # TTS training logs
├── ui_chatbot.html           # Main chat interface
└── windows_patch.py          # Windows compatibility patch
🛠️ Installation
Prerequisites

Python 3.8+
PostgreSQL (optional)
Supabase account (optional)

Setup

Clone the repository
bashgit clone <repository-url>
cd CUTIE-CHATTER-MAIN_CHATBOTS

Install dependencies
bashpip install -r requirements.txt

Environment Configuration
bashcp .env.example .env
# Edit .env with your configurations

Database Setup
For PostgreSQL:
bashpython test_postgresql_setup.py
For Supabase:
bashpython setup_supabase.py
python test_supabase_connection.py

Run the application
bashpython run.py


🔧 Configuration
Environment Variables
Create a .env file in the root directory:
env# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cutiechatter
DB_USER=your_username
DB_PASSWORD=your_password

# Supabase Configuration (if using Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Authentication
SECRET_KEY=your_secret_key
Database Configuration
The application supports multiple database backends:

SQLite: Default local database
PostgreSQL: For production deployments
Supabase: Cloud-based PostgreSQL

Refer to migration_guide.md and SUPABASE_MIGRATION_GUIDE.md for detailed setup instructions.
🚀 Usage
Web Interface

Open your browser and navigate to the application URL
Use auth.html for user authentication
Access the main chat interface via ui_chatbot.html

Core Modules

Main Application: cutie.py - Primary chatbot logic
Authentication: auth.py - User management and authentication
Chat Bridge: chat_bridge.py - Communication bridge between components
TTS Demo: demo_tts.py - Text-to-speech demonstration

🧪 Testing
Run the test suites to ensure everything is working:
bash# Test PostgreSQL setup
python test_postgresql_setup.py

# Test Supabase connection
python test_supabase_connection.py

# Generate test data
python generate_dummy_data.py
📊 Features Overview
Text-to-Speech (TTS)

Custom TTS engine with training capabilities
Audio output stored in temp_audio/
Training logs available in tts_training.log

Sentiment Analysis

Built-in sentiment processing
Configurable sentiment models

OCR Integration

Optical Character Recognition capabilities
Image-to-text processing

Multi-Backend Support

Flexible database backend switching
Support for local and cloud databases

🔄 Database Migration
For migrating between different database backends:

PostgreSQL Migration: See migration_guide.md
Supabase Migration: See SUPABASE_MIGRATION_GUIDE.md

📦 Building and Distribution
Creating Executable
bash# Build with PyInstaller
pyinstaller CutieChatbot.spec
The built application will be available in the dist/ directory.
🎨 Theming
The application supports custom themes located in the themes/ directory. Modify the theme files to customize the appearance.
📝 Logging

Training Logs: training_logs/ directory
TTS Training: tts_training.log
Application logs are generated during runtime

🤝 Contributing

Fork the repository
Create a feature branch
Make your changes
Test thoroughly
Submit a pull request

📄 License
See LICENSE file for details.
🆘 Support
For issues and support:

Check the migration guides for database-related issues
Review the test files for configuration examples
Ensure all dependencies are properly installed


Note: This chatbot application is designed to be modular and extensible. Each component can be used independently or as part of the complete system.
