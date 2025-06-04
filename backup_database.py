#!/usr/bin/env python3
"""
Database backup script for the Discord bot.
Supports multiple backup formats and provides restore functionality.
"""

import os
import sys
import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from database.models import get_session, JeopardyQuestion, GameSession, TurnoverUsage
from sqlalchemy import text
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger("backup_script")

class DatabaseBackup:
    """Database backup and restore utility."""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Parse database URL for pg_dump
        self.db_params = self._parse_database_url()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def _parse_database_url(self) -> Dict[str, str]:
        """Parse DATABASE_URL into components for pg_dump."""
        # Expected format: postgresql://user:password@host:port/database
        from urllib.parse import urlparse
        
        parsed = urlparse(self.database_url)
        database_name = ''
        if parsed.path:
            database_name = str(parsed.path)[1:] if str(parsed.path).startswith('/') else str(parsed.path)
        
        return {
            'host': str(parsed.hostname) if parsed.hostname else 'localhost',
            'port': str(parsed.port or 5432),
            'username': str(parsed.username) if parsed.username else '',
            'password': str(parsed.password) if parsed.password else '',
            'database': database_name
        }
    
    def create_pg_dump_backup(self, filename: Optional[str] = None) -> str:
        """
        Create a PostgreSQL dump backup using pg_dump.
        This is the recommended format for PostgreSQL backups.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discord_bot_backup_{timestamp}.sql"
        
        backup_path = self.backup_dir / filename
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', self.db_params['host'],
            '-p', self.db_params['port'],
            '-U', self.db_params['username'],
            '-d', self.db_params['database'],
            '--no-password',  # Use PGPASSWORD environment variable
            '--verbose',
            '--clean',  # Include DROP statements
            '--if-exists',  # Use IF EXISTS for DROP statements
            '-f', str(backup_path)
        ]
        
        # Set password as environment variable
        env = os.environ.copy()
        if self.db_params['password']:
            env['PGPASSWORD'] = self.db_params['password']
        
        try:
            logger.info(f"Creating pg_dump backup: {backup_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {backup_path}")
                logger.info(f"Backup size: {backup_path.stat().st_size / 1024:.2f} KB")
                return str(backup_path)
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                raise RuntimeError(f"pg_dump failed: {result.stderr}")
                
        except FileNotFoundError:
            logger.error("pg_dump command not found. Make sure PostgreSQL client tools are installed.")
            raise RuntimeError("pg_dump command not found")
    
    def create_json_backup(self, filename: Optional[str] = None) -> str:
        """
        Create a JSON backup of all data.
        This format is human-readable and portable but not as efficient.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discord_bot_backup_{timestamp}.json"
        
        backup_path = self.backup_dir / filename
        
        session = get_session()
        try:
            logger.info(f"Creating JSON backup: {backup_path}")
            
            # Extract all data
            backup_data = {
                'metadata': {
                    'backup_date': datetime.now().isoformat(),
                    'backup_type': 'json',
                    'version': '1.0'
                },
                'jeopardy_questions': [],
                'game_sessions': [],
                'turnover_usage': []
            }
            
            # Backup Jeopardy questions
            questions = session.query(JeopardyQuestion).all()
            for q in questions:
                backup_data['jeopardy_questions'].append({
                    'id': q.id,
                    'category': q.category,
                    'clue': q.clue,
                    'answer': q.answer,
                    'value': q.value,
                    'air_date': q.air_date,
                    'round_type': q.round_type,
                    'show_number': q.show_number,
                    'created_at': q.created_at.isoformat() if q.created_at is not None else None
                })
            
            # Backup game sessions
            sessions = session.query(GameSession).all()
            for s in sessions:
                backup_data['game_sessions'].append({
                    'id': s.id,
                    'channel_id': s.channel_id,
                    'question_id': s.question_id,
                    'is_active': s.is_active,
                    'timeout_seconds': s.timeout_seconds,
                    'created_at': s.created_at.isoformat() if s.created_at is not None else None
                })
            
            # Backup turnover usage
            usage_records = session.query(TurnoverUsage).all()
            for u in usage_records:
                backup_data['turnover_usage'].append({
                    'id': u.id,
                    'user_id': u.user_id,
                    'last_used_date': u.last_used_date,
                    'usage_count': u.usage_count,
                    'created_at': u.created_at.isoformat() if hasattr(u, 'created_at') and u.created_at is not None else None,
                    'updated_at': u.updated_at.isoformat() if hasattr(u, 'updated_at') and u.updated_at is not None else None
                })
            
            # Write to file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON backup created successfully: {backup_path}")
            logger.info(f"Backup contains: {len(backup_data['jeopardy_questions'])} questions, "
                       f"{len(backup_data['game_sessions'])} game sessions, "
                       f"{len(backup_data['turnover_usage'])} usage records")
            logger.info(f"Backup size: {backup_path.stat().st_size / 1024:.2f} KB")
            
            return str(backup_path)
            
        finally:
            session.close()
    
    def restore_from_pg_dump(self, backup_file: str) -> bool:
        """
        Restore database from a pg_dump backup file.
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Build psql command
        cmd = [
            'psql',
            '-h', self.db_params['host'],
            '-p', self.db_params['port'],
            '-U', self.db_params['username'],
            '-d', self.db_params['database'],
            '--no-password',
            '-f', str(backup_path)
        ]
        
        # Set password as environment variable
        env = os.environ.copy()
        if self.db_params['password']:
            env['PGPASSWORD'] = self.db_params['password']
        
        try:
            logger.info(f"Restoring from pg_dump backup: {backup_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully from pg_dump backup")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("psql command not found. Make sure PostgreSQL client tools are installed.")
            return False
    
    def restore_from_json(self, backup_file: str) -> bool:
        """
        Restore database from a JSON backup file.
        Note: This will clear existing data in the tables being restored.
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        session = get_session()
        try:
            logger.info(f"Restoring from JSON backup: {backup_path}")
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Verify backup format
            if 'metadata' not in backup_data:
                logger.error("Invalid backup file format")
                return False
            
            # Clear existing data (be careful!)
            logger.warning("Clearing existing data...")
            session.query(GameSession).delete()
            session.query(TurnoverUsage).delete()
            session.query(JeopardyQuestion).delete()
            session.commit()
            
            # Restore Jeopardy questions
            if 'jeopardy_questions' in backup_data:
                for q_data in backup_data['jeopardy_questions']:
                    question = JeopardyQuestion(
                        category=q_data['category'],
                        clue=q_data['clue'],
                        answer=q_data['answer'],
                        value=q_data.get('value'),
                        air_date=q_data.get('air_date'),
                        round_type=q_data.get('round_type'),
                        show_number=q_data.get('show_number')
                    )
                    session.add(question)
            
            # Restore turnover usage
            if 'turnover_usage' in backup_data:
                for u_data in backup_data['turnover_usage']:
                    usage = TurnoverUsage(
                        user_id=u_data['user_id'],
                        last_used_date=u_data['last_used_date'],
                        usage_count=u_data['usage_count']
                    )
                    session.add(usage)
            
            session.commit()
            logger.info("Database restored successfully from JSON backup")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def list_backups(self) -> list:
        """List all available backup files."""
        backups = []
        for backup_file in self.backup_dir.glob("discord_bot_backup_*"):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime),
                'type': 'sql' if backup_file.suffix == '.sql' else 'json'
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics."""
        session = get_session()
        try:
            stats = {
                'jeopardy_questions': session.query(JeopardyQuestion).count(),
                'game_sessions': session.query(GameSession).count(),
                'turnover_usage': session.query(TurnoverUsage).count()
            }
            return stats
        finally:
            session.close()

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Discord Bot Database Backup Utility")
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'stats'], 
                       help='Action to perform')
    parser.add_argument('--format', choices=['sql', 'json'], default='sql',
                       help='Backup format (default: sql)')
    parser.add_argument('--file', help='Backup file path for restore operation')
    parser.add_argument('--filename', help='Custom filename for backup')
    
    args = parser.parse_args()
    
    try:
        backup_util = DatabaseBackup()
        
        if args.action == 'backup':
            if args.format == 'sql':
                backup_path = backup_util.create_pg_dump_backup(args.filename)
            else:
                backup_path = backup_util.create_json_backup(args.filename)
            
            print(f"Backup created: {backup_path}")
            
        elif args.action == 'restore':
            if not args.file:
                print("Error: --file argument required for restore operation")
                sys.exit(1)
            
            backup_path = Path(args.file)
            if backup_path.suffix == '.sql':
                success = backup_util.restore_from_pg_dump(args.file)
            else:
                success = backup_util.restore_from_json(args.file)
            
            if success:
                print("Database restored successfully")
            else:
                print("Restore failed")
                sys.exit(1)
                
        elif args.action == 'list':
            backups = backup_util.list_backups()
            if not backups:
                print("No backups found")
            else:
                print("\nAvailable backups:")
                print("-" * 80)
                for backup in backups:
                    size_kb = backup['size'] / 1024
                    print(f"{backup['filename']:<40} {backup['type']:<4} "
                          f"{size_kb:>8.1f} KB  {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
        elif args.action == 'stats':
            stats = backup_util.get_database_stats()
            print("\nDatabase Statistics:")
            print("-" * 30)
            for table, count in stats.items():
                print(f"{table:<20}: {count:>8}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()