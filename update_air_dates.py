#!/usr/bin/env python3
"""
Script to update air_dates for existing Jeopardy questions.
This script will try to extract air dates from show numbers and update the database.
Includes resume functionality and comprehensive error handling.
"""

import logging
import json
import os
import time
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

# Progress tracking file
PROGRESS_FILE = 'air_date_update_progress.json'

def load_progress():
    """Load progress from file if it exists."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(data):
    """Save progress to file."""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Could not save progress: {e}")

def update_air_dates_from_show_numbers():
    """
    Update air_dates for questions that have show_numbers but missing air_dates.
    Process all questions in batches until complete with resume functionality.
    """
    session = get_session()
    scraper = JeopardyScraper(delay_seconds=0.3)  # Optimized speed
    
    # Load previous progress
    progress = load_progress()
    processed_shows_set = set(progress.get('processed_shows', []))
    failed_shows_set = set(progress.get('failed_shows', []))
    
    try:
        # Get all unique show numbers that need air_date updates
        unique_shows = session.query(JeopardyQuestion.show_number).filter(
            JeopardyQuestion.show_number.isnot(None),
            (JeopardyQuestion.air_date.is_(None) | (JeopardyQuestion.air_date == ''))
        ).distinct().all()
        
        unique_show_numbers = [int(show[0]) for show in unique_shows if show[0] is not None]
        
        # Remove already processed shows
        remaining_shows = [show for show in unique_show_numbers 
                          if show not in processed_shows_set and show not in failed_shows_set]
        
        logger.info(f"Total unique shows: {len(unique_show_numbers)}")
        logger.info(f"Already processed: {len(processed_shows_set)}")
        logger.info(f"Previously failed: {len(failed_shows_set)}")
        logger.info(f"Remaining to process: {len(remaining_shows)}")
        
        if not remaining_shows:
            logger.info("All shows have been processed!")
            return
        
        total_updated = progress.get('total_updated', 0)
        start_time = time.time()
        
        for i, show_number in enumerate(remaining_shows):
            # Construct J-Archive URL for the show
            game_url = f"http://j-archive.com/showgame.php?game_id={show_number}"
            
            try:
                # Scrape the game page to get air_date
                game_questions = scraper.scrape_game_questions(game_url, show_number)
                
                if game_questions and len(game_questions) > 0 and game_questions[0].get('air_date'):
                    air_date = game_questions[0]['air_date']
                    
                    # Update all questions from this show in one query
                    updated_count = session.query(JeopardyQuestion).filter_by(
                        show_number=show_number
                    ).update({'air_date': air_date})
                    
                    session.commit()
                    total_updated += updated_count
                    processed_shows_set.add(show_number)
                    
                    logger.info(f"Progress: {i+1}/{len(remaining_shows)} - "
                              f"Show {show_number}: Updated {updated_count} questions "
                              f"with air_date: {air_date}")
                else:
                    logger.warning(f"No air_date found for show {show_number}")
                    failed_shows_set.add(show_number)
                    
            except Exception as e:
                logger.warning(f"Error updating show {show_number}: {e}")
                failed_shows_set.add(show_number)
                session.rollback()
                continue
            
            # Save progress every 10 shows
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed * 60  # shows per minute
                eta_minutes = (len(remaining_shows) - i - 1) / rate if rate > 0 else 0
                
                progress_data = {
                    'processed_shows': list(processed_shows_set),
                    'failed_shows': list(failed_shows_set),
                    'total_updated': total_updated
                }
                save_progress(progress_data)
                
                logger.info(f"Batch progress: {i+1}/{len(remaining_shows)} shows, "
                          f"{total_updated} total questions updated, "
                          f"Rate: {rate:.1f} shows/min, ETA: {eta_minutes:.1f} min")
        
        # Final save
        progress_data = {
            'processed_shows': list(processed_shows_set),
            'failed_shows': list(failed_shows_set),
            'total_updated': total_updated
        }
        save_progress(progress_data)
        
        logger.info(f"Completed! Updated {total_updated} questions total")
        logger.info(f"Successfully processed: {len(processed_shows_set)} shows")
        logger.info(f"Failed: {len(failed_shows_set)} shows")
        
        # Final statistics
        remaining = session.query(JeopardyQuestion).filter(
            JeopardyQuestion.show_number.isnot(None),
            (JeopardyQuestion.air_date.is_(None) | (JeopardyQuestion.air_date == ''))
        ).count()
        
        logger.info(f"Remaining questions without air_date: {remaining}")
        
        if remaining == 0:
            logger.info("SUCCESS: All questions now have air dates!")
            # Clean up progress file
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Progress has been saved.")
        progress_data = {
            'processed_shows': list(processed_shows_set),
            'failed_shows': list(failed_shows_set),
            'total_updated': total_updated
        }
        save_progress(progress_data)
        raise
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

def get_database_status():
    """Get current status of air date population."""
    session = get_session()
    try:
        total_questions = session.query(JeopardyQuestion).count()
        with_air_dates = session.query(JeopardyQuestion).filter(
            JeopardyQuestion.air_date.isnot(None),
            JeopardyQuestion.air_date != ''
        ).count()
        without_air_dates = session.query(JeopardyQuestion).filter(
            JeopardyQuestion.show_number.isnot(None),
            (JeopardyQuestion.air_date.is_(None) | (JeopardyQuestion.air_date == ''))
        ).count()
        
        unique_shows_total = session.query(JeopardyQuestion.show_number).filter(
            JeopardyQuestion.show_number.isnot(None)
        ).distinct().count()
        
        unique_shows_missing = session.query(JeopardyQuestion.show_number).filter(
            JeopardyQuestion.show_number.isnot(None),
            (JeopardyQuestion.air_date.is_(None) | (JeopardyQuestion.air_date == ''))
        ).distinct().count()
        
        percentage_complete = (with_air_dates / total_questions * 100) if total_questions > 0 else 0
        
        logger.info(f"Database Status:")
        logger.info(f"  Total questions: {total_questions:,}")
        logger.info(f"  Questions with air dates: {with_air_dates:,} ({percentage_complete:.1f}%)")
        logger.info(f"  Questions missing air dates: {without_air_dates:,}")
        logger.info(f"  Total unique shows: {unique_shows_total:,}")
        logger.info(f"  Shows missing air dates: {unique_shows_missing:,}")
        
        return {
            'total_questions': total_questions,
            'with_air_dates': with_air_dates,
            'without_air_dates': without_air_dates,
            'percentage_complete': percentage_complete,
            'unique_shows_total': unique_shows_total,
            'unique_shows_missing': unique_shows_missing
        }
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        logger.info("Checking database status...")
        get_database_status()
    elif len(sys.argv) > 1 and sys.argv[1] == 'test':
        logger.info("Testing air date extraction...")
        test_air_date_extraction()
    else:
        logger.info("Starting comprehensive air date update process...")
        
        # Show initial status
        logger.info("Initial database status:")
        get_database_status()
        
        # Run the update process
        logger.info("Beginning air date extraction and update...")
        update_air_dates_from_show_numbers()
        
        # Show final status
        logger.info("Final database status:")
        get_database_status()
        
        logger.info("Air date update process completed")
        logger.info("Usage: python update_air_dates.py [status|test]")