# Discord Bot

A feature-rich Discord bot built with discord.py that provides utility commands and can be easily extended with additional functionality.

## Features

- **Slash Commands**: Modern Discord slash command support
- **Jeopardy Game**: Interactive Jeopardy game with authentic questions from actual TV episodes
- **Basic Utility Commands**: Ping, help, info, random number generation, user information
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Detailed logging system with file and console output
- **Database Integration**: PostgreSQL database for persistent storage
- **Extensible**: Easy to add new commands and features
- **Production Ready**: Proper token management and security practices

## Available Commands

### Basic Commands
- `/ping` - Check bot latency and response time
- `/help` - Display all available commands
- `/info` - Show detailed bot information and statistics
- `/random [maximum]` - Generate a random number (1 to maximum, default 100)
- `/userinfo [user]` - Display information about a user

### Jeopardy Game Commands
- `/clue` - Start a new Jeopardy game with a random question from actual TV episodes
- `/end_game` - End the current game in the channel (moderators only)
- `/jeopardy_stats` - Show statistics about the question database

## Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Discord bot token

### Installation

1. **Clone the repository and install dependencies:**
   ```bash
   # Dependencies are automatically installed via pyproject.toml
   # Or install manually:
   pip install discord.py python-dotenv psutil sqlalchemy psycopg2-binary beautifulsoup4 requests trafilatura asyncpg
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Initialize the database:**
   ```bash
   python init_database.py
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Detailed Setup Instructions

### 1. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. **Important:** Under "Privileged Gateway Intents", enable:
   - Message Content Intent (required for game responses)
   - Server Members Intent (optional, for user info commands)
5. Copy the bot token (keep this secure!)

### 2. Set Up Database

**Option A: Local PostgreSQL**
```bash
# Install PostgreSQL on your system
# Create a database
createdb discord_bot

# Update DATABASE_URL in .env:
DATABASE_URL=postgresql://username:password@localhost:5432/discord_bot
```

**Option B: Cloud Database (Recommended for deployment)**
- Use services like Railway, Supabase, or AWS RDS
- Copy the connection string to your .env file

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
# Required
DISCORD_TOKEN=your_actual_bot_token_here
DATABASE_URL=your_database_connection_string

# Optional (with defaults)
LOG_LEVEL=INFO
JEOPARDY_TIMEOUT=30
SCRAPER_DELAY=2.0
DEBUG_MODE=False
```

### 4. Database Setup

Initialize the database tables:
```bash
python init_database.py
```

**Optional:** Populate with real Jeopardy questions (takes time):
```bash
python populate_database.py
```

### 5. Invite Bot to Your Server

1. In Discord Developer Portal, go to OAuth2 > URL Generator
2. Select scopes: `bot` and `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
4. Use the generated URL to invite your bot

## Configuration Details

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Your bot's token from Discord Developer Portal | `MTA1234567890.GH1234.abcdef...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/dbname` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `JEOPARDY_TIMEOUT` | `30` | Seconds to wait for game answers |
| `SCRAPER_DELAY` | `2.0` | Delay between web requests when scraping |
| `DEBUG_MODE` | `False` | Enable development features |

## Troubleshooting

### Common Issues

**Bot not responding to commands:**
- Ensure Message Content Intent is enabled in Discord Developer Portal
- Check that the bot has proper permissions in your server
- Verify the bot token is correct in your .env file

**Database connection errors:**
- Verify DATABASE_URL format: `postgresql://username:password@host:port/database`
- Ensure PostgreSQL is running and accessible
- Run `python init_database.py` to create tables

**"Duplicate key violation" errors in Jeopardy games:**
- This happens when a game session already exists in a channel
- Use `/end_game` command to clear stuck sessions
- Or restart the bot to clear all active sessions

**Web scraping errors:**
- Check internet connection
- The scraper includes delays to be respectful to servers
- Some games may not be available or have parsing issues

### Database Management

**Reset database:**
```bash
# Warning: This deletes all data
python -c "from database.models import *; create_tables()"
```

**Check database status:**
```bash
python -c "from database.models import get_session; print('Database connected!' if get_session() else 'Connection failed')"
```

### Performance Optimization

- The bot includes automatic command syncing on startup
- Database sessions are properly managed with connection pooling
- Logging is configured to rotate files automatically
- Memory usage is optimized with proper cleanup of game sessions

## Deployment

### Replit Deployment

This bot is designed to run on Replit with minimal configuration:

1. **Fork/Import the project** to your Replit account
2. **Add Secrets** in the Replit interface:
   - `DISCORD_TOKEN`: Your bot token
   - `DATABASE_URL`: Your PostgreSQL connection string
3. **Run the bot** using the Run button or `python bot.py`

The bot will automatically:
- Install all required dependencies
- Initialize database tables if they don't exist
- Start and maintain the connection

### Other Hosting Platforms

**Railway:**
```bash
# Connect your GitHub repository
# Add environment variables in Railway dashboard
# Deploy automatically on git push
```

**Heroku:**
```bash
# Add Procfile: worker: python bot.py
# Add Config Vars for environment variables
# Deploy via GitHub or Heroku CLI
```

**VPS/Cloud Server:**
```bash
# Install Python 3.11+, PostgreSQL
# Clone repository and install dependencies
# Set up systemd service for auto-restart
# Configure reverse proxy if needed
```

## Project Structure

```
discord-bot/
├── bot.py                 # Main bot file
├── commands/              # Command modules
│   ├── basic.py          # Basic utility commands
│   └── jeopardy.py       # Jeopardy game commands
├── database/              # Database models and config
│   └── models.py         # SQLAlchemy models
├── scraper/               # Web scraping functionality
│   └── jeopardy_scraper.py # J-Archive scraper
├── utils/                 # Utility functions
│   └── logger.py         # Logging configuration
├── init_database.py      # Database initialization
├── populate_database.py  # Question database population
├── .env.example          # Environment variables template
├── pyproject.toml        # Python dependencies
└── README.md             # This file
```

## Database Schema

**jeopardy_questions table:**
- `id`: Primary key
- `category`: Question category
- `clue`: The question/clue text
- `answer`: Correct answer
- `value`: Dollar value (100-2000)
- `air_date`: Original broadcast date
- `round_type`: Jeopardy/Double Jeopardy/Final
- `show_number`: Episode number

**game_sessions table:**
- `id`: Primary key
- `channel_id`: Discord channel ID
- `question_id`: Current question
- `is_active`: Game status
- `timeout_seconds`: Answer timeout
- `created_at`: Session start time

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** with proper testing
4. **Follow the existing code style** and add logging where appropriate
5. **Submit a pull request** with a clear description

### Adding New Commands

1. Create a new file in the `commands/` directory
2. Follow the existing pattern with proper error handling
3. Add the cog to the bot in `bot.py`
4. Update this README with command documentation

### Code Style Guidelines

- Use type hints for function parameters and return values
- Add comprehensive docstrings for all functions and classes
- Include proper error handling with user-friendly messages
- Follow PEP 8 style guidelines
- Use the provided logger for all logging operations

## License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Ensure all environment variables are properly configured
4. Verify database connectivity and table creation

## Acknowledgments

- Built with discord.py library
- Jeopardy questions sourced from J-Archive.com
- Uses SQLAlchemy for robust database operations
- Implements modern Discord slash command interface
