# Discord Bot

A feature-rich Discord bot built with discord.py that provides utility commands and can be easily extended with additional functionality.

## Features

- **Slash Commands**: Modern Discord slash command support
- **Basic Utility Commands**: Ping, help, info, random number generation, user information
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Detailed logging system with file and console output
- **Extensible**: Easy to add new commands and features
- **Production Ready**: Proper token management and security practices

## Available Commands

- `/ping` - Check bot latency and response time
- `/help` - Display all available commands
- `/info` - Show detailed bot information and statistics
- `/random [maximum]` - Generate a random number (1 to maximum, default 100)
- `/userinfo [user]` - Display information about a user

## Setup Instructions

### 1. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token (you'll need this for step 3)

### 2. Install Dependencies

```bash
pip install discord.py python-dotenv psutil
