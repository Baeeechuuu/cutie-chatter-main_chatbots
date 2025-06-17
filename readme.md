# CutieChatter 💬

A modern web-based chatbot application with multiple AI personalities, built with Flask and PostgreSQL. Chat with different AI characters, each with unique personalities and conversation styles.

## ✨ Features

- 🤖 Multiple AI chatbot personalities
- 👤 User authentication and registration
- 💾 Chat history persistence
- 🎨 Modern, responsive web interface
- ☁️ Cloud database support (Supabase)
- 🔒 Secure session management

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL (Supabase)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Custom session-based auth
- **AI**: OpenAI GPT integration

## 📋 Prerequisites

Before running this application, make sure you have:

- Python 3.7 or higher
- A Supabase account and project
- OpenAI API key (optional, for AI features)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cutie-chatter-main_chatbots
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file with your actual credentials:

```env
# Supabase Database Configuration
DB_HOST=your-supabase-host.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.your-project-ref
DB_PASSWORD=your-actual-password
DB_SSLMODE=require

# Optional: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key
```

**Important**: Get your Supabase credentials from:
1. Go to [https://supabase.com](https://supabase.com)
2. Select your project
3. Go to **Settings → Database**
4. Use the **Connection Pooling** details (port 6543)

### 4. Set Up Database

Run the Supabase setup script:

```bash
python setup_supabase.py
```

This will:
- Test your Supabase connection
- Create necessary database tables
- Migrate any existing local data (if available)

### 5. Generate Sample Data (Optional)

To populate the database with sample users and chats:

```bash
python generate_dummy_data.py
```

This creates:
- Sample user accounts
- Demo chat conversations
- Test data for development

## 🏃‍♂️ Running the Application

### Start the Flask Server

```bash
python app.py
```

The application will be available at: **http://localhost:5000**

### Default Test Accounts

If you generated dummy data, you can use these test accounts:

- **Username**: `alice` | **Password**: `password123`
- **Username**: `bob` | **Password**: `password123`
- **Username**: `charlie` | **Password**: `password123`

## 📁 Project Structure

```
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
```

## 🔧 Configuration

### Database Configuration

The app supports both local PostgreSQL and Supabase:

- **Supabase (Recommended)**: Cloud PostgreSQL with automatic scaling
- **Local PostgreSQL**: For development (optional)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_HOST` | Database host | ✅ |
| `DB_PORT` | Database port (6543 for Supabase pooling) | ✅ |
| `DB_NAME` | Database name | ✅ |
| `DB_USER` | Database username | ✅ |
| `DB_PASSWORD` | Database password | ✅ |
| `DB_SSLMODE` | SSL mode (require for Supabase) | ✅ |
| `OPENAI_API_KEY` | OpenAI API key for AI features | ❌ |

## 🐛 Troubleshooting

### Common Issues

1. **"Wrong password" error**
   - Double-check your Supabase password
   - Make sure you're using Connection Pooling credentials (port 6543)

2. **"Module not found" error**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database connection issues**
   - Verify your `.env` file has correct credentials
   - Test connection: `python setup_supabase.py`

4. **Port already in use**
   - Change the port in `app.py`: `app.run(port=5001)`

### Database Reset

To reset your database:

```bash
# This will clear all data and recreate tables
python setup_supabase.py
python generate_dummy_data.py
```

## 🔄 Migration from SQLite

If you're migrating from a previous SQLite version:

1. The migration script will automatically detect local PostgreSQL data
2. Run `python setup_supabase.py` and choose 'y' to migrate
3. Your existing data will be transferred to Supabase

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment

For production deployment, consider:

1. **Environment Variables**: Set production values
2. **WSGI Server**: Use Gunicorn or uWSGI
3. **Reverse Proxy**: Nginx or Apache
4. **SSL Certificate**: Enable HTTPS
5. **Database**: Ensure Supabase is properly configured

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/register` | GET/POST | User registration |
| `/login` | GET/POST | User login |
| `/logout` | POST | User logout |
| `/chat` | GET | Chat interface |
| `/api/chat` | POST | Send chat message |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Verify your environment configuration
3. Check the console/terminal for error messages
4. Ensure all dependencies are installed

## 🎯 Next Steps

After successful setup:

1. **Customize Chatbots**: Modify chatbot personalities in the code
2. **Add Features**: Extend functionality as needed
3. **Styling**: Customize the UI/UX
4. **Deploy**: Move to production environment

---

**Happy Chatting! 💬✨**
