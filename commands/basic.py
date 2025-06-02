import time
import platform
import psutil
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BasicCommands(commands.Cog):
    """
    Basic utility commands for the Discord bot.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
    
    @app_commands.command(name="ping", description="Check the bot's latency and response time")
    async def ping(self, interaction: discord.Interaction):
        """
        Ping command to check bot latency and response time.
        """
        start_time = time.time()
        
        # Create initial embed
        embed = discord.Embed(
            title="🏓 Pinging...",
            color=discord.Color.yellow()
        )
        
        # Send initial response
        await interaction.response.send_message(embed=embed)
        
        # Calculate response time
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        # Update embed with results
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🌐 API Latency",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        embed.add_field(
            name="⚡ Response Time",
            value=f"{round(response_time)}ms",
            inline=True
        )
        
        # Edit the original response
        await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="info", description="Display information about the bot")
    async def info(self, interaction: discord.Interaction):
        """
        Display comprehensive bot information.
        """
        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime_seconds = uptime_seconds % 60
        
        uptime_str = f"{uptime_hours}h {uptime_minutes}m {uptime_seconds}s"
        
        # Get system information
        memory_usage = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Create info embed
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Bot info
        embed.add_field(
            name="📊 Statistics",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Users:** {len(self.bot.users)}\n"
                  f"**Latency:** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # System info
        embed.add_field(
            name="💻 System",
            value=f"**Python:** {platform.python_version()}\n"
                  f"**OS:** {platform.system()}\n"
                  f"**CPU:** {cpu_usage}%\n"
                  f"**Memory:** {memory_usage.percent}%",
            inline=True
        )
        
        # Runtime info
        embed.add_field(
            name="⏱️ Runtime",
            value=f"**Uptime:** {uptime_str}\n"
                  f"**Discord.py:** {discord.__version__}",
            inline=True
        )
        
        # Add bot avatar as thumbnail
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="help", description="Display available commands and their descriptions")
    async def help(self, interaction: discord.Interaction):
        """
        Display help information with all available commands.
        """
        embed = discord.Embed(
            title="📚 Command Help",
            description="Here are all the available commands:",
            color=discord.Color.blue()
        )
        
        # Basic Commands
        embed.add_field(
            name="🏓 /ping",
            value="Check the bot's latency and response time",
            inline=False
        )
        
        embed.add_field(
            name="🤖 /info",
            value="Display detailed information about the bot",
            inline=False
        )
        
        embed.add_field(
            name="📚 /help",
            value="Show this help message",
            inline=False
        )
        
        embed.add_field(
            name="🎲 /random",
            value="Generate a random number between 1 and specified maximum",
            inline=False
        )
        
        embed.add_field(
            name="👤 /userinfo",
            value="Display information about a user (yourself or mentioned user)",
            inline=False
        )
        
        embed.set_footer(text="Use the commands by typing them in chat!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="random", description="Generate a random number")
    @app_commands.describe(maximum="Maximum number (default: 100)")
    async def random_number(self, interaction: discord.Interaction, maximum: Optional[int] = 100):
        """
        Generate a random number between 1 and the specified maximum.
        """
        if maximum < 1:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Maximum number must be at least 1!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if maximum > 1000000:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Maximum number cannot exceed 1,000,000!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        import random
        result = random.randint(1, maximum)
        
        embed = discord.Embed(
            title="🎲 Random Number",
            description=f"**Result:** {result}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Range",
            value=f"1 - {maximum}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Display information about a user")
    @app_commands.describe(user="The user to get information about (leave empty for yourself)")
    async def userinfo(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """
        Display information about a specified user or the command invoker.
        """
        # Default to the user who invoked the command
        target_user = user or interaction.user
        
        # Create embed
        embed = discord.Embed(
            title=f"👤 User Information - {target_user.display_name}",
            color=target_user.color if hasattr(target_user, 'color') and target_user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Basic user info
        embed.add_field(
            name="📝 Basic Info",
            value=f"**Username:** {target_user.name}\n"
                  f"**Display Name:** {target_user.display_name}\n"
                  f"**ID:** {target_user.id}\n"
                  f"**Bot:** {'Yes' if target_user.bot else 'No'}",
            inline=True
        )
        
        # Account dates
        created_at = target_user.created_at.strftime("%B %d, %Y")
        embed.add_field(
            name="📅 Account Created",
            value=created_at,
            inline=True
        )
        
        # Server-specific info (if it's a member)
        if isinstance(target_user, discord.Member):
            joined_at = target_user.joined_at.strftime("%B %d, %Y") if target_user.joined_at else "Unknown"
            embed.add_field(
                name="📅 Joined Server",
                value=joined_at,
                inline=True
            )
            
            # Roles (excluding @everyone)
            roles = [role.mention for role in target_user.roles[1:]]
            if roles:
                roles_text = ", ".join(roles) if len(roles) <= 10 else f"{', '.join(roles[:10])}... (+{len(roles) - 10} more)"
                embed.add_field(
                    name=f"🎭 Roles ({len(roles)})",
                    value=roles_text,
                    inline=False
                )
        
        # Set user avatar as thumbnail
        if target_user.avatar:
            embed.set_thumbnail(url=target_user.avatar.url)
        
        # Set footer
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """
    Setup function for the cog.
    """
    await bot.add_cog(BasicCommands(bot))
