"""
Quick script to add a few real Jeopardy questions to the database.
"""

import logging
from scraper.jeopardy_scraper import JeopardyScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_quick_questions():
    """Add just a few real questions quickly."""
    scraper = JeopardyScraper(delay_seconds=1.0)
    
    try:
        # Get the most recent season
        seasons = scraper.get_season_list()
        recent_season = sorted(seasons, key=lambda x: x['season'], reverse=True)[0]
        
        # Get games from that season
        games = scraper.get_games_from_season(recent_season['url'])
        
        # Process just 2 games quickly
        total_questions = 0
        for game in games[:2]:
            logger.info(f"Processing game {game['game_id']}")
            questions = scraper.scrape_game_questions(game['url'], game['game_id'])
            
            if questions:
                saved = scraper.save_questions_to_database(questions)
                total_questions += saved
                logger.info(f"Added {saved} questions")
        
        return total_questions
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 0

if __name__ == "__main__":
    added = add_quick_questions()
    print(f"Added {added} real Jeopardy questions!")