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

### Run with Docker

1. **Set up environment variable:**
```bash
cp .env.example .env
# Edit .env with your actual values

```

### Install as executable

1. **Build and install the executable:**
```bash
pip install .
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your actual values
```

3. **Populate the database:**
```bash
xelbot db populate
```

4. **Run the bot:**
```bash
xelbot run
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

**Local PostgreSQL**
```bash
# Install PostgreSQL on your system
# Create a database
createdb xelbot

# Update DATABASE_URL in .env:
DATABASE_URL=postgresql://username:password@localhost:5432/xelbot
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values.

### 4. Invite Bot to Your Server

1. In Discord Developer Portal, go to OAuth2 > URL Generator
2. Select scopes: `bot` and `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
4. Use the generated URL to invite your bot

## Troubleshooting

### Database Management

**Check database status:**
```bash
xelbot db info
```

**Populate database questions:**
```bash
xelbot db populate
```

**Reset database:**
```bash
# Warning: This deletes all data
python -c "from xelbot.database.models import *; create_tables()"
```

### Adding New Commands

1. Create a new file in the `commands/` directory
2. Follow the existing pattern with proper error handling
3. Add the cog to the bot in `bot.py`
4. Update this README with command documentation

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Ensure all environment variables are properly configured
4. Verify database connectivity and table creation
