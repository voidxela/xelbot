"""
Production script to populate the database with real Jeopardy questions.
"""

import logging
from scraper.jeopardy_scraper import JeopardyScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)

logger = logging.getLogger(__name__)

def populate_with_real_questions(max_games: int = 10):
    """
    Populate database with real Jeopardy questions from multiple games.
    
    Args:
        max_games: Maximum number of games to scrape (default 10 for production use)
    """
    scraper = JeopardyScraper(delay_seconds=2.0)  # Be respectful to the server
    
    try:
        logger.info(f"Starting to populate database with up to {max_games} games of real Jeopardy questions...")
        
        # Get recent seasons
        seasons = scraper.get_season_list()
        if not seasons:
            logger.error("Could not retrieve season list")
            return 0
        
        # Use the most recent season
        recent_season = sorted(seasons, key=lambda x: x['season'], reverse=True)[0]
        logger.info(f"Using season {recent_season['season']}")
        
        # Get games from that season
        games = scraper.get_games_from_season(recent_season['url'])
        if not games:
            logger.error("No games found in recent season")
            return 0
        
        total_questions = 0
        games_processed = 0
        
        # Process the specified number of games
        for game in games[:max_games]:
            logger.info(f"Processing game {game['game_id']} ({games_processed + 1}/{max_games})")
            
            questions = scraper.scrape_game_questions(game['url'], game['game_id'])
            
            if questions:
                saved = scraper.save_questions_to_database(questions)
                total_questions += saved
                logger.info(f"Saved {saved} questions from game {game['game_id']}")
            else:
                logger.warning(f"No questions found in game {game['game_id']}")
            
            games_processed += 1
        
        logger.info(f"Completed! Processed {games_processed} games and added {total_questions} questions to the database.")
        return total_questions
        
    except Exception as e:
        logger.error(f"Error during database population: {e}")
        return 0

if __name__ == "__main__":
    # Start with a moderate number of games to be respectful to the server
    questions_added = populate_with_real_questions(max_games=8)
    
    if questions_added > 0:
        print(f"Success! Added {questions_added} real Jeopardy questions to your database.")
        print("Your Discord bot now has authentic questions from actual Jeopardy episodes!")
    else:
        print("No questions were added. Please check the logs for any issues.")