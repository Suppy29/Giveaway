#!/usr/bin/env python3
"""
🎬 Advanced Telegram GIF Bot
A feature-rich bot for GIF searches, favorites, and interactive features
"""

import os
import json
import asyncio
import logging
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
        self.gif_labels = {}
        self.scheduled_tasks = {}
        
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
                    self.gif_labels = data.get('gif_labels', {})
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def save_data(self):
        """Save persistent data to file"""
        try:
            data = {
                'user_stats': dict(self.user_stats),
                'group_settings': dict(self.group_settings),
                'favorites': dict(self.favorites),
                'gif_labels': self.gif_labels
            }
            with open('bot_data.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
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
        
        table.add_row("🎬 Command:", f"/{command}")
        table.add_row("👤 User:", user_info)
        table.add_row("💬 Chat:", chat_info)
        if query:
            table.add_row("🔍 Query:", query)
        table.add_row("⏰ Time:", datetime.now().strftime("%H:%M:%S"))
        
        console.print(Panel(table, title="[bold green]Bot Activity[/bold green]", 
                          border_style="green"))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message with features overview"""
        self.log_command(update, "start")
        
        welcome_text = """
🎬 **Welcome to Advanced GIF Bot!** 🎬

I'm here to make your chats more fun with GIFs! Here's what I can do:

🔍 **Search Commands:**
/s [query] - Search for GIFs
/s [query] [n] - Get multiple GIFs (max 5)
/r [query] - Random GIF from query
/trending - Top trending GIFs

⭐ **Favorites:**
/fav add [reply to GIF] - Save to favorites
/fav list - Show your favorites
/gif [keyword] - Quick access to labeled GIFs

⚙️ **Settings (Admin only):**
/toggle passive - Auto-react to keywords
/setmax [n] - Set default GIF count
/safe - Toggle safe mode

📊 **Fun Stuff:**
/stats - Your GIF usage stats
/quote [query] - Quote + matching GIF
/schedule [time] [query] - Schedule GIF posts

Type /help for detailed command info!
        """
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detailed help with interactive buttons"""
        self.log_command(update, "help")
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search Commands", callback_data="help_search")],
            [InlineKeyboardButton("⭐ Favorites", callback_data="help_favorites")],
            [InlineKeyboardButton("⚙️ Admin Settings", callback_data="help_admin")],
            [InlineKeyboardButton("📊 Fun Features", callback_data="help_fun")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_text = """
🎬 **GIF Bot Help Center** 🎬

Choose a category to learn more:
        """
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help category selections"""
        query = update.callback_query
        await query.answer()
        
        help_texts = {
            "help_search": """
🔍 **Search Commands**

/s [query] - Search for the best GIF
• Example: `/s dancing cat`

/s [query] [number] - Get multiple GIFs
• Example: `/s funny dogs 3`
• Max: 5 GIFs per search

/r [query] - Get a random GIF
• Example: `/r celebration`

/trending - See what's trending now
            """,
            
            "help_favorites": """
⭐ **Favorites System**

/fav add - Reply to any GIF to save it
/fav list - View all your saved GIFs
/fav remove [number] - Remove from favorites

**GIF Labeling:**
/label [keyword] - Label the last GIF you posted
/gif [keyword] - Quick access to labeled GIFs

**Examples:**
Reply to a GIF: `/fav add`
Quick access: `/gif happy`
            """,
            
            "help_admin": """
⚙️ **Admin Commands**

/toggle passive - Enable/disable auto-reactions
• Bot reacts to keywords like "lol", "bruh", "sad"

/setmax [n] - Set default GIF count (1-5)
• Example: `/setmax 2`

/safe - Toggle safe mode (filter NSFW content)

**Note:** Only group admins can use these commands
            """,
            
            "help_fun": """
📊 **Fun Features**

/stats - View your GIF usage statistics
/quote [query] - Get motivational quote + GIF
/schedule [time] [query] - Schedule GIF posts
• Example: `/schedule 14:30 celebration`

**Passive Mode Triggers:**
When enabled, I react to:
• "lol" → funny GIFs
• "bruh" → facepalm GIFs  
• "sad" → crying GIFs
• And many more!
            """
        }
        
        await query.edit_message_text(
            help_texts.get(query.data, "Help not found"),
            parse_mode='Markdown'
        )
    
    async def search_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main GIF search command"""
        if not context.args:
            await update.message.reply_text("🔍 **Usage:** `/s [search query]` or `/s [query] [number]`", 
                                          parse_mode='Markdown')
            return
        
        # Parse arguments
        query_parts = context.args[:-1]
        count = 1
        
        # Check if last argument is a number
        if context.args[-1].isdigit():
            count = min(int(context.args[-1]), 5)  # Max 5 GIFs
            if not query_parts:  # If only number provided
                await update.message.reply_text("🔍 **Usage:** `/s [search query] [number]`", 
                                              parse_mode='Markdown')
                return
        else:
            query_parts = context.args
            count = self.group_settings[str(update.effective_chat.id)]['max_gifs']
        
        query = ' '.join(query_parts)
        self.log_command(update, "search", f"{query} (count: {count})")
        
        # Show typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, 
                                         action=ChatAction.TYPING)
        
        # Search for GIFs
        safe_mode = self.group_settings[str(update.effective_chat.id)]['safe_mode']
        gifs = await self.tenor.search_gif(query, limit=count, safe_search=safe_mode)
        
        if not gifs:
            await update.message.reply_text(f'🚫 No GIFs found for "{query}" 😢')
            return
        
        # Send GIFs
        for i, gif_url in enumerate(gifs):
            caption = f"🎬 **Result {i+1}** for *{query}*" if len(gifs) > 1 else f"🎬 *{query}*"
            await update.message.reply_animation(gif_url, caption=caption, parse_mode='Markdown')
        
        # Update stats
        self.user_stats[str(update.effective_user.id)] += len(gifs)
        self.save_data()
    
    async def random_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a random GIF from query"""
        if not context.args:
            await update.message.reply_text("🎲 **Usage:** `/r [search query]`", parse_mode='Markdown')
            return
        
        query = ' '.join(context.args)
        self.log_command(update, "random", query)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, 
                                         action=ChatAction.TYPING)
        
        safe_mode = self.group_settings[str(update.effective_chat.id)]['safe_mode']
        gifs = await self.tenor.search_gif(query, limit=20, safe_search=safe_mode)
        
        if not gifs:
            await update.message.reply_text(f'🚫 No GIFs found for "{query}" 😢')
            return
        
        # Send random GIF from results
        import random
        random_gif = random.choice(gifs)
        await update.message.reply_animation(
            random_gif, 
            caption=f"🎲 **Random GIF** for *{query}*",
            parse_mode='Markdown'
        )
        
        self.user_stats[str(update.effective_user.id)] += 1
        self.save_data()
    
    async def trending_gifs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trending GIFs"""
        self.log_command(update, "trending")
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, 
                                         action=ChatAction.TYPING)
        
        gifs = await self.tenor.get_trending(limit=3)
        
        if not gifs:
            await update.message.reply_text("🚫 Couldn't fetch trending GIFs right now 😢")
            return
        
        await update.message.reply_text("🔥 **Trending GIFs right now:**", parse_mode='Markdown')
        
        for i, gif_url in enumerate(gifs):
            await update.message.reply_animation(
                gif_url,
                caption=f"🔥 **Trending #{i+1}**",
                parse_mode='Markdown'
            )
        
        self.user_stats[str(update.effective_user.id)] += len(gifs)
        self.save_data()
    
    async def add_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add GIF to favorites"""
        if not update.message.reply_to_message or not update.message.reply_to_message.animation:
            await update.message.reply_text("⭐ **Reply to a GIF** with `/fav add` to save it!", 
                                          parse_mode='Markdown')
            return
        
        user_id = str(update.effective_user.id)
        gif_file_id = update.message.reply_to_message.animation.file_id
        
        if gif_file_id in self.favorites[user_id]:
            await update.message.reply_text("⭐ This GIF is already in your favorites!")
            return
        
        self.favorites[user_id].append(gif_file_id)
        self.save_data()
        
        await update.message.reply_text(
            f"⭐ **GIF saved to favorites!** ({len(self.favorites[user_id])} total)\n"
            f"Use `/fav list` to see all your favorites!",
            parse_mode='Markdown'
        )
        
        self.log_command(update, "fav add")
    
    async def list_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List user's favorite GIFs"""
        user_id = str(update.effective_user.id)
        user_favs = self.favorites[user_id]
        
        if not user_favs:
            await update.message.reply_text("⭐ You don't have any favorite GIFs yet!\n"
                                          "Reply to any GIF with `/fav add` to save it.", 
                                          parse_mode='Markdown')
            return
        
        self.log_command(update, "fav list")
        
        await update.message.reply_text(f"⭐ **Your {len(user_favs)} favorite GIFs:**", 
                                      parse_mode='Markdown')
        
        for i, gif_file_id in enumerate(user_favs[:10]):  # Show max 10
            try:
                await update.message.reply_animation(
                    gif_file_id,
                    caption=f"⭐ **Favorite #{i+1}**",
                    parse_mode='Markdown'
                )
            except Exception:
                # If GIF is no longer accessible, remove it
                self.favorites[user_id].remove(gif_file_id)
        
        if len(user_favs) > 10:
            await update.message.reply_text(f"... and {len(user_favs) - 10} more!")
        
        self.save_data()
    
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
        elif action == "remove" and len(context.args) > 1:
            await self.remove_favorite(update, context)
        else:
            await update.message.reply_text(
                "⭐ **Favorites Commands:**\n"
                "`/fav add` - Reply to a GIF to save it\n"
                "`/fav list` - Show your favorites\n"
                "`/fav remove [number]` - Remove favorite",
                parse_mode='Markdown'
            )
    
    async def remove_favorite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove GIF from favorites"""
        if len(context.args) < 2 or not context.args[1].isdigit():
            await update.message.reply_text("⭐ **Usage:** `/fav remove [number]`", parse_mode='Markdown')
            return
        
        user_id = str(update.effective_user.id)
        index = int(context.args[1]) - 1
        
        if index < 0 or index >= len(self.favorites[user_id]):
            await update.message.reply_text("⭐ Invalid favorite number!", parse_mode='Markdown')
            return
        
        removed = self.favorites[user_id].pop(index)
        self.save_data()
        
        await update.message.reply_text(f"⭐ **Favorite #{index+1} removed!**", parse_mode='Markdown')
        self.log_command(update, "fav remove")
    
    async def toggle_passive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle passive mode (admin only)"""
        if not await self.is_admin(update, context):
            return
        
        chat_id = str(update.effective_chat.id)
        current = self.group_settings[chat_id]['passive_mode']
        self.group_settings[chat_id]['passive_mode'] = not current
        self.save_data()
        
        status = "enabled" if not current else "disabled"
        await update.message.reply_text(
            f"🤖 **Passive mode {status}!**\n"
            f"I will {'now' if not current else 'no longer'} react to keywords like 'lol', 'bruh', 'sad'",
            parse_mode='Markdown'
        )
        
        self.log_command(update, "toggle passive", status)
    
    async def set_max_gifs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set maximum GIFs per search (admin only)"""
        if not await self.is_admin(update, context):
            return
        
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("⚙️ **Usage:** `/setmax [1-5]`", parse_mode='Markdown')
            return
        
        max_count = min(int(context.args[0]), 5)
        chat_id = str(update.effective_chat.id)
        self.group_settings[chat_id]['max_gifs'] = max_count
        self.save_data()
        
        await update.message.reply_text(
            f"⚙️ **Default GIF count set to {max_count}**",
            parse_mode='Markdown'
        )
        
        self.log_command(update, "setmax", str(max_count))
    
    async def toggle_safe_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle safe mode (admin only)"""
        if not await self.is_admin(update, context):
            return
        
        chat_id = str(update.effective_chat.id)
        current = self.group_settings[chat_id]['safe_mode']
        self.group_settings[chat_id]['safe_mode'] = not current
        self.save_data()
        
        status = "enabled" if not current else "disabled"
        await update.message.reply_text(
            f"🔒 **Safe mode {status}!**\n"
            f"NSFW content filtering is now {'ON' if not current else 'OFF'}",
            parse_mode='Markdown'
        )
        
        self.log_command(update, "safe mode", status)
    
    async def user_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user_id = str(update.effective_user.id)
        user_count = self.user_stats[user_id]
        fav_count = len(self.favorites[user_id])
        
        await update.message.reply_text(
            f"📊 **Your GIF Stats:**\n\n"
            f"🎬 GIFs requested: **{user_count}**\n"
            f"⭐ Favorites saved: **{fav_count}**\n"
            f"🏆 Rank: **{'GIF Master' if user_count > 100 else 'GIF Enthusiast' if user_count > 50 else 'GIF Explorer'}**",
            parse_mode='Markdown'
        )
        
        self.log_command(update, "stats")
    
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
                import random
                query = random.choice(queries)
                
                safe_mode = self.group_settings[chat_id]['safe_mode']
                gifs = await self.tenor.search_gif(query, limit=5, safe_search=safe_mode)
                
                if gifs:
                    gif = random.choice(gifs)
                    await update.message.reply_animation(
                        gif,
                        caption=f"🤖 *{trigger}*",
                        parse_mode='Markdown'
                    )
                    
                    self.user_stats[str(update.effective_user.id)] += 1
                    self.save_data()
                break
    
    async def is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin"""
        if update.effective_chat.type == "private":
            return True
        
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, 
                                                     update.effective_user.id)
            is_admin = member.status in ['administrator', 'creator']
            
            if not is_admin:
                await update.message.reply_text("🔒 This command is for admins only!")
            
            return is_admin
        except Exception:
            return False

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
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CallbackQueryHandler(bot.help_callback))
    application.add_handler(CommandHandler("s", bot.search_gif))
    application.add_handler(CommandHandler("r", bot.random_gif))
    application.add_handler(CommandHandler("trending", bot.trending_gifs))
    application.add_handler(CommandHandler("fav", bot.handle_favorites))
    application.add_handler(CommandHandler("toggle", bot.toggle_passive))
    application.add_handler(CommandHandler("setmax", bot.set_max_gifs))
    application.add_handler(CommandHandler("safe", bot.toggle_safe_mode))
    application.add_handler(CommandHandler("stats", bot.user_stats))
    
    # Add message handler for passive triggers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, 
                                         bot.handle_passive_triggers))
    
    # Add enhanced features
    bot.enhanced.add_handlers(application)
    
    # Start bot
    console.print(Panel.fit(
        "[bold green]🎬 Advanced GIF Bot Starting...[/bold green]\n"
        "[yellow]Ready to serve GIFs![/yellow]",
        border_style="green"
    ))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
