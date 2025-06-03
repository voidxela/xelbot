"""
Script to clean existing questions with missing categories and repopulate with improved data.
"""

import logging
from scraper.improved_scraper import ImprovedJeopardyScraper
from database.models import get_session, JeopardyQuestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_and_repopulate():
    """Remove questions with 'Unknown' category and add better quality data."""
    
    # First, let's see what we have
    db_session = get_session()
    
    try:
        # Count current questions
        total_questions = db_session.query(JeopardyQuestion).count()
        unknown_questions = db_session.query(JeopardyQuestion).filter_by(category='Unknown').count()
        
        logger.info(f"Current database: {total_questions} total questions, {unknown_questions} with 'Unknown' category")
        
        # Remove questions with Unknown category
        if unknown_questions > 0:
            db_session.query(JeopardyQuestion).filter_by(category='Unknown').delete()
            db_session.commit()
            logger.info(f"Removed {unknown_questions} questions with 'Unknown' category")
        
        # Get updated count
        remaining_questions = db_session.query(JeopardyQuestion).count()
        logger.info(f"Remaining questions: {remaining_questions}")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        db_session.rollback()
        return 0
    finally:
        db_session.close()
    
    # Now add better quality questions
    scraper = ImprovedJeopardyScraper(delay_seconds=1.5)
    
    try:
        # Get a recent season to ensure good data
        seasons = scraper.get_season_list()
        if not seasons:
            logger.error("Could not get season list")
            return 0
        
        recent_season = sorted(seasons, key=lambda x: x['season'], reverse=True)[0]
        logger.info(f"Using season {recent_season['season']}")
        
        games = scraper.get_games_from_season(recent_season['url'])
        if not games:
            logger.error("No games found")
            return 0
        
        # Process 3 games to get high-quality questions
        total_added = 0
        for game in games[:3]:
            logger.info(f"Processing game {game['game_id']}")
            questions = scraper.scrape_game_questions(game['url'], game['game_id'])
            
            if questions:
                saved = scraper.save_questions_to_database(questions)
                total_added += saved
                logger.info(f"Added {saved} questions from game {game['game_id']}")
        
        logger.info(f"Successfully added {total_added} high-quality questions")
        return total_added
        
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return 0

def get_season_list(scraper):
    """Get the list of seasons from J-Archive."""
    try:
        response = scraper.session.get("https://www.j-archive.com/listseasons.php")
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        seasons = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'showseason.php?season=' in href:
                import re
                season_match = re.search(r'season=(\d+)', href)
                if season_match:
                    season_num = int(season_match.group(1))
                    seasons.append({
                        'season': season_num,
                        'url': f"https://www.j-archive.com/{href}"
                    })
        
        return seasons
        
    except Exception as e:
        logger.error(f"Error getting seasons: {e}")
        return []

def get_games_from_season(scraper, season_url):
    """Get games from a season."""
    try:
        import time
        time.sleep(scraper.delay_seconds)
        
        response = scraper.session.get(season_url)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        games = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'showgame.php?game_id=' in href:
                import re
                game_match = re.search(r'game_id=(\d+)', href)
                if game_match:
                    game_id = int(game_match.group(1))
                    games.append({
                        'game_id': game_id,
                        'url': f"https://www.j-archive.com/{href}"
                    })
        
        logger.info(f"Found {len(games)} games in season")
        return games
        
    except Exception as e:
        logger.error(f"Error getting games: {e}")
        return []

# Add these methods to the scraper class
ImprovedJeopardyScraper.get_season_list = lambda self: get_season_list(self)
ImprovedJeopardyScraper.get_games_from_season = lambda self, url: get_games_from_season(self, url)

if __name__ == "__main__":
    added = clean_and_repopulate()
    if added > 0:
        print(f"Database cleaned and repopulated with {added} high-quality questions!")
    else:
        print("No questions were added. Check the logs for issues.")