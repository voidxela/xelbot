"""
Jeopardy game commands for the Discord bot.
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import re
from typing import Optional
from database.models import JeopardyQuestion, GameSession, get_session
from utils.logger import get_logger

logger = get_logger("jeopardy")

class NewGameView(discord.ui.View):
    """View with button to start a new Jeopardy game."""
    
    def __init__(self, jeopardy_cog):
        super().__init__(timeout=300)
        self.jeopardy_cog = jeopardy_cog
        self.message = None  # Will be set after the message is sent
    
    async def on_timeout(self):
        """Called when the view times out. Remove the view entirely."""
        # Simply remove the view (buttons) from the message when it times out
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=None)
        except Exception:
            # Silently fail if message can't be edited (e.g., deleted, no permission)
            pass
    
    @discord.ui.button(label='🎯 Start New Game', style=discord.ButtonStyle.primary)
    async def start_new_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start a new Jeopardy game when button is clicked."""
        # Check if there's already an active game in this channel
        channel_id = interaction.channel_id
        if channel_id in self.jeopardy_cog.active_games:
            embed = discord.Embed(
                title="🎯 Game Already Active",
                description="There's already a Jeopardy game running in this channel! Answer the current question first.",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get a random question
        question = await self.jeopardy_cog.get_random_question()
        
        if not question:
            embed = discord.Embed(
                title="❌ No Questions Available",
                description="No Jeopardy questions found in the database. Please wait while we gather more questions.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create the clue embed with year information
        embed = self.jeopardy_cog.create_question_embed(question)
        
        await interaction.response.send_message(embed=embed)
        
        # Store game data
        self.jeopardy_cog.active_games[channel_id] = {
            'question': question,
            'start_time': discord.utils.utcnow()
        }
        
        # Save to database with proper error handling
        session = get_session()
        try:
            # First, clean up any existing sessions for this channel
            session.query(GameSession).filter_by(
                channel_id=str(channel_id)
            ).delete()
            session.commit()
            
            # Create new session
            game_session = GameSession(
                channel_id=str(channel_id),
                question_id=question.id,
                is_active=True,
                timeout_seconds=30
            )
            session.add(game_session)
            session.commit()
            logger.info(f"Created new game session for channel {channel_id}")
        except Exception as e:
            logger.error(f"Error saving game session: {e}")
            session.rollback()
            # Continue without database session - game still works in memory
        finally:
            session.close()
        
        # Start timeout task
        if interaction.channel_id is not None:
            timeout_task = asyncio.create_task(
                self.jeopardy_cog.timeout_game(interaction.channel_id, interaction.channel, question)
            )
            self.jeopardy_cog.active_games[channel_id]['timeout_task'] = timeout_task

class JeopardyGame(commands.Cog):
    """
    Jeopardy game commands and functionality.
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # channel_id -> game_data
    
    def create_question_embed(self, question: JeopardyQuestion, title: str = "🎯 Jeopardy Clue", 
                             include_time_limit: bool = True, color: discord.Color = discord.Color.blue()) -> discord.Embed:
        """
        Create a standardized embed for displaying Jeopardy questions with year information.
        """
        embed = discord.Embed(
            title=title,
            description=question.clue,
            color=color
        )
        embed.add_field(
            name="Category",
            value=question.category,
            inline=True
        )
        if question.value is not None:
            embed.add_field(
                name="Value",
                value=f"${question.value:,}",
                inline=True
            )
        
        # Add year if air_date is available
        air_date_value = getattr(question, 'air_date', None)
        if air_date_value and str(air_date_value).strip():
            try:
                # Extract year from air_date (format: YYYY-MM-DD)
                year = str(air_date_value).split('-')[0]
                embed.add_field(
                    name="Year",
                    value=year,
                    inline=True
                )
            except:
                pass  # If air_date format is unexpected, skip the year display
        
        if include_time_limit:
            embed.add_field(
                name="Time Limit",
                value="30 seconds",
                inline=True
            )
            embed.set_footer(text="Type your answer in chat! Remember to phrase as a question.")
        
        return embed
        
    def normalize_answer(self, answer: str) -> str:
        """
        Normalize an answer for comparison.
        Removes common prefixes, punctuation, parentheses content, and converts to lowercase.
        """
        # Remove "What is", "Who is", etc.
        answer = re.sub(r'^(what|who|where|when|why|how)\s+(is|are|was|were)\s+', '', answer.lower())
        
        # Remove content in parentheses (optional parts)
        answer = re.sub(r'\([^)]*\)', '', answer)
        
        # Remove articles at the beginning
        answer = re.sub(r'^(a|an|the)\s+', '', answer)
        
        # Remove common geographical descriptors and prefixes
        answer = re.sub(r'\b(peninsula|island|city|state|country|province|territory)\b', '', answer)
        
        # Normalize hyphens, dashes, and spaces
        answer = re.sub(r'[-–—]', ' ', answer)
        
        # Remove punctuation but preserve spaces
        answer = re.sub(r'[^\w\s]', '', answer)
        
        # Normalize multiple spaces to single space
        answer = re.sub(r'\s+', ' ', answer).strip()
        
        return answer
    
    def check_answer(self, user_answer: str, correct_answer: str) -> bool:
        """
        Check if the user's answer matches the correct answer.
        Uses flexible matching to account for variations, geographical descriptions,
        parenthetical content, and hyphenation differences.
        """
        user_normalized = self.normalize_answer(user_answer)
        correct_normalized = self.normalize_answer(correct_answer)
        
        # Exact match after normalization
        if user_normalized == correct_normalized:
            return True
        
        # Split into words for more flexible matching
        correct_words = correct_normalized.split()
        user_words = user_normalized.split()
        
        # Special case: if user gives a single word that's contained in the correct answer
        # This handles cases like "wellington" for "wellington new zealand"
        if len(user_words) == 1 and len(correct_words) > 1:
            user_word = user_words[0]
            if len(user_word) >= 4:  # Must be a significant word
                for correct_word in correct_words:
                    if len(correct_word) >= 4 and (user_word == correct_word or 
                                                  user_word in correct_word or 
                                                  correct_word in user_word):
                        return True
        
        # Special case: if correct answer has a single key word that user provides
        # This handles cases like "lincoln" for "abraham lincoln"
        if len(correct_words) > 1 and len(user_words) >= 1:
            # Find the most significant word in the correct answer (usually the last name or main term)
            significant_correct_words = [word for word in correct_words if len(word) >= 4]
            user_significant_words = [word for word in user_words if len(word) >= 3]
            
            # If user provides any significant word that matches
            for user_word in user_significant_words:
                for correct_word in significant_correct_words:
                    if user_word == correct_word or user_word in correct_word or correct_word in user_word:
                        # Additional check: make sure it's not a common word
                        common_words = ['with', 'from', 'that', 'this', 'they', 'have', 'been', 'were', 
                                      'answer', 'question', 'word', 'name', 'place', 'thing', 'person']
                        if correct_word not in common_words:
                            return True
        
        # Handle single word answers with substring matching
        if len(correct_words) == 1 and len(user_words) == 1:
            correct_word = correct_words[0]
            user_word = user_words[0]
            # Check if they contain each other (handles partial matches)
            if correct_word in user_word or user_word in correct_word:
                return True
        
        # For multi-word answers, use flexible word matching
        if len(correct_words) > 1 and len(user_words) > 1:
            # Count how many significant words match
            matches = 0
            common_words = ['answer', 'question', 'word', 'name', 'place', 'thing', 'person']
            
            for correct_word in correct_words:
                # Skip very short words and common words
                if len(correct_word) < 3 or correct_word in common_words:
                    continue
                    
                # Check if this word appears in user answer (exact or partial)
                word_found = False
                for user_word in user_words:
                    if len(user_word) < 3:
                        continue
                    # Exact match or one contains the other
                    if correct_word == user_word or correct_word in user_word or user_word in correct_word:
                        word_found = True
                        break
                
                if word_found:
                    matches += 1
            
            # Need at least 60% of significant words to match, and at least one significant word
            significant_words = sum(1 for word in correct_words if len(word) >= 3 and word not in common_words)
            if significant_words > 0 and matches > 0:
                match_ratio = matches / significant_words
                return match_ratio >= 0.6
        
        # Fallback: check if user answer contains most of the correct answer
        # This handles cases where word order might be different
        if len(correct_normalized) > 0 and len(user_normalized) > 0:
            # Special case: if correct answer is much shorter due to normalization,
            # check if the correct answer is fully contained in user answer
            if len(correct_normalized) < len(user_normalized) * 0.5:
                # Check if correct answer is a substring of user answer
                if correct_normalized in user_normalized:
                    return True
            
            # More sophisticated similarity check - both directions
            correct_in_user = sum(1 for char in correct_normalized if char in user_normalized)
            user_in_correct = sum(1 for char in user_normalized if char in correct_normalized)
            
            # Calculate bidirectional similarity
            forward_sim = correct_in_user / len(correct_normalized)
            backward_sim = user_in_correct / len(user_normalized)
            
            # Only match if both directions show high similarity and answers are reasonably similar in length
            length_ratio = min(len(user_normalized), len(correct_normalized)) / max(len(user_normalized), len(correct_normalized))
            
            return forward_sim >= 0.9 and backward_sim >= 0.9 and length_ratio >= 0.7
        
        return False
    
    async def get_random_question(self) -> Optional[JeopardyQuestion]:
        """
        Get a random question from the database.
        """
        session = get_session()
        try:
            # Get total count
            total = session.query(JeopardyQuestion).count()
            if total == 0:
                return None
            
            # Get random offset
            offset = random.randint(0, total - 1)
            question = session.query(JeopardyQuestion).offset(offset).first()
            return question
        except Exception as e:
            logger.error(f"Error getting random question: {e}")
            return None
        finally:
            session.close()
    
    async def end_game(self, channel_id: int, winner: Optional[discord.Member] = None, 
                      correct_answer: Optional[str] = None):
        """
        End the active game in a channel.
        """
        if channel_id in self.active_games:
            game_data = self.active_games[channel_id]
            
            # Cancel the timeout task
            if 'timeout_task' in game_data:
                game_data['timeout_task'].cancel()
            
            # Remove from active games
            del self.active_games[channel_id]
            
            # Update database
            db_session_obj = get_session()
            try:
                # Update the is_active field using SQLAlchemy update
                db_session_obj.query(GameSession).filter_by(
                    channel_id=str(channel_id)
                ).update({"is_active": False})
                db_session_obj.commit()
            except Exception as e:
                logger.error(f"Error updating game session: {e}")
            finally:
                db_session_obj.close()
    
    async def timeout_game(self, channel_id: int, channel, question: JeopardyQuestion):
        """
        Handle game timeout.
        """
        try:
            await asyncio.sleep(30)  # Default timeout
            
            # Check if game is still active
            if channel_id not in self.active_games:
                return
            
            # Try to send timeout message
            try:
                # Get fresh channel reference to avoid stale objects
                fresh_channel = self.bot.get_channel(channel_id)
                if fresh_channel is None:
                    # Try to fetch the channel if not in cache
                    fresh_channel = await self.bot.fetch_channel(channel_id)
                
                if fresh_channel:
                    embed = self.create_question_embed(
                        question, 
                        title="⏰ Time's Up!", 
                        include_time_limit=False, 
                        color=discord.Color.red()
                    )
                    embed.description = f"The correct answer was: **{question.answer}**"
                    
                    # Create view with new game button
                    view = NewGameView(self)
                    
                    message = await fresh_channel.send(embed=embed, view=view)
                    view.message = message
                    logger.info(f"Timeout message sent for game in channel {channel_id}")
                else:
                    logger.warning(f"Could not get channel {channel_id} for timeout message")
                    
            except discord.Forbidden:
                logger.warning(f"No permission to send timeout message in channel {channel_id}")
            except discord.NotFound:
                logger.warning(f"Channel {channel_id} not found for timeout message")
            except discord.HTTPException as e:
                logger.error(f"HTTP error sending timeout message to channel {channel_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending timeout message to channel {channel_id}: {e}")
            
            # Always end the game after timeout, regardless of message send success
            await self.end_game(channel_id, correct_answer=str(question.answer))
                
        except asyncio.CancelledError:
            # Game was ended before timeout - this is normal
            logger.debug(f"Timeout task cancelled for channel {channel_id}")
        except Exception as e:
            logger.error(f"Error in timeout task for channel {channel_id}: {e}")
            # Ensure game is cleaned up even if there's an error
            try:
                await self.end_game(channel_id, correct_answer=str(question.answer))
            except Exception as cleanup_error:
                logger.error(f"Error during timeout cleanup for channel {channel_id}: {cleanup_error}")
                # Force remove from active games as last resort
                if channel_id in self.active_games:
                    del self.active_games[channel_id]
    
    @app_commands.command(name="clue", description="Start a Jeopardy game with a random clue")
    async def clue(self, interaction: discord.Interaction):
        """
        Start a new Jeopardy game with a random question.
        """
        channel_id = interaction.channel_id
        
        # Check if there's already an active game in this channel
        if channel_id in self.active_games:
            embed = discord.Embed(
                title="🎯 Game Already Active",
                description="There's already a Jeopardy game running in this channel! Answer the current question first.",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get a random question
        question = await self.get_random_question()
        
        if not question:
            embed = discord.Embed(
                title="❌ No Questions Available",
                description="No Jeopardy questions found in the database. Please wait while we gather more questions.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create the clue embed with year information
        embed = self.create_question_embed(question)
        
        await interaction.response.send_message(embed=embed)
        
        # Store game data
        self.active_games[channel_id] = {
            'question': question,
            'start_time': discord.utils.utcnow()
        }
        
        # Save to database with proper error handling
        session = get_session()
        try:
            # First, clean up any existing sessions for this channel
            session.query(GameSession).filter_by(
                channel_id=str(channel_id)
            ).delete()
            session.commit()
            
            # Create new session
            game_session = GameSession(
                channel_id=str(channel_id),
                question_id=question.id,
                is_active=True,
                timeout_seconds=30
            )
            session.add(game_session)
            session.commit()
            logger.info(f"Created new game session for channel {channel_id}")
        except Exception as e:
            logger.error(f"Error saving game session: {e}")
            session.rollback()
            # Continue without database session - game still works in memory
        finally:
            session.close()
        
        # Start timeout task
        if interaction.channel_id is not None:
            timeout_task = asyncio.create_task(
                self.timeout_game(interaction.channel_id, interaction.channel, question)
            )
            self.active_games[channel_id]['timeout_task'] = timeout_task
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listen for answers to active Jeopardy games.
        """
        # Ignore bot messages
        if message.author.bot:
            return
        
        channel_id = message.channel.id
        
        # Check if there's an active game in this channel
        if channel_id not in self.active_games:
            return
        
        game_data = self.active_games[channel_id]
        question = game_data['question']
        
        # Check if the answer is correct
        user_answer = message.content.strip()
        if self.check_answer(user_answer, question.answer):
            # Correct answer!
            embed = discord.Embed(
                title="🎉 Correct!",
                description=f"**{message.author.display_name}** got it right!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Answer",
                value=question.answer,
                inline=False
            )
            embed.add_field(
                name="Category",
                value=question.category,
                inline=True
            )
            if question.value:
                embed.add_field(
                    name="Value",
                    value=f"${question.value:,}",
                    inline=True
                )
            
            # Calculate time taken
            time_taken = (discord.utils.utcnow() - game_data['start_time']).total_seconds()
            embed.add_field(
                name="Time",
                value=f"{time_taken:.1f} seconds",
                inline=True
            )
            
            if question.air_date:
                embed.set_footer(text=f"Originally aired: {question.air_date}")
            
            # Create view with new game button
            view = NewGameView(self)
            
            sent_message = await message.channel.send(embed=embed, view=view)
            view.message = sent_message
            await self.end_game(channel_id, winner=message.author, correct_answer=question.answer)
    
    @app_commands.command(name="endgame", description="End the current Jeopardy game (moderators only)")
    async def end_current_game(self, interaction: discord.Interaction):
        """
        End the current game in the channel (for moderators).
        """
        # Check if user has manage messages permission
        if (interaction.guild is None or 
            not isinstance(interaction.user, discord.Member) or 
            not interaction.user.guild_permissions.manage_messages):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need 'Manage Messages' permission to end games.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        channel_id = interaction.channel_id
        
        if channel_id not in self.active_games:
            embed = discord.Embed(
                title="ℹ️ No Active Game",
                description="There's no active Jeopardy game in this channel.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game_data = self.active_games[channel_id]
        question = game_data['question']
        
        embed = discord.Embed(
            title="🛑 Game Ended",
            description="The game has been ended by a moderator.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Correct Answer",
            value=question.answer,
            inline=False
        )
        embed.add_field(
            name="Category",
            value=question.category,
            inline=True
        )
        
        # Create view with new game button
        view = NewGameView(self)
        
        await interaction.response.send_message(embed=embed, view=view)
        if interaction.channel_id is not None:
            await self.end_game(interaction.channel_id, correct_answer=str(question.answer))
    
    @app_commands.command(name="jeopardy_stats", description="Show Jeopardy database statistics")
    async def jeopardy_stats(self, interaction: discord.Interaction):
        """
        Show statistics about the Jeopardy question database.
        """
        session = get_session()
        try:
            total_questions = session.query(JeopardyQuestion).count()
            
            if total_questions == 0:
                embed = discord.Embed(
                    title="📊 Jeopardy Statistics",
                    description="No questions in database yet. Please wait while we gather data.",
                    color=discord.Color.blue()
                )
            else:
                # Get category count
                categories = session.query(JeopardyQuestion.category).distinct().count()
                
                # Get latest air date
                latest = session.query(JeopardyQuestion).filter(
                    JeopardyQuestion.air_date.isnot(None)
                ).order_by(JeopardyQuestion.air_date.desc()).first()
                
                embed = discord.Embed(
                    title="📊 Jeopardy Statistics",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Total Questions",
                    value=f"{total_questions:,}",
                    inline=True
                )
                embed.add_field(
                    name="Categories",
                    value=f"{categories:,}",
                    inline=True
                )
                if latest is not None and latest.air_date is not None:
                    embed.add_field(
                        name="Latest Episode",
                        value=str(latest.air_date),
                        inline=True
                    )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Could not retrieve statistics.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        finally:
            session.close()

async def setup(bot):
    """
    Setup function for the cog.
    """
    await bot.add_cog(JeopardyGame(bot))