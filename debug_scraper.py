"""
Debug script to inspect the HTML structure of J-Archive pages.
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_game_page():
    """
    Inspect a single game page to understand the HTML structure.
    """
    # Use a recent game URL
    url = "https://www.j-archive.com/showgame.php?game_id=9219"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for Jeopardy round
    jeopardy_round = soup.find('div', id='jeopardy_round')
    if jeopardy_round:
        logger.info("Found Jeopardy round")
        
        # Find the first clue
        clue_cells = jeopardy_round.find_all('td', class_='clue')
        if clue_cells:
            first_clue = clue_cells[0]
            logger.info(f"First clue HTML: {first_clue}")
            
            # Look for any links
            links = first_clue.find_all('a')
            for i, link in enumerate(links):
                logger.info(f"Link {i}: {link}")
                logger.info(f"Attributes: {link.attrs}")
                
                # Check each attribute for answer
                for attr_name, attr_value in link.attrs.items():
                    if isinstance(attr_value, str) and len(attr_value) > 50:
                        logger.info(f"Long attribute {attr_name}: {attr_value[:200]}...")

if __name__ == "__main__":
    inspect_game_page()