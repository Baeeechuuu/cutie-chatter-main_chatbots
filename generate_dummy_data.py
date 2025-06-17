# generate_dummy_data.py - Script to generate dummy data for CutieChatter PostgreSQL database
import json
import random
from datetime import datetime, timedelta
from database_config import db_config
from auth_postgresql import AuthManager

class DummyDataGenerator:
    """Generate dummy data for testing and demonstration"""
    
    def __init__(self):
        self.auth_manager = AuthManager()
        self.dummy_messages = [
            "Hello! How are you today?",
            "What's your favorite color?",
            "Can you help me with something?",
            "Tell me a joke!",
            "What's the weather like?",
            "I'm feeling great today!",
            "Do you have any recommendations for books?",
            "What time is it?",
            "Can you explain how AI works?",
            "I love chatting with you!",
            "What's your favorite food?",
            "How can I improve my coding skills?",
            "Tell me something interesting!",
            "What are your hobbies?",
            "Can you help me plan my day?",
            "I'm working on a new project",
            "What's the meaning of life?",
            "How do you handle stress?",
            "What's your opinion on technology?",
            "Can you recommend a good movie?",
            "I'm learning something new today",
            "What motivates you?",
            "How do you stay productive?",
            "What's your favorite quote?",
            "Tell me about your experiences"
        ]
        
        self.bot_responses = [
            "That's wonderful! I'm here to help.",
            "I think blue is quite lovely!",
            "Of course! What do you need help with?",
            "Why did the AI cross the road? To get to the other side of the algorithm!",
            "I don't have access to weather data, but I hope it's nice where you are!",
            "That's fantastic! A positive attitude makes everything better.",
            "I'd recommend 'The Hitchhiker's Guide to the Galaxy' - it's both funny and thought-provoking!",
            "I don't have access to real-time data, but you can check your system clock!",
            "AI works by processing patterns in data to make predictions and decisions.",
            "I enjoy our conversations too! Thanks for being so friendly.",
            "I don't eat, but pizza seems to be universally loved!",
            "Practice regularly, work on projects, and don't be afraid to make mistakes!",
            "Did you know that honey never spoils? Archaeologists have found edible honey from ancient times!",
            "I enjoy learning about different topics and helping people solve problems.",
            "Let's start by listing your priorities for today. What's most important?",
            "That sounds exciting! What kind of project are you working on?",
            "That's a deep question! I think it's about finding purpose and making meaningful connections.",
            "Taking breaks, staying organized, and maintaining perspective usually help.",
            "Technology can be incredibly powerful when used thoughtfully and ethically.",
            "I'd suggest checking out some classic films or recent releases based on your preferences!",
            "Learning is one of life's greatest pleasures! What are you studying?",
            "Curiosity and the desire to help others motivate me greatly.",
            "Setting clear goals and taking regular breaks can boost productivity significantly.",
            "One of my favorites is: 'The only way to do great work is to love what you do.'",
            "Every interaction teaches me something new about human creativity and kindness!"
        ]
        
        self.usernames = [
            "alice_wonder", "bob_builder", "charlie_dev", "diana_design", "eve_expert",
            "frank_coder", "grace_gamer", "henry_hacker", "ivy_innovate", "jack_joker",
            "kate_creative", "liam_learner", "mia_maker", "noah_navigator", "olivia_optimizer",
            "peter_programmer", "quinn_questioner", "rachel_researcher", "sam_solver", "tina_tester"
        ]
        
        self.domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "example.com"]
    
    def clear_database(self):
        """Clear all data from the database tables"""
        print("🧹 Clearing database...")
        
        try:
            with db_config.get_cursor() as (cursor, conn):
                # Delete in order to respect foreign key constraints
                cursor.execute("DELETE FROM sessions")
                cursor.execute("DELETE FROM user_chats") 
                cursor.execute("DELETE FROM users")
                
                # Reset auto-increment sequences
                cursor.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1")
                cursor.execute("ALTER SEQUENCE sessions_id_seq RESTART WITH 1")
                cursor.execute("ALTER SEQUENCE user_chats_id_seq RESTART WITH 1")
                
                conn.commit()
                print("  ✅ Database cleared successfully")
                
        except Exception as e:
            print(f"  ❌ Error clearing database: {e}")
            raise
    
    def generate_users(self, count=10):
        """Generate dummy users"""
        print(f"🔧 Generating {count} dummy users...")
        
        created_users = []
        
        for i in range(count):
            username = f"{random.choice(self.usernames)}{random.randint(1, 999)}"
            email = f"{username}@{random.choice(self.domains)}"
            password = "password123"  # Same password for all demo users
            
            result = self.auth_manager.register_user(username, email, password, password)
            
            if result["success"]:
                created_users.append({
                    "user_id": result["user_id"],
                    "username": username,
                    "email": email,
                    "password": password
                })
                print(f"  ✅ Created user: {username} ({email})")
            else:
                print(f"  ❌ Failed to create user {username}: {result['message']}")
        
        return created_users
    
    def generate_chat_data(self, user_id, num_chats=3):
        """Generate dummy chat data for a user"""
        chats = []
        
        for chat_num in range(num_chats):
            chat_id = f"chat_{user_id}_{chat_num}_{random.randint(1000, 9999)}"
            
            # Generate random number of messages (5-15 per chat)
            num_messages = random.randint(5, 15)
            messages = []
            
            chat_start_time = datetime.now() - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            for msg_num in range(num_messages):
                # Alternate between user and bot messages
                is_user_message = msg_num % 2 == 0
                
                message_time = chat_start_time + timedelta(minutes=msg_num * random.randint(1, 5))
                
                if is_user_message:
                    message = {
                        "id": f"msg_{chat_id}_{msg_num}",
                        "type": "user",
                        "content": random.choice(self.dummy_messages),
                        "timestamp": message_time.isoformat(),
                        "metadata": {
                            "platform": "web",
                            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    }
                else:
                    message = {
                        "id": f"msg_{chat_id}_{msg_num}",
                        "type": "assistant", 
                        "content": random.choice(self.bot_responses),
                        "timestamp": (message_time + timedelta(seconds=random.randint(1, 30))).isoformat(),
                        "metadata": {
                            "model": "cutie-chat-v1",
                            "processing_time": round(random.uniform(0.5, 2.0), 2),
                            "confidence": round(random.uniform(0.8, 0.99), 3)
                        }
                    }
                
                messages.append(message)
            
            chat = {
                "id": chat_id,
                "title": f"Chat {chat_num + 1}",
                "created_at": chat_start_time.isoformat(),
                "updated_at": (chat_start_time + timedelta(minutes=len(messages) * 3)).isoformat(),
                "messages": messages,
                "settings": {
                    "model": "cutie-chat-v1",
                    "temperature": round(random.uniform(0.7, 1.0), 2),
                    "max_tokens": random.choice([150, 200, 300]),
                    "theme": random.choice(["dark", "light", "auto"])
                },
                "metadata": {
                    "total_messages": len(messages),
                    "last_activity": messages[-1]["timestamp"] if messages else chat_start_time.isoformat()
                }
            }
            
            chats.append(chat)
        
        return chats
    
    def populate_chat_data(self, users, chats_per_user=3):
        """Populate chat data for users"""
        print(f"💬 Generating chat data ({chats_per_user} chats per user)...")
        
        for user in users:
            chat_data = self.generate_chat_data(user["user_id"], chats_per_user)
            
            result = self.auth_manager.save_user_chat_data(user["user_id"], chat_data)
            
            if result["success"]:
                total_messages = sum(len(chat["messages"]) for chat in chat_data)
                print(f"  ✅ Generated {len(chat_data)} chats with {total_messages} messages for {user['username']}")
            else:
                print(f"  ❌ Failed to save chat data for {user['username']}: {result['message']}")
    
    def generate_sessions(self, users, sessions_per_user=2):
        """Generate active sessions for some users"""
        print(f"🔗 Generating sessions ({sessions_per_user} per user)...")
        
        active_sessions = []
        
        for user in users[:len(users)//2]:  # Only half the users have active sessions
            for session_num in range(random.randint(1, sessions_per_user)):
                login_result = self.auth_manager.login_user(user["username"], user["password"])
                
                if login_result["success"]:
                    active_sessions.append({
                        "user": user,
                        "session_token": login_result["session_token"]
                    })
                    print(f"  ✅ Created session for {user['username']}")
        
        return active_sessions
    
    def display_database_stats(self):
        """Display database statistics"""
        print("\n📊 Database Statistics:")
        
        try:
            with db_config.get_cursor() as (cursor, conn):
                # Count users
                cursor.execute("SELECT COUNT(*) as count FROM users")
                user_count = cursor.fetchone()['count']
                print(f"  👥 Total Users: {user_count}")
                
                # Count active sessions
                cursor.execute("SELECT COUNT(*) as count FROM sessions WHERE is_active = TRUE")
                session_count = cursor.fetchone()['count']
                print(f"  🔗 Active Sessions: {session_count}")
                
                # Count chats
                cursor.execute("SELECT COUNT(*) as count FROM user_chats")
                chat_count = cursor.fetchone()['count']
                print(f"  💬 Total Chat Records: {chat_count}")
                
                # Recent registrations
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                recent_users = cursor.fetchone()['count']
                print(f"  🆕 New Users (24h): {recent_users}")
                
                # Sample users
                cursor.execute("SELECT username, email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
                sample_users = cursor.fetchall()
                print(f"\n  📋 Recent Users:")
                for user in sample_users:
                    print(f"    • {user['username']} ({user['email']}) - {user['created_at']}")
                
        except Exception as e:
            print(f"  ❌ Error getting database stats: {e}")
    
    def run_full_generation(self, num_users=10, chats_per_user=3, sessions_per_user=2):
        """Run complete dummy data generation"""
        print("🚀 Starting Dummy Data Generation for CutieChatter PostgreSQL Database")
        print("=" * 70)
        
        # Clear existing data first
        self.clear_database()
        
        # Generate users
        users = self.generate_users(num_users)
        
        if not users:
            print("❌ No users were created. Stopping data generation.")
            return
        
        # Generate chat data
        self.populate_chat_data(users, chats_per_user)
        
        # Generate sessions
        active_sessions = self.generate_sessions(users, sessions_per_user)
        
        # Display results
        print("\n✅ Dummy Data Generation Complete!")
        print("=" * 70)
        self.display_database_stats()
        
        print(f"\n🔑 Demo Login Credentials:")
        print(f"  Password for all users: password123")
        print(f"  Sample usernames: {', '.join([u['username'] for u in users[:5]])}")
        
        if active_sessions:
            print(f"\n🔗 Active Sessions Created: {len(active_sessions)}")
            print("  These users are currently 'logged in'")
        
        print("\n🎯 You can now test the application with this dummy data!")

def main():
    """Main function to run dummy data generation"""
    try:
        generator = DummyDataGenerator()
        generator.run_full_generation(
            num_users=15,       # Number of dummy users to create
            chats_per_user=4,   # Number of chat sessions per user
            sessions_per_user=2 # Number of active sessions per user
        )
        
    except Exception as e:
        print(f"❌ Error running dummy data generation: {e}")
        print("Make sure PostgreSQL is running and database configuration is correct.")

if __name__ == "__main__":
    main() 