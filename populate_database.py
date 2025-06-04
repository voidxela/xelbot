"""
Production script to populate the database with real Jeopardy questions.
Tracks which games have been scraped to avoid duplicates and resume from last position.
"""

import logging
from scraper.jeopardy_scraper import JeopardyScraper
from database.models import get_session, JeopardyQuestion, create_tables
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')

logger = logging.getLogger(__name__)


def initialize_database():
    """
    Initialize the database by creating tables if they don't exist.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Checking database initialization...")

        # Try to query the database to see if tables exist
        db_session = get_session()
        try:
            # Simple query to check if the main table exists
            db_session.query(JeopardyQuestion).count()
            logger.info("Database tables already exist")
            return True
        except OperationalError as e:
            # Tables don't exist, create them
            logger.info("Database tables not found, creating them...")
            db_session.close()

            # Create the tables
            create_tables()
            logger.info("Database tables created successfully")
            return True
        finally:
            if db_session:
                db_session.close()

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False


def get_scraped_games():
    """Get list of game IDs that have already been scraped."""
    db_session = get_session()
    try:
        scraped_games = set()
        results = db_session.query(
            JeopardyQuestion.show_number).distinct().all()
        for (game_id, ) in results:
            if game_id:
                scraped_games.add(game_id)
        return scraped_games
    except Exception as e:
        logger.error(f"Error getting scraped games: {e}")
        return set()
    finally:
        db_session.close()


def populate_jeopardy_questions():
    """
    Populate database with real Jeopardy questions from multiple games.
    Continues from where previous runs left off.
    """
    scraper = JeopardyScraper(delay_seconds=2.0)

    try:
        scraped_games = get_scraped_games()
        logger.info(f"Found {len(scraped_games)} games already in database")
        seasons = sorted(scraper.get_season_list(),
                         key=lambda x: x['season'],
                         reverse=True)
        if not seasons:
            logger.error("Could not retrieve season list")
            return 0
        season_index = 0
        season = seasons[season_index]
        logger.info(f"Using season {season['season']}")
        games = scraper.get_games_from_season(season['url'])
        if not games:
            logger.error("No games found in season")
            return 0
        new_games = [
            game for game in games if game['game_id'] not in scraped_games
        ]
        while not new_games and season_index < len(seasons):
            logger.info("All games in this season have already been scraped")
            second_season = sorted(seasons,
                                   key=lambda x: x['season'],
                                   reverse=True)[1]
            logger.info(f"Trying season {second_season['season']}")
            games = scraper.get_games_from_season(second_season['url'])
            new_games = [
                game for game in games if game['game_id'] not in scraped_games
            ]
        if not new_games:
            logger.info("No new games to scrape")
            return 0
        logger.info(f"Found {len(new_games)} new games to scrape")
        total_questions = 0
        games_processed = 0
        for game in new_games:
            logger.info(
                f"Processing game {game['game_id']} ({games_processed + 1}/{len(new_games)})"
            )

            questions = scraper.scrape_game_questions(game['url'],
                                                      game['game_id'])

            if questions:
                saved = scraper.save_questions_to_database(questions)
                total_questions += saved
                logger.info(
                    f"Saved {saved} questions from game {game['game_id']}")
            else:
                logger.warning(f"No questions found in game {game['game_id']}")

            games_processed += 1

        logger.info(
            f"Completed! Processed {games_processed} new games and added {total_questions} questions to the database."
        )

        # Show final stats
        db_session = get_session()
        try:
            total_in_db = db_session.query(JeopardyQuestion).count()
            unique_games = db_session.query(
                JeopardyQuestion.show_number).distinct().count()
            logger.info(
                f"Database now contains {total_in_db} questions from {unique_games} games"
            )
        except Exception as e:
            logger.error(f"Error getting final stats: {e}")
        finally:
            db_session.close()

        return total_questions

    except Exception as e:
        logger.error(f"Error during database population: {e}")
        return 0


def show_database_stats():
    """Show current database statistics."""
    try:
        db_session = get_session()
        try:
            total_questions = db_session.query(JeopardyQuestion).count()
            unique_games = db_session.query(
                JeopardyQuestion.show_number).distinct().count()

            # Get category distribution
            from sqlalchemy import func
            category_counts = db_session.query(
                JeopardyQuestion.category,
                func.count(JeopardyQuestion.id).label('count')).group_by(
                    JeopardyQuestion.category).order_by(
                        func.count(
                            JeopardyQuestion.id).desc()).limit(10).all()

            print(f"\n=== Database Statistics ===")
            print(f"Total questions: {total_questions}")
            print(f"Unique games: {unique_games}")
            print(f"\nTop 10 categories:")
            for category, count in category_counts:
                print(f"  {category}: {count} questions")

            return total_questions
        finally:
            db_session.close()

    except OperationalError as e:
        logger.warning(
            "Database tables don't exist yet. No statistics available.")
        print(f"\n=== Database Statistics ===")
        print("Database not initialized yet.")
        return 0
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        print(f"\n=== Database Statistics ===")
        print(f"Error accessing database: {e}")
        return 0


if __name__ == "__main__":
    print("Jeopardy Database Population Script")
    print("=" * 40)

    # Initialize database if needed
    if not initialize_database():
        print("Error: Could not initialize database. Exiting.")
        exit(1)

    # Show current stats
    current_total = show_database_stats()

    # Start scraping
    populate_jeopardy_questions()
