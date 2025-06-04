#!/usr/bin/env python3
"""
Database initialization script for the Jeopardy Discord bot.
This script creates the necessary database tables if they don't exist.
"""

import logging
from database.models import create_tables, get_session, JeopardyQuestion, GameSession
from sqlalchemy.exc import OperationalError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)

logger = logging.getLogger(__name__)

def initialize_database():
    """
    Initialize the database by creating all necessary tables.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Initializing database...")
        
        # Create all tables
        engine = create_tables()
        logger.info("Database tables created successfully")
        
        # Test the connection by trying to query
        db_session = get_session()
        try:
            jeopardy_count = db_session.query(JeopardyQuestion).count()
            game_session_count = db_session.query(GameSession).count()
            
            logger.info(f"Database connection verified")
            logger.info(f"Current data: {jeopardy_count} questions, {game_session_count} active game sessions")
            
        finally:
            db_session.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False

def main():
    """Main function to initialize the database."""
    print("Jeopardy Bot Database Initialization")
    print("=" * 40)
    
    if initialize_database():
        print("✓ Database initialized successfully!")
        return 0
    else:
        print("✗ Database initialization failed!")
        return 1

if __name__ == "__main__":
    exit(main())