#!/usr/bin/env python3
"""
🎬 Ultimate GIF Bot - Express Yourself with GIFs!
A feature-rich bot for GIF searches, reactions, and fun interactions
"""

import os
import json
import asyncio
import logging
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ChatAction
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel

from tenor_api import TenorAPI
from enhanced_features import EnhancedFeatures

# Load environment variables
load_dotenv()

# Rich console for beautiful logging
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("GIF_Bot")

class GIFBot:
    """Advanced Telegram GIF Bot with comprehensive features"""
    
    def __init__(self):
        self.tenor = TenorAPI()
        self.enhanced = EnhancedFeatures(self)
        self.user_stats = defaultdict(int)
        self.group_settings = defaultdict(lambda: {
            'passive_mode': False,
            'max_gifs': 3,
            'safe_mode': True
        })
        self.favorites = defaultdict(list)
        self.collections = defaultdict(dict)  # user_id: {collection_name: [gif_ids]}
        self.gif_labels = {}
        self.scheduled_tasks = {}
        self.challenges = {}
        
        # Passive mode triggers
        self.triggers = {
            'lol': ['funny', 'laugh', 'lmao'],
            'bruh': ['facepalm', 'really', 'seriously'],
            'sad': ['crying', 'tear', 'depression'],
            'happy': ['celebration', 'joy', 'party'],
            'angry': ['mad', 'rage', 'furious'],
            'love': ['heart', 'romance', 'cute'],
            'wow': ['amazed', 'surprised', 'mind blown'],
            'tired': ['sleepy', 'exhausted', 'yawn']
        }
        
        # Quick reactions mapping
        self.quick_reactions = {
            "😂": "laughing",
            "😍": "love",
            "😢": "crying",
            "😡": "angry",
            "🤯": "mind blown",
            "👍": "thumbs up",
            "👎": "thumbs down",
            "🎉": "celebration",
            "💩": "fail",
            "💋": "kiss",
            "🤗": "hug",
            "🤔": "thinking",
            "🤫": "shh",
            "🫠": "melting"
        }
        
        # Command reactions mapping
        self.command_reactions = {
            "start": "👋",
            "about": "ℹ️",
            "help": "📖",
            "s": "🔍",
            "r": "🎲",
            "fav_add": "⭐",
            "fav_list": "📋",
            "fav_remove": "🗑️",
            "newcollection": "📂",
            "addtocollection": "➕",
            "collections": "📚",
            "showcollection": "🖼️",
            "react": "⚡",
            "meme": "😂",
            "quote": "✨",
            "challenge": "🏆",
            "submitgif": "📤",
            "schedule": "⏰",
            "toggle_passive": "🤖",
            "setmax": "🔢",
            "safe": "🔒",
            "stats": "📊",
            "ranking": "🏆",
            "cancelchallenge": "❌"
        }
        
        self.load_data()
    
    def load_data(self):
        """Load persistent data from files"""
        try:
            if os.path.exists('bot_data.json'):
                with open('bot_data.json', 'r') as f:
                    data = json.load(f)
                    self.user_stats = defaultdict(int, data.get('user_stats', {}))
                    self.group_settings = defaultdict(
                        lambda: {'passive_mode': False, 'max_gifs': 3, 'safe_mode': True},
                        data.get('group_settings', {})
                    )
                    self.favorites = defaultdict(list, data.get('favorites', {}))
                    self.collections = defaultdict(dict, data.get('collections', {}))
                    self.gif_labels = data.get('gif_labels', {})
                    self.challenges = data.get('challenges', {})
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def save_data(self):
        """Save persistent data to file"""
        try:
            data = {
                'user_stats': dict(self.user_stats),
                'group_settings': dict(self.group_settings),
                'favorites': dict(self.favorites),
                'collections': dict(self.collections),
                'gif_labels': self.gif_labels,
                'challenges': self.challenges
            }
            with open('bot_data.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    async def react_to_command(self, update: Update, command: str):
        """React to command with appropriate emoji"""
        try:
            emoji = self.command_reactions.get(command, "👍")
            await update.message.reply_text(emoji)
        except Exception as e:
            logger.error(f"Error reacting to command: {e}")
    
    def log_command(self, update: Update, command: str, query: str = ""):
        """Log command usage with rich formatting"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Create user info
        user_info = f"{user.first_name}"
        if user.username:
            user_info += f" (@{user.username})"
        user_info += f" [ID: {user.id}]"
        
        # Create chat info
        chat_info = "Private Chat" if chat.type == "private" else f"Group: {chat.title}"
        
        # Create table for command log
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="bold cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Command:", f"/{command}")
        table.add_row("User:", user_info)
        table.add_row("Chat:", chat_info)
        if query:
            table.add_row("Query:", query)
        table.add_row("Time:", datetime.now().strftime("%H:%M:%S"))
        
        console.print(Panel(table, title="[green]Bot Activity[/green]", 
                          border_style="green"))
    
    def _get_reply_id(self, update: Update) -> Optional[int]:
        """Get message ID to reply to if user is replying to someone"""
        if update.message and update.message.reply_to_message:
            return update.message.reply_to_message.message_id
        return None
    
    async def _send_gif(
        self, 
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        gif_url: str, 
        caption: str,
        reply_id: Optional[int] = None
    ):
        """Send GIF with proper reply handling"""
        await context.bot.send_animation(
            chat_id=chat_id,
            animation=gif_url,
            caption=caption,
            reply_to_message_id=reply_id
        )
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message with features overview"""
        await self.react_to_command(update, "start")
        self.log_command(update, "start")
        
        welcome_text = """
👋 Welcome to the Ultimate GIF Bot!

I'm here to make your chats more fun with GIFs! Here's what I can do:

🔍 Find GIFs:
/s [query] - Search for GIFs
/s [query] [n] - Get multiple GIFs (max 5)
/r [query] - Random GIF from query

⭐ Favorites:
/fav_add - Save GIFs to favorites (reply to GIF)
/fav_list - Show your favorites
/fav_remove [number] - Remove favorite

⚡ Express Yourself:
/react [emoji] - Quick reaction GIFs
/meme [top]|[bottom] - Create GIF memes
/quote [topic] - Inspirational quote + GIF

🎮 Fun & Games:
/challenge [theme] [seconds] - Start a GIF challenge
/submitgif - Submit for current challenge
/stats - Your GIF usage stats
/ranking - Group leaderboard

⚙️ Settings (Admins):
/toggle_passive - Auto-react to keywords
/setmax [n] - Set default GIF count
/safe - Toggle safe mode

📆 Schedule Fun:
/schedule [HH:MM] [query] - Schedule GIF posts

👉 Add me to your groups to spread the fun! 
Just search for me in Telegram and click "Add to Group"

Use /help for detailed command info!
        """
        
        await update.message.reply_text(welcome_text)
        
        # Send welcome GIF
        try:
            welcome_gif = await self.tenor.search_gif("hello", limit=1)
            if welcome_gif:
                await update.message.reply_animation(
                    welcome_gif[0],
                    caption="Let's get started! What GIF adventure shall we begin today?"
                )
        except Exception as e:
            logger.error(f"Error sending welcome GIF: {e}")
    
    async def group_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when bot is added to a group"""
        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    await update.message.reply_text(
                        "👋 Hey everyone! Thanks for adding me to the group!\n\n"
                        "I'm the Ultimate GIF Bot - here to make your chats more fun with GIFs!\n\n"
                        "Here's what I can do:\n"
                        "- Search GIFs with /s [query]\n"
                        "- Save favorites with /fav_add\n"
                        "- Start challenges with /challenge\n"
                        "- And much more!\n\n"
                        "Use /help to see all commands. Let's have some fun! 🎉"
                    )
                    # Send welcome GIF
                    try:
                        welcome_gif = await self.tenor.search_gif("group hello", limit=1)
                        if welcome_gif:
                            await update.message.reply_animation(welcome_gif[0])
                    except Exception:
                        pass
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show information about the bot creator"""
        await self.react_to_command(update, "about")
        self.log_command(update, "about")
        
        about_text = """
👋 Hey there!

I'm Suppy 🧑‍💻 — the creator of this bot! 

💖 This bot was created just for fun as a personal project. 
No business stuff, just pure GIF joy! 🎉

🎯 Why I made this?  
I wanted a cool way to share laughs and reactions with friends! 
Life's too short for boring chats, right? 😄

📌 Important Note:  
I might not be actively maintaining this bot forever, 
but as long as it's running, feel free to enjoy it! 🚀

🙏 Big Thanks!  
Seriously, thanks for checking out my creation! 
If you have a moment, share a GIF that makes you smile with /s happy 😊

👉 My username: @Suppyee
        """
        
        await update.message.reply_text(about_text)
        
        # Send a thank you GIF
        try:
            thanks_gif = await self.tenor.search_gif("thank you", limit=1)
            if thanks_gif:
                await update.message.reply_animation(
                    thanks_gif[0],
                    caption="Thanks for being awesome!"
                )
        except Exception as e:
            logger.error(f"Error sending thanks GIF: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detailed help with interactive buttons"""
        await self.react_to_command(update, "help")
        self.log_command(update, "help")
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search & Find", callback_data="help_search")],
            [InlineKeyboardButton("⭐ Favorites & Collections", callback_data="help_favorites")],
            [InlineKeyboardButton("🎮 Fun & Games", callback_data="help_fun")],
            [InlineKeyboardButton("⚡ Quick Reactions", callback_data="help_reactions")],
            [InlineKeyboardButton("⚙️ Settings & Admin", callback_data="help_admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_text = "🌈 GIF Bot Help Center\n\nChoose a category to learn more:"
        
        await update.message.reply_text(help_text, reply_markup=reply_markup)
    
    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help category selections"""
        query = update.callback_query
        await query.answer()
        
        help_texts = {
            "help_search": """
🔍 Search & Find GIFs

/s [query] - Find the perfect GIF
Example: /s dancing cat

/s [query] [number] - Get multiple GIFs
Example: /s funny dogs 3
Max: 5 GIFs per search

/r [query] - Get a random GIF surprise!
Example: /r celebration

/quote [topic] - Get motivational quote + matching GIF
Example: /quote success
            """,
            
            "help_favorites": """
⭐ Favorites & Collections

/fav_add - Reply to any GIF to save it
/fav_list - View all your saved GIFs
/fav_remove [number] - Remove from favorites

📂 Collections:
/newcollection [name] - Create a new collection
Example: /newcollection Cats

/addtocollection [name] - Add to collection (reply to GIF)
Example: /addtocollection Cats

/collections - List your collections
/showcollection [name] - Show GIFs in a collection
            """,
            
            "help_fun": """
🎮 Fun & Games

/challenge [theme] [seconds] - Start a GIF challenge!
Example: /challenge Summer 300 (5 minutes)

/submitgif - Submit GIF for current challenge
Reply to a GIF with this command

/stats - View your GIF usage stats
/ranking - Top 10 GIF users in this group

/schedule [HH:MM] [query] - Schedule GIF posts
Example: /schedule 14:30 celebration
            """,
            
            "help_reactions": """
⚡ Quick Reactions

/react [emoji] - Send reaction GIF instantly!
Available emojis:
😂 - Laughing reaction
😍 - Love reaction
😢 - Sad reaction
😡 - Angry reaction
🤯 - Mind blown
👍 - Thumbs up
👎 - Thumbs down
🎉 - Celebration
💩 - Fail reaction
💋 - Kiss
🤗 - Hug
🤔 - Thinking
🤫 - Shhh
🫠 - Melting

Example: /react 😂
            """,
            
            "help_admin": """
⚙️ Settings & Admin

/toggle_passive - Enable/disable auto-reactions
I react to keywords like "lol", "bruh", "sad"

/setmax [n] - Set default GIF count (1-5)
Example: /setmax 2

/safe - Toggle safe mode (filter NSFW content)

/cancelchallenge - Cancel current challenge

Note: Group admin commands work in groups only
            """
        }
        
        text = help_texts.get(query.data, "Oops! Help topic not found 😅 Try another one!")
        back_button = InlineKeyboardButton("🔙 Back to Main Help", callback_data="help_main")
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button]]))
    
    async def search_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main GIF search command"""
        await self.react_to_command(update, "s")
        
        if not context.args:
            await update.message.reply_text("Oops! You forgot to tell me what to search for!\nTry: /s cats dancing")
            return
        
        # Parse arguments
        query_parts = context.args[:-1]
        count = 1
        
        # Check if last argument is a number
        if context.args and context.args[-1].isdigit():
            count = min(int(context.args[-1]), 5)  # Max 5 GIFs
            if not query_parts:  # If only number provided
                await update.message.reply_text("Try: /s [search query] [number]\nExample: /s funny cats 2")
                return
        else:
            query_parts = context.args
            count = self.group_settings[str(update.effective_chat.id)]['max_gifs']
        
        query = ' '.join(query_parts)
        self.log_command(update, "search", f"{query} (count: {count})")
        
        # Show typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        try:
            # Search for GIFs
            safe_mode = self.group_settings[str(update.effective_chat.id)]['safe_mode']
            
            # For single GIF, get 10 and pick randomly
            if count == 1:
                gifs = await self.tenor.search_gif(query, limit=10, safe_search=safe_mode)
                if gifs:
                    gif_url = random.choice(gifs)
                    gifs = [gif_url]  # Convert to list for consistency
                else:
                    gifs = []
            else:
                gifs = await self.tenor.search_gif(query, limit=count, safe_search=safe_mode)
            
            if not gifs:
                await update.message.reply_text(f'No GIFs found for "{query}" 😢\nTry something else?')
                return
            
            # Get reply target if user is replying to someone
            reply_id = self._get_reply_id(update)
            chat_id = update.effective_chat.id
            
            # Send GIFs
            for i, gif_url in enumerate(gifs):
                caption = f"Result {i+1} for {query}" if len(gifs) > 1 else f"{query}"
                await self._send_gif(context, chat_id, gif_url, caption, reply_id)
            
            # Update stats
            self.user_stats[str(update.effective_user.id)] += len(gifs)
            self.save_data()
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("Oops! Something went wrong. Try again later?")
    
    async def random_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a random GIF from query"""
        await self.react_to_command(update, "r")
        
        if not context.args:
            await update.message.reply_text("Tell me what to find randomly!\nExample: /r cats being weird")
            return
        
        query = ' '.join(context.args)
        self.log_command(update, "random", query)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        try:
            safe_mode = self.group_settings[str(update.effective_chat.id)]['safe_mode']
            gifs = await self.tenor.search_gif(query, limit=20, safe_search=safe_mode)
            
            if not gifs:
                await update.message.reply_text(f'No GIFs found for "{query}" 😢')
                return
            
            # Get reply target if user is replying to someone
            reply_id = self._get_reply_id(update)
            chat_id = update.effective_chat.id
            
            # Send random GIF from results
            random_gif = random.choice(gifs)
            await self._send_gif(
                context,
                chat_id,
                random_gif, 
                f"Random GIF for {query}!",
                reply_id
            )
            
            self.user_stats[str(update.effective_user.id)] += 1
            self.save_data()
            
        except Exception as e:
            logger.error(f"Random GIF error: {e}")
            await update.message.reply_text("Oops! Something went wrong. Try again?")
    
    async def add_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add GIF to favorites"""
        await self.react_to_command(update, "fav_add")
        
        if not update.message.reply_to_message or not update.message.reply_to_message.animation:
            await update.message.reply_text("Reply to a GIF with /fav_add to save it!")
            return
        
        user_id = str(update.effective_user.id)
        gif_file_id = update.message.reply_to_message.animation.file_id
        
        if gif_file_id in self.favorites[user_id]:
            await update.message.reply_text("This GIF is already in your favorites!")
            return
        
        self.favorites[user_id].append(gif_file_id)
        self.save_data()
        
        await update.message.reply_text(
            f"GIF saved to favorites! ({len(self.favorites[user_id])} total)\n"
            f"See them with /fav_list"
        )
        
        self.log_command(update, "fav_add")
    
    async def list_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List user's favorite GIFs"""
        await self.react_to_command(update, "fav_list")
        user_id = str(update.effective_user.id)
        user_favs = self.favorites[user_id]
        
        if not user_favs:
            await update.message.reply_text("You don't have any favorite GIFs yet!\nReply to a GIF with /fav_add to save it.")
            return
        
        self.log_command(update, "fav_list")
        
        # Get reply target if user is replying to someone
        reply_id = self._get_reply_id(update)
        chat_id = update.effective_chat.id
        
        # Send favorite GIFs
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⭐ Your Favorite GIFs! ({len(user_favs)} total)",
            reply_to_message_id=reply_id
        )
        
        for i, gif_file_id in enumerate(user_favs[:10]):  # Show max 10
            try:
                await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=gif_file_id,
                    caption=f"Favorite #{i+1}",
                    reply_to_message_id=reply_id
                )
            except Exception as e:
                logger.error(f"Error sending favorite GIF: {e}")
                # If GIF is no longer accessible, remove it
                if gif_file_id in self.favorites[user_id]:
                    self.favorites[user_id].remove(gif_file_id)
        
        if len(user_favs) > 10:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"... and {len(user_favs) - 10} more!",
                reply_to_message_id=reply_id
            )
        
        self.save_data()
    
    async def remove_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove GIF from favorites"""
        await self.react_to_command(update, "fav_remove")
        
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /fav_remove [number]\nExample: /fav_remove 2")
            return
        
        user_id = str(update.effective_user.id)
        index = int(context.args[0]) - 1
        
        if index < 0 or index >= len(self.favorites[user_id]):
            await update.message.reply_text("Invalid favorite number! Check with /fav_list")
            return
        
        removed = self.favorites[user_id].pop(index)
        self.save_data()
        
        await update.message.reply_text(f"Favorite #{index+1} removed!")
        self.log_command(update, "fav_remove")
    
    async def handle_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle favorite commands"""
        if not context.args:
            await self.list_favorites(update, context)
            return
        
        action = context.args[0].lower()
        
        if action == "add":
            await self.add_favorite(update, context)
        elif action == "list":
            await self.list_favorites(update, context)
        elif action == "remove":
            context.args = context.args[1:]
            await self.remove_favorite(update, context)
        else:
            await update.message.reply_text(
                "Favorites Commands:\n"
                "/fav_add - Reply to a GIF to save it\n"
                "/fav_list - Show your favorites\n"
                "/fav_remove [number] - Remove favorite"
            )
    
    async def toggle_passive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle passive mode (admin only)"""
        if not await self.is_admin(update, context):
            return
        
        await self.react_to_command(update, "toggle_passive")
        chat_id = str(update.effective_chat.id)
        current = self.group_settings[chat_id]['passive_mode']
        self.group_settings[chat_id]['passive_mode'] = not current
        self.save_data()
        
        status = "enabled" if not current else "disabled"
        emoji = "🤖" if not current else "😴"
        await update.message.reply_text(
            f"{emoji} Passive mode {status}!\n"
            f"I will {'now' if not current else 'no longer'} react to keywords"
        )
        
        self.log_command(update, "toggle_passive", status)
    
    async def set_max_gifs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set maximum GIFs per search (admin only)"""
        if not await self.is_admin(update, context):
            return
        
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /setmax [1-5]\nExample: /setmax 3")
            return
        
        max_count = min(int(context.args[0]), 5)
        chat_id = str(update.effective_chat.id)
        self.group_settings[chat_id]['max_gifs'] = max_count
        self.save_data()
        
        await update.message.reply_text(f"Default GIF count set to {max_count}")
        self.log_command(update, "setmax", str(max_count))
    
    async def toggle_safe_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle safe mode (admin only)"""
        if not await self.is_admin(update, context):
            return
        
        await self.react_to_command(update, "safe")
        chat_id = str(update.effective_chat.id)
        current = self.group_settings[chat_id]['safe_mode']
        self.group_settings[chat_id]['safe_mode'] = not current
        self.save_data()
        
        status = "enabled" if not current else "disabled"
        emoji = "🔒" if not current else "🔓"
        await update.message.reply_text(f"{emoji} Safe mode {status}!")
        self.log_command(update, "safe_mode", status)
    
    async def show_user_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        await self.react_to_command(update, "stats")
        user_id = str(update.effective_user.id)
        user_count = self.user_stats.get(user_id, 0)
        fav_count = len(self.favorites.get(user_id, []))
        
        # Determine user rank
        if user_count >= 5000:
            rank = "GIF God 🦸"
        elif user_count >= 2000:
            rank = "GIF Legend ✨"
        elif user_count >= 500:
            rank = "GIF Master 🏆"
        elif user_count >= 100:
            rank = "GIF Explorer 🚀"
        else:
            rank = "GIF Newbie 🌱"
        
        # Add fun comment based on usage
        if user_count == 0:
            comment = "New here? Try /s hello to get started!"
        elif user_count < 10:
            comment = "Just warming up! Keep those GIFs coming!"
        elif user_count < 30:
            comment = "You're getting the hang of this!"
        else:
            comment = "You're a GIF legend!"
        
        await update.message.reply_text(
            f"📊 Your GIF Stats:\n\n"
            f"🎬 GIFs requested: {user_count}\n"
            f"⭐ Favorites saved: {fav_count}\n"
            f"🏆 Rank: {rank}\n\n"
            f"{comment}"
        )
        
        self.log_command(update, "stats")
    
    async def show_group_ranking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show top 10 users in current group"""
        await self.react_to_command(update, "ranking")
        
        # Only available in groups
        if update.effective_chat.type == "private":
            await update.message.reply_text("This command only works in groups!")
            return
        
        # Get all users who have used the bot in this group
        # Note: This is a simplified approach - in a real bot you'd track per-group stats
        group_users = {}
        
        # This is a placeholder - in a real implementation you'd need to track per-group usage
        # For now, we'll show global top users
        sorted_users = sorted(self.user_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not sorted_users:
            await update.message.reply_text("No stats available yet!")
            return
        
        response = "🏆 Top GIF Users:\n\n"
        for i, (user_id, count) in enumerate(sorted_users):
            try:
                user = await context.bot.get_chat_member(update.effective_chat.id, int(user_id))
                name = user.user.first_name
                response += f"{i+1}. {name}: {count} GIFs\n"
            except:
                response += f"{i+1}. User {user_id}: {count} GIFs\n"
        
        await update.message.reply_text(response)
        self.log_command(update, "ranking")
    
    async def handle_passive_triggers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle passive mode keyword triggers"""
        if not update.message or not update.message.text:
            return
        
        chat_id = str(update.effective_chat.id)
        if not self.group_settings[chat_id]['passive_mode']:
            return
        
        message_text = update.message.text.lower()
        
        for trigger, queries in self.triggers.items():
            if trigger in message_text:
                # Send a random GIF from trigger queries
                query = random.choice(queries)
                
                try:
                    safe_mode = self.group_settings[chat_id]['safe_mode']
                    gifs = await self.tenor.search_gif(query, limit=5, safe_search=safe_mode)
                    
                    if gifs:
                        gif = random.choice(gifs)
                        await update.message.reply_animation(
                            gif,
                            caption=f"{trigger}"
                        )
                        
                        self.user_stats[str(update.effective_user.id)] += 1
                        self.save_data()
                    break
                except Exception as e:
                    logger.error(f"Passive trigger error: {e}")
    
    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin"""
        if update.effective_chat.type == "private":
            return True
        
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
            is_admin = member.status in ['administrator', 'creator']
            
            if not is_admin:
                await update.message.reply_text("This command is for admins only!")
            
            return is_admin
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return False
    
    async def quick_react(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a reaction GIF based on emoji"""
        await self.react_to_command(update, "react")
        
        if not context.args:
            emoji_list = "\n".join([f"{emoji}" for emoji in self.quick_reactions.keys()])
            await update.message.reply_text(
                "Quick Reactions!\n\n"
                "Send a reaction GIF with an emoji!\n\n"
                "Usage: /react [emoji]\n\n"
                "Available emojis:\n" + emoji_list + "\n\n"
                "Example: /react 😂"
            )
            return
        
        emoji = context.args[0]
        if emoji not in self.quick_reactions:
            await update.message.reply_text(
                "Emoji not supported! Try one of these:\n" + 
                " ".join(self.quick_reactions.keys()) + 
                "\n\nSee all with /react"
            )
            return
        
        query = self.quick_reactions[emoji]
        self.log_command(update, "react", emoji)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        try:
            safe_mode = self.group_settings[str(update.effective_chat.id)]['safe_mode']
            gifs = await self.tenor.search_gif(query, limit=10, safe_search=safe_mode)
            
            if not gifs:
                await update.message.reply_text(f"Couldn't find a reaction GIF for {emoji}")
                return
            
            # Get reply target if user is replying to someone
            reply_id = self._get_reply_id(update)
            chat_id = update.effective_chat.id
            
            # Send random GIF from results
            random_gif = random.choice(gifs)
            await self._send_gif(
                context,
                chat_id,
                random_gif, 
                f"{emoji}",
                reply_id
            )
            
            self.user_stats[str(update.effective_user.id)] += 1
            self.save_data()
            
        except Exception as e:
            logger.error(f"Quick react error: {e}")
            await update.message.reply_text("Oops! Something went wrong. Try again?")
    
    async def start_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a new GIF challenge with custom duration"""
        await self.react_to_command(update, "challenge")
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /challenge [theme] [seconds]\nExample: /challenge Summer 300 (5 minutes)")
            return
        
        # Default time is 300 seconds (5 minutes)
        seconds = 300
        theme = args[0]
        
        if len(args) >= 2 and args[1].isdigit():
            seconds = int(args[1])
            # Limit to between 30 seconds and 24 hours
            seconds = max(30, min(seconds, 24 * 3600))
        
        chat_id = update.effective_chat.id
        
        # Create challenge
        self.challenges[str(chat_id)] = {
            "theme": theme,
            "creator": update.effective_user.id,
            "participants": {},
            "end_time": datetime.now() + timedelta(seconds=seconds)
        }
        self.save_data()
        
        duration = timedelta(seconds=seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"
        
        await update.message.reply_text(
            f"🏆 NEW GIF CHALLENGE!\n\n"
            f"Theme: {theme}\n"
            f"Duration: {time_str}\n"
            f"Submit your GIFs with /submitgif\n"
            f"Ends at: {self.challenges[str(chat_id)]['end_time'].strftime('%H:%M:%S')}"
        )
        self.log_command(update, "challenge", f"{theme} {seconds}s")
        
        # Schedule challenge end
        context.job_queue.run_once(
            self.end_challenge,
            seconds,
            chat_id=chat_id,
            data={"chat_id": chat_id}
        )
    
    async def end_challenge(self, context: ContextTypes.DEFAULT_TYPE):
        """End a challenge and announce results"""
        job = context.job
        chat_id = str(job.chat_id)
        
        if chat_id not in self.challenges:
            return
        
        challenge = self.challenges[chat_id]
        
        if not challenge["participants"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏆 Challenge '{challenge['theme']}' ended with no submissions 😢"
            )
            del self.challenges[chat_id]
            self.save_data()
            return
        
        # Select a random winner
        winner_id = random.choice(list(challenge["participants"].keys()))
        winner_gif = challenge["participants"][winner_id]
        
        try:
            winner = await context.bot.get_chat_member(chat_id, int(winner_id))
            winner_name = winner.user.first_name
        except:
            winner_name = f"User {winner_id}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🏆 Challenge '{challenge['theme']}' ended!\n\n"
                 f"🎉 Winner: {winner_name}!\n"
                 f"Thanks to all participants!"
        )
        
        # Send winner's GIF
        await context.bot.send_animation(
            chat_id=chat_id,
            animation=winner_gif,
            caption=f"🏆 Winning GIF by {winner_name}"
        )
        
        # Cleanup
        del self.challenges[chat_id]
        self.save_data()
    
    async def cancel_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel an ongoing challenge"""
        await self.react_to_command(update, "cancelchallenge")
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.challenges:
            await update.message.reply_text("No active challenge to cancel!")
            return
        
        # Only challenge creator or admin can cancel
        if (update.effective_user.id != self.challenges[chat_id]["creator"] and 
            not await self.is_admin(update, context)):
            await update.message.reply_text("Only the challenge creator or admin can cancel!")
            return
        
        # Cancel scheduled job
        for job in context.job_queue.jobs():
            if job.data and job.data.get("chat_id") == chat_id:
                job.schedule_removal()
        
        del self.challenges[chat_id]
        self.save_data()
        await update.message.reply_text("✅ Challenge canceled!")
        self.log_command(update, "cancelchallenge")
    
    async def submit_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit a GIF for the current challenge"""
        await self.react_to_command(update, "submitgif")
        chat_id = str(update.effective_chat.id)
        
        if chat_id not in self.challenges:
            await update.message.reply_text("No active challenge! Start one with /challenge")
            return
        
        if not update.message.reply_to_message or not update.message.reply_to_message.animation:
            await update.message.reply_text("Reply to a GIF with /submitgif to enter the challenge!")
            return
        
        challenge = self.challenges[chat_id]
        user_id = update.effective_user.id
        
        # Add submission
        challenge["participants"][str(user_id)] = update.message.reply_to_message.animation.file_id
        self.save_data()
        
        await update.message.reply_text(f"🎉 Submission received for '{challenge['theme']}' challenge!")
        self.log_command(update, "submitgif", challenge['theme'])
    
    async def schedule_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Schedule a GIF to be sent at a specific time"""
        await self.react_to_command(update, "schedule")
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /schedule [HH:MM] [search query]\n"
                "Example: /schedule 15:30 birthday party\n\n"
                "Times are in your current timezone"
            )
            return
        
        time_str = context.args[0]
        query = ' '.join(context.args[1:])
        
        # Validate time format
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", time_str):
            await update.message.reply_text("Invalid time format! Use HH:MM (24-hour format)\nExample: 14:30")
            return
        
        self.log_command(update, "schedule", f"{time_str} {query}")
        
        try:
            # Calculate delay in seconds
            now = datetime.now()
            scheduled_time = datetime.strptime(time_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            
            # If time has already passed today, schedule for tomorrow
            if scheduled_time < now:
                scheduled_time += timedelta(days=1)
            
            delay = (scheduled_time - now).total_seconds()
            
            # Schedule the job
            context.job_queue.run_once(
                callback=self.send_scheduled_gif,
                when=delay,
                chat_id=update.effective_chat.id,
                data={"query": query, "user_id": update.effective_user.id},
                name=f"{update.effective_user.id}_{query}_{scheduled_time.timestamp()}"
            )
            
            await update.message.reply_text(
                f"⏰ Scheduled! I'll send a GIF for '{query}' at {scheduled_time.strftime('%H:%M')}!"
            )
        except Exception as e:
            logger.error(f"Scheduling error: {e}")
            await update.message.reply_text("Couldn't schedule that. Try again?")
    
    async def send_scheduled_gif(self, context: ContextTypes.DEFAULT_TYPE):
        """Callback for scheduled GIF job"""
        job = context.job
        query = job.data["query"]
        chat_id = job.chat_id
        
        try:
            safe_mode = self.group_settings.get(str(chat_id), {}).get('safe_mode', True)
            gifs = await self.tenor.search_gif(query, limit=1, safe_search=safe_mode)
            
            if gifs:
                await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=gifs[0],
                    caption=f"⏰ Scheduled GIF for '{query}'"
                )
                # Update user stats
                self.user_stats[str(job.data["user_id"])] += 1
                self.save_data()
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ Couldn't find a GIF for '{query}'."
                )
        except Exception as e:
            logger.error(f"Error sending scheduled GIF: {e}")

    async def inspirational_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send an inspirational quote with a matching GIF"""
        await self.react_to_command(update, "quote")
        topic = ' '.join(context.args) if context.args else "inspiration"
        self.log_command(update, "quote", topic)

        try:
            import requests
            # Get a random inspirational quote
            response = requests.get("https://api.quotable.io/random")
            if response.status_code == 200:
                data = response.json()
                quote_text = f'"{data["content"]}" — {data["author"]}'
            else:
                quote_text = "Believe you can and you're halfway there."

            # Get a GIF matching the topic
            safe_mode = self.group_settings[str(update.effective_chat.id)]['safe_mode']
            gifs = await self.tenor.search_gif(topic, limit=5, safe_search=safe_mode)

            if gifs:
                gif_url = random.choice(gifs)
                await update.message.reply_animation(gif_url, caption=quote_text)
                self.user_stats[str(update.effective_user.id)] += 1
                self.save_data()
            else:
                await update.message.reply_text(quote_text)
        except Exception as e:
            logger.error(f"Quote command error: {e}")
            await update.message.reply_text("Couldn't fetch an inspirational quote right now.")
            
def main():
    """Main function to run the bot"""
    # Check for required environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    tenor_key = os.getenv("TENOR_API_KEY")
    
    if not token or not tenor_key:
        console.print("[red]❌ Missing environment variables![/red]")
        console.print("Please set TELEGRAM_BOT_TOKEN and TENOR_API_KEY in .env file")
        return
    
    # Initialize bot
    bot = GIFBot()
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("about", bot.about))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CallbackQueryHandler(bot.help_callback))
    
    # GIF commands
    application.add_handler(CommandHandler("s", bot.search_gif))
    application.add_handler(CommandHandler("r", bot.random_gif))
    
    # Favorites
    application.add_handler(CommandHandler("fav", bot.handle_favorites))
    application.add_handler(CommandHandler("fav_add", bot.add_favorite))
    application.add_handler(CommandHandler("fav_list", bot.list_favorites))
    application.add_handler(CommandHandler("fav_remove", bot.remove_favorite))
    
    # Reactions
    application.add_handler(CommandHandler("react", bot.quick_react))
    
    # Fun features
    application.add_handler(CommandHandler("quote", bot.inspirational_quote))
    application.add_handler(CommandHandler("challenge", bot.start_challenge))
    application.add_handler(CommandHandler("submitgif", bot.submit_gif))
    application.add_handler(CommandHandler("cancelchallenge", bot.cancel_challenge))
    application.add_handler(CommandHandler("schedule", bot.schedule_gif))
    
    # Stats
    application.add_handler(CommandHandler("stats", bot.show_user_stats))
    application.add_handler(CommandHandler("ranking", bot.show_group_ranking))
    
    # Settings
    application.add_handler(CommandHandler(["toggle", "toggle_passive"], bot.toggle_passive))
    application.add_handler(CommandHandler("setmax", bot.set_max_gifs))
    application.add_handler(CommandHandler("safe", bot.toggle_safe_mode))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_passive_triggers))
    
    # Group welcome handler
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot.group_welcome))
    
    # Add enhanced features
    bot.enhanced.add_handlers(application)
    
    # Start bot
    console.print(Panel.fit(
        "[green]🎬 Ultimate GIF Bot Starting...[/green]\n"
        "[yellow]Ready to spread GIF joy! ✨[/yellow]",
        border_style="green"
    ))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()