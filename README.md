CutieChatter 💬
A modern web-based chatbot application with multiple AI personalities, built with Flask and PostgreSQL. Chat with different AI characters, each with unique personalities and conversation styles.

✨ Features
🤖 Multiple AI chatbot personalities
👤 User authentication and registration
💾 Chat history persistence
🎨 Modern, responsive web interface
☁️ Cloud database support (Supabase)
🔒 Secure session management
🛠️ Tech Stack
Backend: Python Flask
Database: PostgreSQL (Supabase)
Frontend: HTML, CSS, JavaScript
Authentication: Custom session-based auth
AI: OpenAI GPT integration
📋 Prerequisites
Before running this application, make sure you have:

Python 3.7 or higher
A Supabase account and project
OpenAI API key (optional, for AI features)
🚀 Installation & Setup
1. Clone the Repository
git clone <repository-url>
cd cutie-chatter-main_chatbots
2. Install Dependencies
pip install -r requirements.txt
3. Set Up Environment Variables
Create a .env file in the root directory:

# Copy the example file
cp .env.example .env
Edit the .env file with your actual credentials:

# Supabase Database Configuration
DB_HOST=your-supabase-host.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.your-project-ref
DB_PASSWORD=your-actual-password
DB_SSLMODE=require

# Optional: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key
Important: Get your Supabase credentials from:

Go to https://supabase.com
Select your project
Go to Settings → Database
Use the Connection Pooling details (port 6543)
4. Set Up Database
Run the Supabase setup script:

python setup_supabase.py
This will:

Test your Supabase connection
Create necessary database tables
Migrate any existing local data (if available)
5. Generate Sample Data (Optional)
To populate the database with sample users and chats:

python generate_dummy_data.py
This creates:

Sample user accounts
Demo chat conversations
Test data for development
🏃‍♂️ Running the Application
Start the Flask Server
python app.py
The application will be available at: http://localhost:5000

Default Test Accounts
If you generated dummy data, you can use these test accounts:

Username: alice | Password: password123
Username: bob | Password: password123
Username: charlie | Password: password123
📁 Project Structure
cutie-chatter-main_chatbots/
├── app.py                 # Main Flask application
├── auth.py               # Authentication logic
├── auth_postgresql.py    # PostgreSQL auth implementation
├── database_config.py    # Database configuration
├── setup_supabase.py     # Database setup script
├── generate_dummy_data.py # Sample data generator
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .env.example         # Environment template
├── static/              # CSS, JS, images
├── templates/           # HTML templates
└── README.md           # This file
🔧 Configuration
Database Configuration
The app supports both local PostgreSQL and Supabase:

Supabase (Recommended): Cloud PostgreSQL with automatic scaling
Local PostgreSQL: For development (optional)
Environment Variables
Variable	Description	Required
DB_HOST	Database host	✅
DB_PORT	Database port (6543 for Supabase pooling)	✅
DB_NAME	Database name	✅
DB_USER	Database username	✅
DB_PASSWORD	Database password	✅
DB_SSLMODE	SSL mode (require for Supabase)	✅
OPENAI_API_KEY	OpenAI API key for AI features	❌
🐛 Troubleshooting
Common Issues
"Wrong password" error

Double-check your Supabase password
Make sure you're using Connection Pooling credentials (port 6543)
"Module not found" error

pip install -r requirements.txt
Database connection issues

Verify your .env file has correct credentials
Test connection: python setup_supabase.py
Port already in use

Change the port in app.py: app.run(port=5001)
Database Reset
To reset your database:

# This will clear all data and recreate tables
python setup_supabase.py
python generate_dummy_data.py
🔄 Migration from SQLite
If you're migrating from a previous SQLite version:

The migration script will automatically detect local PostgreSQL data
Run python setup_supabase.py and choose 'y' to migrate
Your existing data will be transferred to Supabase
🚀 Deployment
Local Development
python app.py
Production Deployment
For production deployment, consider:

Environment Variables: Set production values
WSGI Server: Use Gunicorn or uWSGI
Reverse Proxy: Nginx or Apache
SSL Certificate: Enable HTTPS
Database: Ensure Supabase is properly configured
Example with Gunicorn:

pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
📝 API Endpoints
Endpoint	Method	Description
/	GET	Home page
/register	GET/POST	User registration
/login	GET/POST	User login
/logout	POST	User logout
/chat	GET	Chat interface
/api/chat	POST	Send chat message
🤝 Contributing
Fork the repository
Create a feature branch
Make your changes
Test thoroughly
Submit a pull request
📄 License
This project is licensed under the MIT License.

🆘 Support
If you encounter any issues:

Check the troubleshooting section above
Verify your environment configuration
Check the console/terminal for error messages
Ensure all dependencies are installed
🎯 Next Steps
After successful setup:

Customize Chatbots: Modify chatbot personalities in the code
Add Features: Extend functionality as needed
Styling: Customize the UI/UX
Deploy: Move to production environment
Happy Chatting! 💬✨
