"""
Turnover command for the Discord bot.
Plays random football turnover clips from the database.
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import logging
import re
from datetime import datetime
import pytz
from database.models import get_session
import sqlite3
import psycopg2

logger = logging.getLogger(__name__)

class TurnoverCommands(commands.Cog):
    """
    Turnover commands for playing random football clips.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.turnover_urls = []
        self.load_turnover_urls()
    
    def load_turnover_urls(self):
        """
        Load turnover URLs from the CSV file.
        """
        try:
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'turnovers.csv')
            
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                content = file.read().strip()
                
                # Extract URLs from the format [URL]
                url_pattern = r'\[([^]]+)\]'
                urls = re.findall(url_pattern, content)
                
                # Filter out empty URLs and validate they're Discord CDN URLs
                self.turnover_urls = [
                    url.strip() for url in urls 
                    if url.strip() and 'cdn.discordapp.com' in url
                ]
                
                logger.info(f"Loaded {len(self.turnover_urls)} turnover URLs")
                
        except FileNotFoundError:
            logger.error("turnovers.csv file not found")
            self.turnover_urls = []
        except Exception as e:
            logger.error(f"Error loading turnover URLs: {e}")
            self.turnover_urls = []
    
    def get_random_turnover(self):
        """
        Get a random turnover URL from the loaded list.
        """
        if not self.turnover_urls:
            return None
        return random.choice(self.turnover_urls)
    
    def extract_game_info(self, url):
        """
        Extract game information from the URL filename.
        """
        try:
            # Extract filename from URL
            filename = url.split('/')[-1]
            # Remove file extension
            game_name = filename.replace('.mp4', '')
            
            # Parse the format: YEAR-WEEK-TEAM1-TEAM2
            parts = game_name.split('-')
            if len(parts) >= 4:
                year = parts[0]
                week = parts[1]
                teams = '-'.join(parts[2:])
                return f"{year} {week}: {teams}"
            else:
                return game_name
        except:
            return "Football Turnover"
    
    def get_eastern_date(self):
        """
        Get current date in Eastern time zone as YYYY-MM-DD string.
        """
        eastern = pytz.timezone('US/Eastern')
        now_eastern = datetime.now(eastern)
        return now_eastern.strftime('%Y-%m-%d')
    
    def can_use_turnover(self, user_id: int):
        """
        Check if user can use turnover command today.
        Returns (can_use: bool, usage_record: TurnoverUsage or None)
        """
        session = get_session()
        try:
            current_date = self.get_eastern_date()
            usage_record = session.query(TurnoverUsage).filter(TurnoverUsage.user_id == str(user_id)).first()
            
            if usage_record is None:
                # User has never used the command
                return True, None
            elif usage_record.last_used_date != current_date:
                # User last used it on a different date
                return True, usage_record
            else:
                # User already used it today
                return False, usage_record
        finally:
            session.close()
    
    def record_turnover_usage(self, user_id: int):
        """
        Record that user has used the turnover command today.
        """
        session = get_session()
        try:
            current_date = self.get_eastern_date()
            usage_record = session.query(TurnoverUsage).filter(TurnoverUsage.user_id == str(user_id)).first()
            
            if usage_record is not None:
                # Update existing record
                session.execute(
                    TurnoverUsage.__table__.update()
                    .where(TurnoverUsage.user_id == str(user_id))
                    .values(
                        last_used_date=current_date,
                        usage_count=TurnoverUsage.usage_count + 1,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Create new record
                usage_record = TurnoverUsage(
                    user_id=str(user_id),
                    last_used_date=current_date,
                    usage_count=1
                )
                session.add(usage_record)
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording turnover usage for user {user_id}: {e}")
            raise
        finally:
            session.close()
    
    @app_commands.command(name="turnover", description="Play a random football turnover clip (once per day)")
    async def turnover(self, interaction: discord.Interaction):
        """
        Play a random football turnover clip from the database.
        Limited to once per day per user (resets at midnight Eastern time).
        """
        try:
            user_id = interaction.user.id
            
            # Check cooldown first
            can_use, usage_record = self.can_use_turnover(user_id)
            if not can_use:
                eastern = pytz.timezone('US/Eastern')
                now_eastern = datetime.now(eastern)
                next_midnight = now_eastern.replace(hour=0, minute=0, second=0, microsecond=0)
                next_midnight = next_midnight.replace(day=next_midnight.day + 1)
                
                # Calculate hours until reset
                time_until_reset = next_midnight - now_eastern
                hours_remaining = int(time_until_reset.total_seconds() / 3600)
                minutes_remaining = int((time_until_reset.total_seconds() % 3600) / 60)
                
                embed = discord.Embed(
                    title="⏰ Daily Limit Reached",
                    description=f"You've already used your daily turnover clip!\n\nCome back in **{hours_remaining}h {minutes_remaining}m** for your next clip.",
                    color=discord.Color.yellow()
                )
                embed.add_field(
                    name="📊 Your Stats",
                    value=f"Total clips watched: {usage_record.usage_count if usage_record else 0}",
                    inline=False
                )
                embed.set_footer(text="Resets daily at midnight Eastern time")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if we have any turnover URLs loaded
            if not self.turnover_urls:
                embed = discord.Embed(
                    title="🏈 No Turnover Clips Available",
                    description="The turnover clip database is currently empty.\n\nThe original Discord CDN links have expired and need to be replaced with fresh video URLs.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="📝 How to Add Clips",
                    value="Upload new turnover videos and add their URLs to `data/turnovers.csv` in the format:\n`[URL]`",
                    inline=False
                )
                await interaction.response.send_message(embed=embed)
                return
            
            # Get a random turnover clip
            turnover_url = self.get_random_turnover()
            
            if not turnover_url:
                embed = discord.Embed(
                    title="❌ Error Getting Clip",
                    description="Could not retrieve a turnover clip at this time.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            # Record usage before sending clip
            self.record_turnover_usage(user_id)
            
            # Extract game information
            game_info = self.extract_game_info(turnover_url)
            
            # Create message content with game info and video URL
            # Discord will automatically embed the video
            content = f"🏈 **TURNOVER!** {game_info}\n{turnover_url}"
            
            # Send just the content with video URL for clean embedding
            await interaction.response.send_message(content=content)
            
            logger.info(f"Sent turnover clip to user {user_id}: {game_info}")
            
        except Exception as e:
            logger.error(f"Error in turnover command: {e}")
            
            embed = discord.Embed(
                title="❌ Command Error",
                description="An error occurred while processing the turnover command.",
                color=discord.Color.red()
            )
            
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass
    
    @app_commands.command(name="turnover_stats", description="Show statistics about the turnover clip database")
    async def turnover_stats(self, interaction: discord.Interaction):
        """
        Show statistics about the turnover clip database.
        """
        try:
            total_clips = len(self.turnover_urls)
            
            if total_clips == 0:
                embed = discord.Embed(
                    title="📊 Turnover Database Stats",
                    description="No turnover clips are currently loaded.",
                    color=discord.Color.yellow()
                )
            else:
                # Analyze clips by year if possible
                years = {}
                for url in self.turnover_urls:
                    try:
                        filename = url.split('/')[-1]
                        year = filename.split('-')[0]
                        if year.isdigit():
                            years[year] = years.get(year, 0) + 1
                    except:
                        continue
                
                embed = discord.Embed(
                    title="📊 Turnover Database Stats",
                    description=f"Database contains **{total_clips}** turnover clips",
                    color=discord.Color.blue()
                )
                
                if years:
                    year_list = sorted(years.items())
                    year_text = "\n".join([f"**{year}**: {count} clips" for year, count in year_list])
                    embed.add_field(
                        name="📅 Clips by Year",
                        value=year_text,
                        inline=False
                    )
                
                embed.add_field(
                    name="🎲 Random Selection",
                    value="Use `/turnover` to get a random clip!",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in turnover_stats command: {e}")
            
            embed = discord.Embed(
                title="❌ Command Error",
                description="An error occurred while getting turnover statistics.",
                color=discord.Color.red()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """
    Setup function for the cog.
    """
    await bot.add_cog(TurnoverCommands(bot))