"""
Setup script to initialize the Jeopardy database and scrape initial data.
"""

import asyncio
import logging
from database.models import create_tables
from scraper.jeopardy_scraper import run_initial_scrape

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """
    Initialize the database and scrape initial Jeopardy data.
    """
    logger.info("Starting Jeopardy database setup...")
    
    try:
        # Create database tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")
        
        # Run initial scrape
        logger.info("Starting initial data scrape from J-Archive...")
        logger.info("This will be gentle on their servers with delays between requests...")
        
        questions_count = run_initial_scrape()
        
        if questions_count > 0:
            logger.info(f"Setup completed successfully! Scraped {questions_count} questions.")
            logger.info("Your bot is now ready to play Jeopardy!")
        else:
            logger.warning("No questions were scraped. Please check your internet connection.")
            
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise

if __name__ == "__main__":
    main()