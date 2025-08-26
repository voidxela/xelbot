import asyncio
import os

import click
import discord
from dotenv import load_dotenv

from ..bot import DiscordBot
from ..database.tools import initialize_database
from ..utils.logger import get_logger

load_dotenv()

@click.command()
def run():
    """Run xelbot service."""
    logger = get_logger()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


async def start_bot():
    logger = get_logger()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        logger.error(
            "Please create a .env file with your bot token or set the environment variable."
        )
        return
    if not initialize_database():
        print("Error: Could not initialize database. Exiting.")
        exit(1)
    bot = DiscordBot()
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.close()
