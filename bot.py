import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.logger import setup_logger
from commands.basic import BasicCommands
from commands.jeopardy import JeopardyGame
from commands.turnover import TurnoverCommands

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger()

class DiscordBot(commands.Bot):
    """
    Main Discord bot class that handles initialization and command management.
    """
    
    def __init__(self):
        # Define bot intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message content access
        
        # Initialize bot with command prefix and intents
        super().__init__(
            command_prefix='!',  # Fallback prefix for text commands
            intents=intents,
            help_command=None  # We'll implement our own help command
        )
        
        # Bot configuration
        self.guild_id = os.getenv('GUILD_ID')
        if self.guild_id:
            self.guild_id = int(self.guild_id)
    
    async def setup_hook(self):
        """
        Called when the bot is starting up.
        This is where we add cogs and sync commands.
        """
        try:
            # Add command cogs
            await self.add_cog(BasicCommands(self))
            logger.info("Basic commands cog loaded successfully")
            
            await self.add_cog(JeopardyGame(self))
            logger.info("Jeopardy commands cog loaded successfully")
            
            await self.add_cog(TurnoverCommands(self))
            logger.info("Turnover commands cog loaded successfully")
            
            # Sync slash commands
            if self.guild_id:
                # Sync to specific guild for faster testing
                guild = discord.Object(id=self.guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Commands synced to guild {self.guild_id}")
            else:
                # Sync globally (takes up to 1 hour to propagate)
                await self.tree.sync()
                logger.info("Commands synced globally")
                
        except Exception as e:
            logger.error(f"Error during setup: {e}")
            raise
    
    async def on_ready(self):
        """
        Called when the bot has successfully connected to Discord.
        """
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/help for commands"
            )
        )
        
        # Log guild information
        for guild in self.guilds:
            logger.info(f'Connected to guild: {guild.name} (ID: {guild.id})')
            
        # Additional debugging info
        if len(self.guilds) == 0:
            logger.warning("Bot is not in any guilds. Make sure the bot is properly invited to a server.")
            logger.info("Bot invite URL should include 'bot' and 'applications.commands' scopes")
    
    async def on_guild_join(self, guild):
        """
        Called when the bot joins a new guild.
        """
        logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')
        
        # Try to send a welcome message to the system channel
        if guild.system_channel:
            try:
                embed = discord.Embed(
                    title="Hello! 👋",
                    description="Thanks for adding me to your server! Use `/help` to see available commands.",
                    color=discord.Color.blue()
                )
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"No permission to send message in {guild.name} system channel")
    
    async def on_guild_remove(self, guild):
        """
        Called when the bot is removed from a guild.
        """
        logger.info(f'Removed from guild: {guild.name} (ID: {guild.id})')
    
    async def on_command_error(self, ctx, error):
        """
        Global error handler for text commands.
        """
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        logger.error(f"Command error in {ctx.command}: {error}")
        
        # Send user-friendly error message
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(error)}",
            color=discord.Color.red()
        )
        
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            logger.error("Failed to send error message to user")
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """
        Global error handler for slash commands.
        """
        logger.error(f"Slash command error: {error}")
        
        # Create error embed
        embed = discord.Embed(
            title="❌ Command Error",
            description="Something went wrong while executing the command.",
            color=discord.Color.red()
        )
        
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            embed.description = f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, discord.app_commands.MissingPermissions):
            embed.description = "You don't have permission to use this command."
        else:
            embed.description = f"An unexpected error occurred: {str(error)}"
        
        # Send error response
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            logger.error("Failed to send error response to user")

async def main():
    """
    Main function to run the bot.
    """
    # Get bot token from environment
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your bot token or set the environment variable.")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token provided!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
