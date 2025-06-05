#!/usr/bin/env python3
"""
Script to update air_dates for existing Jeopardy questions.
This script will try to extract air dates from show numbers and update the database.
"""

import logging
from database.models import get_session, JeopardyQuestion
from scraper.jeopardy_scraper import JeopardyScraper
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)

logger = logging.getLogger(__name__)

def update_air_dates_from_show_numbers():
    """
    Update air_dates for questions that have show_numbers but missing air_dates.
    """
    session = get_session()
    scraper = JeopardyScraper(delay_seconds=1.0)
    
    try:
        # Get questions with show_number but no air_date
        questions_to_update = session.query(JeopardyQuestion).filter(
            JeopardyQuestion.show_number.isnot(None),
            (JeopardyQuestion.air_date.is_(None) | (JeopardyQuestion.air_date == ''))
        ).limit(50).all()  # Start with a small batch
        
        logger.info(f"Found {len(questions_to_update)} questions to update")
        
        updated_count = 0
        show_numbers_processed = set()
        
        for question in questions_to_update:
            if question.show_number in show_numbers_processed:
                continue
                
            show_numbers_processed.add(question.show_number)
            
            # Construct J-Archive URL for the show
            game_url = f"http://j-archive.com/showgame.php?game_id={question.show_number}"
            
            try:
                # Scrape the game page to get air_date
                game_questions = scraper.scrape_game_questions(game_url, question.show_number)
                
                if game_questions and game_questions[0].get('air_date'):
                    air_date = game_questions[0]['air_date']
                    
                    # Update all questions from this show
                    questions_from_show = session.query(JeopardyQuestion).filter_by(
                        show_number=question.show_number
                    ).all()
                    
                    for q in questions_from_show:
                        q.air_date = air_date
                        updated_count += 1
                    
                    session.commit()
                    logger.info(f"Updated {len(questions_from_show)} questions from show {question.show_number} with air_date: {air_date}")
                    
            except Exception as e:
                logger.warning(f"Error updating show {question.show_number}: {e}")
                session.rollback()
                continue
        
        logger.info(f"Successfully updated {updated_count} questions with air dates")
        
    except Exception as e:
        logger.error(f"Error in update_air_dates_from_show_numbers: {e}")
        session.rollback()
    finally:
        session.close()

def test_air_date_extraction():
    """
    Test air date extraction on a few sample games.
    """
    scraper = JeopardyScraper(delay_seconds=1.0)
    
    # Test with a few recent game IDs
    test_games = [9221, 9220, 9219]  # Recent game IDs
    
    for game_id in test_games:
        game_url = f"http://j-archive.com/showgame.php?game_id={game_id}"
        logger.info(f"Testing air date extraction for game {game_id}")
        
        try:
            questions = scraper.scrape_game_questions(game_url, game_id)
            if questions:
                air_date = questions[0].get('air_date')
                logger.info(f"Game {game_id}: Found air_date = {air_date}")
            else:
                logger.warning(f"Game {game_id}: No questions found")
        except Exception as e:
            logger.error(f"Game {game_id}: Error - {e}")

if __name__ == "__main__":
    logger.info("Starting air date update process...")
    
    # First test the extraction
    logger.info("Testing air date extraction...")
    test_air_date_extraction()
    
    # Then update existing records
    logger.info("Updating existing records...")
    update_air_dates_from_show_numbers()
    
    logger.info("Air date update process completed")