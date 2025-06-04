# Discord Bot Database Backup Guide

## Overview

Your Discord bot now includes a comprehensive database backup system that supports multiple backup formats and provides easy restoration capabilities. The system automatically handles your PostgreSQL database containing Jeopardy questions, game sessions, and user usage data.

## Available Backup Formats

### 1. SQL Format (Recommended)
- **File Extension**: `.sql`
- **Description**: Creates SQL INSERT statements for all data
- **Advantages**: 
  - Human-readable
  - Standard SQL format
  - Easy to edit if needed
  - Smaller file size
- **Best for**: Regular backups, data migration

### 2. JSON Format
- **File Extension**: `.json`
- **Description**: Exports all data as structured JSON
- **Advantages**:
  - Easy to read and parse
  - Cross-platform compatible
  - Good for data analysis
- **Best for**: Data export, analysis, debugging

## Quick Start

### Using the Simple Script

```bash
# Create a SQL backup (recommended)
./backup.sh backup

# Create a JSON backup
./backup.sh backup json

# List all available backups
./backup.sh list

# Show database statistics
./backup.sh stats

# Restore from a backup file
./backup.sh restore backups/backup_file.sql
```

### Using the Python Script Directly

```bash
# Create backups
python3 backup_database.py backup --format sql
python3 backup_database.py backup --format json

# Custom filename
python3 backup_database.py backup --format sql --filename my_backup.sql

# List and manage backups
python3 backup_database.py list
python3 backup_database.py stats

# Restore from backup
python3 backup_database.py restore --file backups/backup_file.sql
```

## Current Database Status

Your database contains:
- **11,340 Jeopardy questions** - Core trivia content
- **3 active game sessions** - Temporary game state data
- **2 turnover usage records** - User cooldown tracking

## Backup Examples

### Recent Backup Sizes
- **SQL Format**: ~3.1 MB (efficient, recommended)
- **JSON Format**: ~4.1 MB (more readable)

## Automatic Features

### Smart Fallback System
The backup system automatically tries PostgreSQL's `pg_dump` tool first, then falls back to a custom SQL generation method if there are version compatibility issues (which is currently happening in your environment).

### Data Safety
- All backups include data validation
- Restore operations can clear existing data safely
- Sequences are properly reset during restoration

## File Locations

- **Backup Directory**: `./backups/`
- **Backup Script**: `./backup_database.py`
- **Shell Wrapper**: `./backup.sh`

## Backup File Naming

Files are automatically named with timestamps:
- SQL: `discord_bot_backup_YYYYMMDD_HHMMSS.sql`
- JSON: `discord_bot_backup_YYYYMMDD_HHMMSS.json`

## Restoration Process

### SQL Backup Restoration
1. Automatically detects backup format
2. Clears existing data tables
3. Resets database sequences
4. Imports all backup data
5. Verifies successful restoration

### JSON Backup Restoration
1. Validates backup file format
2. Clears existing data
3. Recreates all records
4. Maintains data relationships

## Best Practices

### When to Backup
- **Before major updates** to your bot code
- **Before database migrations** or schema changes
- **Weekly** for regular data protection
- **Before scraping new data** to preserve existing content

### Backup Strategy
1. **Daily**: Quick SQL backups for recent changes
2. **Weekly**: Full JSON backup for comprehensive data export
3. **Before changes**: Always backup before modifying database structure

### Storage Recommendations
- Keep backups in multiple locations
- Consider cloud storage for important backups
- Rotate old backups to save space

## Troubleshooting

### Common Issues

**PostgreSQL Version Mismatch**
- System automatically falls back to custom SQL method
- No action needed - backups will still work correctly

**Large File Sizes**
- Your 11K+ questions create substantial backups
- SQL format is more efficient than JSON
- Consider compressing backups for long-term storage

**Restore Failures**
- Check backup file exists and is readable
- Ensure database connection is working
- Verify backup file format matches restore method

## Security Notes

- Backup files contain all your bot's data
- Store securely and limit access
- Backup files include user usage data (Discord user IDs)
- Consider encryption for sensitive data storage

## Integration with Bot Operations

The backup system works alongside your bot without interruption:
- Bot can run while backups are created
- Restoration requires brief downtime
- Game sessions are temporary and rebuild automatically
- Jeopardy questions and user data are fully preserved

## Performance

- **Backup Creation**: ~2-3 seconds for your dataset
- **File Sizes**: 3-4 MB typical range
- **Restoration**: ~3-5 seconds depending on format
- **Database Impact**: Minimal during backup operations