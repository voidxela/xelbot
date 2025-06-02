"""
Test script to verify the improved Jeopardy scraper.
"""

import logging
from scraper.jeopardy_scraper import JeopardyScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)

logger = logging.getLogger(__name__)

def test_single_game():
    """
    Test scraping a single recent game to verify the scraper works.
    """
    scraper = JeopardyScraper(delay_seconds=1.0)
    
    try:
        # Get recent seasons
        logger.info("Getting season list...")
        seasons = scraper.get_season_list()
        
        if not seasons:
            logger.error("No seasons found")
            return
        
        # Get the most recent season
        recent_season = sorted(seasons, key=lambda x: x['season'], reverse=True)[0]
        logger.info(f"Testing with season {recent_season['season']}")
        
        # Get games from that season
        games = scraper.get_games_from_season(recent_season['url'])
        
        if not games:
            logger.error("No games found in recent season")
            return
        
        # Test with the first game
        test_game = games[0]
        logger.info(f"Testing with game {test_game['game_id']}")
        
        # Scrape questions from this game
        questions = scraper.scrape_game_questions(test_game['url'], test_game['game_id'])
        
        if questions:
            logger.info(f"Successfully scraped {len(questions)} questions!")
            
            # Show a few examples
            for i, q in enumerate(questions[:3]):
                logger.info(f"Example {i+1}:")
                logger.info(f"  Category: {q['category']}")
                logger.info(f"  Clue: {q['clue'][:100]}...")
                logger.info(f"  Answer: {q['answer']}")
                logger.info(f"  Value: ${q['value'] if q['value'] else 'Unknown'}")
                logger.info(f"  Round: {q['round_type']}")
                logger.info("")
            
            return len(questions)
        else:
            logger.error("No questions scraped from the test game")
            return 0
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 0

if __name__ == "__main__":
    questions_found = test_single_game()
    if questions_found > 0:
        print(f"Scraper test successful! Found {questions_found} questions.")
    else:
        print("Scraper test failed - no questions found.")