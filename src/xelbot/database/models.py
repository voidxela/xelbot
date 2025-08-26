"""
Database models for the Jeopardy game.
"""

import os
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

class JeopardyQuestion(Base):
    """
    Model for storing Jeopardy questions and answers.
    """
    __tablename__ = 'jeopardy_questions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(255), nullable=False)
    clue = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    value = Column(Integer, nullable=True)  # Dollar value of the question
    air_date = Column(String(50), nullable=True)
    round_type = Column(String(50), nullable=True)  # Jeopardy, Double Jeopardy, Final Jeopardy
    show_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<JeopardyQuestion(id={self.id}, category='{self.category}', value={self.value})>"

class GameSession(Base):
    """
    Model for tracking active Jeopardy game sessions in Discord channels.
    """
    __tablename__ = 'game_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(50), nullable=False, unique=True)
    question_id = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    timeout_seconds = Column(Integer, default=30)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<GameSession(channel_id={self.channel_id}, question_id={self.question_id}, active={self.is_active})>"

class TurnoverUsage(Base):
    """
    Model for tracking turnover command usage with daily cooldowns.
    """
    __tablename__ = 'turnover_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, unique=True)
    last_used_date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD in Eastern time
    usage_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TurnoverUsage(user_id={self.user_id}, last_used_date={self.last_used_date}, usage_count={self.usage_count})>"

# Database setup
def get_database_url():
    """Get database URL from environment variables."""
    return os.getenv('DATABASE_URL')

def create_database_engine():
    """Create database engine."""
    database_url = get_database_url()
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    engine = create_engine(database_url, echo=False)
    return engine

def create_tables():
    """Create all tables in the database."""
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get database session."""
    engine = create_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()