import click
from ..database.tools import initialize_database, show_database_stats, populate_jeopardy_questions


@click.group()
def db():
    """Database management."""
    pass

@click.command()
def init():
    """Initialize the database."""

    if initialize_database():
        print("Database initialized successfully.")
        show_database_stats()
    else:
        print("Database initialization failed.")

@click.command()
def info():
    """Show database statistics."""
    show_database_stats()

@click.command()
def populate():
    """Populate the database with Jeopardy questions."""
    if not initialize_database():
        print("Error: Could not initialize database. Exiting.")
        exit(1)
    show_database_stats()
    question_count_new = populate_jeopardy_questions()
    while question_count_new > 0:
        print(f"Added {question_count_new} new questions. Continuing...")
        show_database_stats()
        question_count_new = populate_jeopardy_questions()

db.add_command(init)
db.add_command(info)
db.add_command(populate)