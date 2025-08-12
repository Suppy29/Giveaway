#!/usr/bin/env python3
"""
Enhanced Features for GIF Bot
Additional functionality including quotes, scheduling, and GIF labeling
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update
from telegram.ext import ContextTypes
from rich.console import Console

console = Console()

class EnhancedFeatures:
    """Additional features for the GIF bot"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.motivational_quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
            "The only impossible journey is the one you never begin. - Tony Robbins",
            "In the midst of winter, I found there was, within me, an invincible summer. - Albert Camus",
            "Be yourself; everyone else is already taken. - Oscar Wilde",
            "Two roads diverged in a wood, and I— I took the one less traveled by. - Robert Frost"
        ]
    
    async def quote_with_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send motivational quote with matching GIF"""
        if not context.args:
            query = "motivation"
        else:
            query = ' '.join(context.args)
        
        self.bot.log_command(update, "quote", query)
        
        # Get random quote
        quote = random.choice(self.motivational_quotes)
        
        # Search for matching GIF
        safe_mode = self.bot.group_settings[str(update.effective_chat.id)]['safe_mode']
        gifs = await self.bot.tenor.search_gif(query, limit=5, safe_search=safe_mode)
        
        # Send quote first
        await update.message.reply_text(
            f"✨ **Daily Motivation** ✨\n\n*{quote}*",
            parse_mode='Markdown'
        )
        
        # Send matching GIF if found
        if gifs:
            gif = random.choice(gifs)
            await update.message.reply_animation(
                gif,
                caption=f"🎬 *{query} vibes*",
                parse_mode='Markdown'
            )
            
            self.bot.user_stats[str(update.effective_user.id)] += 1
            self.bot.save_data()
    
    async def label_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Label the last sent GIF for quick access"""
        if not context.args:
            await update.message.reply_text(
                "🏷️ **Usage:** `/label [keyword]`\n"
                "Reply to a GIF or use after sending one",
                parse_mode='Markdown'
            )
            return
        
        keyword = ' '.join(context.args).lower()
        user_id = str(update.effective_user.id)
        
        gif_file_id = None
        
        # Check if replying to a GIF
        if update.message.reply_to_message and update.message.reply_to_message.animation:
            gif_file_id = update.message.reply_to_message.animation.file_id
        else:
            # Look for recent GIF in chat (this would need message history)
            await update.message.reply_text(
                "🏷️ **Please reply to a GIF** with `/label [keyword]`",
                parse_mode='Markdown'
            )
            return
        
        # Store label
        if user_id not in self.bot.gif_labels:
            self.bot.gif_labels[user_id] = {}
        
        self.bot.gif_labels[user_id][keyword] = gif_file_id
        self.bot.save_data()
        
        await update.message.reply_text(
            f"🏷️ **GIF labeled as '{keyword}'**\n"
            f"Use `/gif {keyword}` to access it quickly!",
            parse_mode='Markdown'
        )
        
        self.bot.log_command(update, "label", keyword)
    
    async def quick_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Access labeled GIF quickly"""
        if not context.args:
            user_id = str(update.effective_user.id)
            labels = list(self.bot.gif_labels.get(user_id, {}).keys())
            
            if not labels:
                await update.message.reply_text(
                    "🏷️ **No labeled GIFs yet!**\n"
                    "Reply to any GIF with `/label [keyword]` to save it",
                    parse_mode='Markdown'
                )
                return
            
            labels_text = ', '.join(labels[:10])
            await update.message.reply_text(
                f"🏷️ **Your labeled GIFs:**\n`{labels_text}`\n\n"
                f"**Usage:** `/gif [keyword]`",
                parse_mode='Markdown'
            )
            return
        
        keyword = ' '.join(context.args).lower()
        user_id = str(update.effective_user.id)
        
        gif_file_id = self.bot.gif_labels.get(user_id, {}).get(keyword)
        
        if not gif_file_id:
            await update.message.reply_text(
                f"🏷️ **No GIF labeled '{keyword}'**\n"
                "Use `/gif` to see your labeled GIFs",
                parse_mode='Markdown'
            )
            return
        
        try:
            await update.message.reply_animation(
                gif_file_id,
                caption=f"🏷️ **{keyword}**",
                parse_mode='Markdown'
            )
            
            self.bot.user_stats[str(update.effective_user.id)] += 1
            self.bot.save_data()
            
        except Exception:
            # GIF no longer accessible
            del self.bot.gif_labels[user_id][keyword]
            self.bot.save_data()
            await update.message.reply_text(
                f"🏷️ **'{keyword}' GIF is no longer available**\n"
                "It has been removed from your labels",
                parse_mode='Markdown'
            )
        
        self.bot.log_command(update, "gif", keyword)
    
    async def schedule_gif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Schedule a GIF to be sent later"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "⏰ **Usage:** `/schedule [HH:MM] [search query]`\n"
                "Example: `/schedule 15:30 celebration`",
                parse_mode='Markdown'
            )
            return
        
        try:
            time_str = context.args[0]
            query = ' '.join(context.args[1:])
            
            # Parse time
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time")
            
            # Calculate target time (today or tomorrow if time has passed)
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Store scheduled task
            task_id = f"{update.effective_chat.id}_{len(self.bot.scheduled_tasks)}"
            self.bot.scheduled_tasks[task_id] = {
                'chat_id': update.effective_chat.id,
                'query': query,
                'time': target_time.isoformat(),
                'user_id': update.effective_user.id
            }
            self.bot.save_data()
            
            # Schedule the task
            delay = (target_time - now).total_seconds()
            asyncio.create_task(self._send_scheduled_gif(task_id, delay))
            
            await update.message.reply_text(
                f"⏰ **GIF scheduled!**\n"
                f"📅 Time: {target_time.strftime('%H:%M')}\n"
                f"🔍 Query: {query}",
                parse_mode='Markdown'
            )
            
            self.bot.log_command(update, "schedule", f"{time_str} {query}")
            
        except ValueError:
            await update.message.reply_text(
                "⏰ **Invalid time format!**\n"
                "Use HH:MM format (24-hour)",
                parse_mode='Markdown'
            )
    
    async def _send_scheduled_gif(self, task_id: str, delay: float):
        """Send scheduled GIF after delay"""
        try:
            await asyncio.sleep(delay)
            
            task = self.bot.scheduled_tasks.get(task_id)
            if not task:
                return
            
            # Search for GIF
            gifs = await self.bot.tenor.search_gif(task['query'], limit=5)
            
            if gifs:
                gif = random.choice(gifs)
                await context.bot.send_animation(
                    chat_id=task['chat_id'],
                    animation=gif,
                    caption=f"⏰ **Scheduled GIF:** *{task['query']}*",
                    parse_mode='Markdown'
                )
                
                # Update stats
                self.bot.user_stats[str(task['user_id'])] += 1
            else:
                await context.bot.send_message(
                    chat_id=task['chat_id'],
                    text=f"⏰ **Scheduled GIF failed:** No results for '{task['query']}'",
                    parse_mode='Markdown'
                )
            
            # Remove completed task
            if task_id in self.bot.scheduled_tasks:
                del self.bot.scheduled_tasks[task_id]
                self.bot.save_data()
                
        except Exception as e:
            console.print(f"[red]❌ Scheduled GIF error: {e}[/red]")
    
    async def gif_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get information about a GIF (reply to GIF)"""
        if not update.message.reply_to_message or not update.message.reply_to_message.animation:
            await update.message.reply_text(
                "📊 **Reply to a GIF** with `/info` to get details",
                parse_mode='Markdown'
            )
            return
        
        gif = update.message.reply_to_message.animation
        
        # Calculate file size in MB
        file_size_mb = round(gif.file_size / (1024 * 1024), 2) if gif.file_size else "Unknown"
        
        info_text = f"""
📊 **GIF Information**

📏 **Dimensions:** {gif.width} × {gif.height}
⏱️ **Duration:** {gif.duration}s
💾 **File Size:** {file_size_mb} MB
🆔 **File ID:** `{gif.file_id[:20]}...`
        """
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
        self.bot.log_command(update, "info")
    
    async def random_trigger(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a completely random GIF"""
        random_queries = [
            "random", "surprise", "funny", "cute", "awesome", 
            "cool", "amazing", "wow", "epic", "crazy"
        ]
        
        query = random.choice(random_queries)
        
        safe_mode = self.bot.group_settings[str(update.effective_chat.id)]['safe_mode']
        gifs = await self.bot.tenor.search_gif(query, limit=20, safe_search=safe_mode)
        
        if gifs:
            gif = random.choice(gifs)
            await update.message.reply_animation(
                gif,
                caption="🎲 **Random GIF!**",
                parse_mode='Markdown'
            )
            
            self.bot.user_stats[str(update.effective_user.id)] += 1
            self.bot.save_data()
        else:
            await update.message.reply_text("🎲 Couldn't find a random GIF right now!")
        
        self.bot.log_command(update, "random")
    
    def add_handlers(self, application):
        """Add enhanced feature handlers to the application"""
        from telegram.ext import CommandHandler
        
        application.add_handler(CommandHandler("quote", self.quote_with_gif))
        application.add_handler(CommandHandler("label", self.label_gif))
        application.add_handler(CommandHandler("gif", self.quick_gif))
        application.add_handler(CommandHandler("schedule", self.schedule_gif))
        application.add_handler(CommandHandler("info", self.gif_info))
        application.add_handler(CommandHandler("random", self.random_trigger))
