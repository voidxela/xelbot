"""
Web scraper for J-Archive Jeopardy questions with improved category extraction.
This scraper is designed to be gentle on the servers with delays between requests.
"""

import requests
import time
import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict
from database.models import get_session, JeopardyQuestion

logger = logging.getLogger(__name__)

class JeopardyScraper:
    """
    Enhanced scraper for J-Archive.com with improved category matching.
    """
    
    def __init__(self, delay_seconds: float = 2.0):
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
            response = self.session.get("https://www.j-archive.com/listseasons.php")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            seasons = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'showseason.php?season=' in href:
                    season_match = re.search(r'season=(\d+)', href)
                    if season_match:
                        season_num = int(season_match.group(1))
                        seasons.append({
                            'season': season_num,
                            'url': f"https://www.j-archive.com/{href}"
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
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'showgame.php?game_id=' in href:
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
            logger.error(f"Error getting games from season: {e}")
            return []
    
    def scrape_game_questions(self, game_url: str, game_id: int) -> List[Dict]:
        """
        Scrape questions from a specific game with improved category extraction.
        """
        try:
            time.sleep(self.delay_seconds)
            
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
            
            # Process each round
            rounds = [
                ('jeopardy_round', 'Jeopardy'),
                ('double_jeopardy_round', 'Double Jeopardy'),
                ('final_jeopardy_round', 'Final Jeopardy')
            ]
            
            for round_id, round_name in rounds:
                round_div = soup.find('div', id=round_id)
                if not round_div:
                    continue
                
                # For Final Jeopardy, handle differently
                if round_name == 'Final Jeopardy':
                    questions.extend(self._parse_final_jeopardy(round_div, air_date, game_id))
                    continue
                
                # Get the main game board table
                game_table = round_div.find('table')
                if not game_table:
                    continue
                
                # Extract categories from the header row
                categories = []
                header_row = game_table.find('tr')
                if header_row:
                    for cat_cell in header_row.find_all('td', class_='category_name'):
                        categories.append(cat_cell.get_text(strip=True))
                
                # Get all data rows (skip header)
                data_rows = game_table.find_all('tr')[1:]
                
                # Standard Jeopardy values
                if round_name == 'Jeopardy':
                    standard_values = [200, 400, 600, 800, 1000]
                else:  # Double Jeopardy
                    standard_values = [400, 800, 1200, 1600, 2000]
                
                # Process each row
                for row_idx, row in enumerate(data_rows):
                    clue_cells = row.find_all('td', class_='clue')
                    
                    for col_idx, clue_cell in enumerate(clue_cells):
                        question_data = self._parse_clue_cell(
                            clue_cell, categories, col_idx, row_idx, 
                            standard_values, air_date, round_name, game_id
                        )
                        if question_data:
                            questions.append(question_data)
            
            logger.info(f"Scraped {len(questions)} questions from game {game_id}")
            return questions
            
        except Exception as e:
            logger.error(f"Error scraping game {game_id}: {e}")
            return []
    
    def _parse_clue_cell(self, clue_cell, categories, col_idx, row_idx, 
                        standard_values, air_date, round_name, game_id):
        """Parse a single clue cell and return question data."""
        try:
            # Get clue text
            clue_text_elem = clue_cell.find('td', class_='clue_text')
            if not clue_text_elem:
                return None
            
            clue_text = clue_text_elem.get_text(strip=True)
            if not clue_text or clue_text == "=":
                return None
            
            # Get answer from correct_response element
            correct_response_elem = clue_cell.find('em', class_='correct_response')
            if not correct_response_elem:
                return None
            
            answer = correct_response_elem.get_text(strip=True)
            if not answer:
                return None
            
            # Clean up answer
            answer = re.sub(r'<[^>]+>', '', answer)
            answer = answer.replace('&nbsp;', ' ').strip()
            
            # Get category
            category = "Unknown"
            if categories and col_idx < len(categories):
                category = categories[col_idx]
            
            # Get value - try from clue_value element first, then use standard values
            value = None
            value_elem = clue_cell.find('td', class_='clue_value')
            if value_elem:
                value_text = value_elem.get_text(strip=True)
                value_match = re.search(r'\$?([\d,]+)', value_text)
                if value_match:
                    value = int(value_match.group(1).replace(',', ''))
            
            # If no value found, use standard values based on position
            if not value and row_idx < len(standard_values):
                value = standard_values[row_idx]
            
            return {
                'category': category,
                'clue': clue_text,
                'answer': answer,
                'value': value,
                'air_date': air_date,
                'round_type': round_name,
                'show_number': game_id
            }
            
        except Exception as e:
            logger.warning(f"Error parsing clue cell: {e}")
            return None
    
    def _parse_final_jeopardy(self, round_div, air_date, game_id):
        """Parse Final Jeopardy round."""
        questions = []
        try:
            # Get category
            category_elem = round_div.find('td', class_='category_name')
            category = category_elem.get_text(strip=True) if category_elem else "Final Jeopardy"
            
            # Get clue
            clue_elem = round_div.find('td', class_='clue_text')
            if not clue_elem:
                return questions
            
            clue_text = clue_elem.get_text(strip=True)
            
            # Get answer
            correct_response_elem = round_div.find('em', class_='correct_response')
            if not correct_response_elem:
                return questions
            
            answer = correct_response_elem.get_text(strip=True)
            answer = re.sub(r'<[^>]+>', '', answer)
            answer = answer.replace('&nbsp;', ' ').strip()
            
            questions.append({
                'category': category,
                'clue': clue_text,
                'answer': answer,
                'value': None,  # Final Jeopardy doesn't have standard values
                'air_date': air_date,
                'round_type': 'Final Jeopardy',
                'show_number': game_id
            })
            
        except Exception as e:
            logger.warning(f"Error parsing Final Jeopardy: {e}")
        
        return questions
    
    def save_questions_to_database(self, questions: List[Dict]) -> int:
        """Save questions to the database."""
        if not questions:
            return 0
        
        db_session = get_session()
        saved_count = 0
        
        try:
            for q_data in questions:
                # Check if question already exists
                existing = db_session.query(JeopardyQuestion).filter_by(
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
                    db_session.add(question)
                    saved_count += 1
            
            db_session.commit()
            logger.info(f"Saved {saved_count} new questions to database")
            return saved_count
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Database error: {e}")
            return 0
        finally:
            db_session.close()

def test_improved_scraper():
    """Test the improved scraper."""
    scraper = ImprovedJeopardyScraper(delay_seconds=1.0)
    
    # Test with a known game
    game_url = "https://www.j-archive.com/showgame.php?game_id=9219"
    questions = scraper.scrape_game_questions(game_url, 9219)
    
    if questions:
        print(f"Found {len(questions)} questions")
        for i, q in enumerate(questions[:3]):
            print(f"\nExample {i+1}:")
            print(f"Category: {q['category']}")
            print(f"Clue: {q['clue'][:100]}...")
            print(f"Answer: {q['answer']}")
            print(f"Value: ${q['value'] if q['value'] else 'N/A'}")
            print(f"Round: {q['round_type']}")
    else:
        print("No questions found")

if __name__ == "__main__":
    test_improved_scraper()