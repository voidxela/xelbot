"""
Web scraper for J-Archive Jeopardy questions.
This scraper is designed to be gentle on the servers with delays between requests.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import logging
from typing import List, Dict, Optional
from database.models import JeopardyQuestion, get_session, create_tables

# Setup logging
logger = logging.getLogger(__name__)

class JeopardyScraper:
    """
    Scraper for J-Archive.com to collect Jeopardy questions and answers.
    """
    
    def __init__(self, delay_seconds: float = 2.0):
        """
        Initialize the scraper.
        
        Args:
            delay_seconds: Delay between requests to be gentle on the server
        """
        self.base_url = "https://www.j-archive.com"
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_season_list(self) -> List[Dict]:
        """
        Get list of all seasons from the main page.
        
        Returns:
            List of season information dictionaries
        """
        try:
            response = self.session.get(f"{self.base_url}/listseasons.php")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            seasons = []
            
            # Find season links
            for link in soup.find_all('a', href=re.compile(r'showseason\.php\?season=\d+')):
                season_match = re.search(r'season=(\d+)', link['href'])
                if season_match:
                    season_num = int(season_match.group(1))
                    seasons.append({
                        'season': season_num,
                        'url': f"{self.base_url}/{link['href']}",
                        'text': link.get_text(strip=True)
                    })
            
            logger.info(f"Found {len(seasons)} seasons")
            return seasons
            
        except Exception as e:
            logger.error(f"Error getting season list: {e}")
            return []
    
    def get_games_from_season(self, season_url: str) -> List[Dict]:
        """
        Get list of games from a specific season.
        
        Args:
            season_url: URL of the season page
            
        Returns:
            List of game information dictionaries
        """
        try:
            time.sleep(self.delay_seconds)  # Be gentle on the server
            
            response = self.session.get(season_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            games = []
            
            # Find game links
            for link in soup.find_all('a', href=re.compile(r'showgame\.php\?game_id=\d+')):
                game_match = re.search(r'game_id=(\d+)', link['href'])
                if game_match:
                    game_id = int(game_match.group(1))
                    games.append({
                        'game_id': game_id,
                        'url': f"{self.base_url}/{link['href']}",
                        'text': link.get_text(strip=True)
                    })
            
            logger.info(f"Found {len(games)} games in season")
            return games
            
        except Exception as e:
            logger.error(f"Error getting games from season: {e}")
            return []
    
    def scrape_game_questions(self, game_url: str, game_id: int) -> List[Dict]:
        """
        Scrape questions from a specific game.
        
        Args:
            game_url: URL of the game page
            game_id: ID of the game
            
        Returns:
            List of question dictionaries
        """
        try:
            time.sleep(self.delay_seconds)  # Be gentle on the server
            
            response = self.session.get(game_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            questions = []
            
            # Get air date
            air_date = None
            date_elem = soup.find('div', id='game_title')
            if date_elem:
                date_text = date_elem.get_text()
                date_match = re.search(r'aired (\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    air_date = date_match.group(1)
            
            # Find all clue divs
            clue_divs = soup.find_all('td', class_='clue')
            
            for clue_div in clue_divs:
                try:
                    # Get the clue text
                    clue_text_elem = clue_div.find('td', class_='clue_text')
                    if not clue_text_elem:
                        continue
                    
                    clue_text = clue_text_elem.get_text(strip=True)
                    if not clue_text:
                        continue
                    
                    # Get the answer from the mouseover attribute
                    clue_link = clue_text_elem.find('a')
                    if not clue_link or 'onmouseover' not in clue_link.attrs:
                        continue
                    
                    mouseover = clue_link['onmouseover']
                    answer_match = re.search(r"correct_response'>\s*([^<]+)", mouseover)
                    if not answer_match:
                        continue
                    
                    answer = answer_match.group(1).strip()
                    
                    # Get category from the header
                    category = None
                    category_elem = clue_div.find_parent('table').find('td', class_='category_name')
                    if category_elem:
                        category = category_elem.get_text(strip=True)
                    
                    # Get value
                    value = None
                    value_elem = clue_div.find('td', class_='clue_value')
                    if value_elem:
                        value_text = value_elem.get_text(strip=True)
                        value_match = re.search(r'\$?([\d,]+)', value_text)
                        if value_match:
                            value = int(value_match.group(1).replace(',', ''))
                    
                    # Determine round type based on the section
                    round_type = "Jeopardy"
                    if clue_div.find_parent('div', id='double_jeopardy_round'):
                        round_type = "Double Jeopardy"
                    elif clue_div.find_parent('div', id='final_jeopardy_round'):
                        round_type = "Final Jeopardy"
                    
                    questions.append({
                        'category': category or 'Unknown',
                        'clue': clue_text,
                        'answer': answer,
                        'value': value,
                        'air_date': air_date,
                        'round_type': round_type,
                        'show_number': game_id
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing clue: {e}")
                    continue
            
            logger.info(f"Scraped {len(questions)} questions from game {game_id}")
            return questions
            
        except Exception as e:
            logger.error(f"Error scraping game {game_id}: {e}")
            return []
    
    def save_questions_to_database(self, questions: List[Dict]) -> int:
        """
        Save questions to the database.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Number of questions saved
        """
        session = get_session()
        saved_count = 0
        
        try:
            for q_data in questions:
                # Check if question already exists
                existing = session.query(JeopardyQuestion).filter_by(
                    clue=q_data['clue'],
                    answer=q_data['answer']
                ).first()
                
                if not existing:
                    question = JeopardyQuestion(
                        category=q_data['category'],
                        clue=q_data['clue'],
                        answer=q_data['answer'],
                        value=q_data['value'],
                        air_date=q_data['air_date'],
                        round_type=q_data['round_type'],
                        show_number=q_data['show_number']
                    )
                    session.add(question)
                    saved_count += 1
            
            session.commit()
            logger.info(f"Saved {saved_count} new questions to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to database: {e}")
        finally:
            session.close()
        
        return saved_count
    
    def scrape_limited_data(self, max_seasons: int = 2, max_games_per_season: int = 5) -> int:
        """
        Scrape a limited amount of data for testing purposes.
        
        Args:
            max_seasons: Maximum number of seasons to scrape
            max_games_per_season: Maximum games per season
            
        Returns:
            Total number of questions scraped
        """
        logger.info("Starting limited Jeopardy data scraping...")
        
        # Create tables if they don't exist
        create_tables()
        
        total_questions = 0
        seasons = self.get_season_list()
        
        # Take only the most recent seasons
        recent_seasons = sorted(seasons, key=lambda x: x['season'], reverse=True)[:max_seasons]
        
        for season in recent_seasons:
            logger.info(f"Scraping season {season['season']}")
            games = self.get_games_from_season(season['url'])
            
            # Take only a few games from each season
            limited_games = games[:max_games_per_season]
            
            for game in limited_games:
                questions = self.scrape_game_questions(game['url'], game['game_id'])
                if questions:
                    saved = self.save_questions_to_database(questions)
                    total_questions += saved
                
                # Extra delay between games
                time.sleep(self.delay_seconds)
        
        logger.info(f"Completed scraping. Total questions: {total_questions}")
        return total_questions

def run_initial_scrape():
    """
    Run an initial scrape to populate the database with some questions.
    """
    scraper = JeopardyScraper(delay_seconds=1.5)  # Be gentle on the server
    return scraper.scrape_limited_data(max_seasons=2, max_games_per_season=3)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the scraper
    questions_count = run_initial_scrape()
    print(f"Scraped {questions_count} questions successfully!")