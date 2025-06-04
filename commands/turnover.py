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
    
    @app_commands.command(name="turnover", description="Play a random football turnover clip")
    async def turnover(self, interaction: discord.Interaction):
        """
        Play a random football turnover clip from the database.
        """
        try:
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
            
            # Extract game information
            game_info = self.extract_game_info(turnover_url)
            
            # Create message content with game info and video URL
            # Discord will automatically embed the video
            content = f"🏈 **TURNOVER!** {game_info}\n{turnover_url}"
            
            # Send just the content with video URL for clean embedding
            await interaction.response.send_message(content=content)
            
            logger.info(f"Sent turnover clip: {game_info}")
            
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