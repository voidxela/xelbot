"""
Seed the database with a few sample Jeopardy questions to test the game functionality.
"""

from database.models import JeopardyQuestion, get_session, create_tables
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_questions():
    """
    Add sample questions to test the Jeopardy game.
    """
    # Create tables first
    create_tables()
    
    session = get_session()
    
    sample_questions = [
        {
            'category': 'WORLD CAPITALS',
            'clue': 'This city is the capital of France.',
            'answer': 'What is Paris?',
            'value': 200,
            'round_type': 'Jeopardy',
            'show_number': 1,
            'air_date': '2024-01-01'
        },
        {
            'category': 'SCIENCE',
            'clue': 'This element has the chemical symbol "O".',
            'answer': 'What is oxygen?',
            'value': 400,
            'round_type': 'Jeopardy',
            'show_number': 1,
            'air_date': '2024-01-01'
        },
        {
            'category': 'MOVIES',
            'clue': 'This 1994 film starred Tom Hanks as a man with a low IQ who witnesses historic events.',
            'answer': 'What is Forrest Gump?',
            'value': 600,
            'round_type': 'Jeopardy',
            'show_number': 1,
            'air_date': '2024-01-01'
        },
        {
            'category': 'PRESIDENTS',
            'clue': 'This president was known as "Honest Abe".',
            'answer': 'Who is Abraham Lincoln?',
            'value': 800,
            'round_type': 'Double Jeopardy',
            'show_number': 1,
            'air_date': '2024-01-01'
        },
        {
            'category': 'ANIMALS',
            'clue': 'This large mammal is known as the "King of the Jungle".',
            'answer': 'What is a lion?',
            'value': 1000,
            'round_type': 'Double Jeopardy',
            'show_number': 1,
            'air_date': '2024-01-01'
        }
    ]
    
    try:
        added_count = 0
        for q_data in sample_questions:
            # Check if question already exists
            existing = session.query(JeopardyQuestion).filter_by(
                clue=q_data['clue']
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
                added_count += 1
        
        session.commit()
        logger.info(f"Added {added_count} sample questions to the database")
        
        # Check total count
        total = session.query(JeopardyQuestion).count()
        logger.info(f"Total questions in database: {total}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding sample questions: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_questions()
    print("Sample questions added successfully! Your Jeopardy game is ready to test.")