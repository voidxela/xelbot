#!/usr/bin/env python3
"""
Setup script for Discord Bot with Jeopardy Game
Automates initial configuration and database setup
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_dependencies():
    """Check if required system dependencies are available."""
    required_commands = ['python', 'pip']
    missing = []
    
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing.append(cmd)
    
    if missing:
        print(f"❌ Missing required commands: {', '.join(missing)}")
        return False
    
    print("✅ System dependencies available")
    return True

def install_python_packages():
    """Install required Python packages."""
    print("📦 Installing Python packages...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade',
            'discord.py', 'python-dotenv', 'psutil', 'sqlalchemy', 
            'psycopg2-binary', 'beautifulsoup4', 'requests', 
            'trafilatura', 'asyncpg'
        ], check=True, capture_output=True)
        print("✅ Python packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    try:
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
        print("⚠️  Remember to edit .env with your actual values:")
        print("   - DISCORD_TOKEN (required)")
        print("   - DATABASE_URL (required)")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_env_vars():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['DISCORD_TOKEN', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or placeholder values for: {', '.join(missing_vars)}")
        print("   Please edit your .env file with actual values")
        return False
    
    print("✅ Environment variables configured")
    return True

def test_database_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    
    try:
        from database.models import get_session
        session = get_session()
        if session:
            session.close()
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Failed to connect to database")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False

def initialize_database():
    """Initialize database tables."""
    print("🗄️  Initializing database tables...")
    
    try:
        from init_database import initialize_database as init_db
        if init_db():
            print("✅ Database tables initialized")
            return True
        else:
            print("❌ Failed to initialize database tables")
            return False
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def create_logs_directory():
    """Create logs directory if it doesn't exist."""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory exists")
    return True

def test_bot_startup():
    """Test that the bot can start without errors."""
    print("🤖 Testing bot startup...")
    
    try:
        # Import main components to check for syntax errors
        from bot import DiscordBot
        from commands.basic import BasicCommands
        from commands.jeopardy import JeopardyGame
        print("✅ Bot modules load successfully")
        return True
    except Exception as e:
        print(f"❌ Bot startup test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Discord Bot Setup Script")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Install packages
    if not install_python_packages():
        sys.exit(1)
    
    # Create configuration files
    if not create_env_file():
        sys.exit(1)
    
    # Check environment variables
    env_configured = check_env_vars()
    
    # Create directories
    create_logs_directory()
    
    # Test bot modules
    if not test_bot_startup():
        sys.exit(1)
    
    # Database setup (only if env vars are configured)
    if env_configured:
        if test_database_connection():
            initialize_database()
        else:
            print("⚠️  Skipping database initialization due to connection issues")
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed!")
    
    if not env_configured:
        print("\n📝 Next steps:")
        print("1. Edit .env file with your Discord token and database URL")
        print("2. Run 'python init_database.py' to set up the database")
        print("3. Run 'python bot.py' to start the bot")
    else:
        print("\n✅ Your bot is ready to run!")
        print("Start it with: python bot.py")
    
    print("\n📚 Documentation: Check README.md for detailed instructions")

if __name__ == "__main__":
    main()