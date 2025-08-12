# 🎬 Advanced Telegram GIF Bot

A feature-rich, visually polished Telegram bot for GIF searches, favorites management, and interactive features.

![Bot Demo](https://img.shields.io/badge/Status-Ready%20to%20Deploy-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue)

## ✨ Features

### 🔍 **Core GIF Search**
- `/s [query]` - Search for the best matching GIF
- `/s [query] [n]` - Get multiple GIFs (max 5)
- `/r [query]` - Random GIF from search results
- `/trending` - Top trending GIFs

### ⭐ **Smart Favorites System**
- `/fav add` - Save GIFs to personal favorites (reply to GIF)
- `/fav list` - Browse all saved favorites
- `/fav remove [n]` - Remove specific favorites
- Automatic cleanup of inaccessible GIFs

### 🏷️ **GIF Labeling & Quick Access**
- `/label [keyword]` - Label GIFs for quick retrieval
- `/gif [keyword]` - Instantly access labeled GIFs
- Personal label management per user

### 🤖 **Intelligent Passive Mode**
Auto-reacts to keywords when enabled:
- "lol" → funny/laugh GIFs
- "bruh" → facepalm GIFs
- "sad" → crying GIFs
- "happy" → celebration GIFs
- And many more triggers!

### ⚙️ **Admin Controls**
- `/toggle passive` - Enable/disable auto-reactions
- `/setmax [n]` - Set default GIF count (1-5)
- `/safe` - Toggle NSFW content filtering
- Group-specific settings

### 📊 **Enhanced Features**
- `/stats` - Personal usage statistics
- `/quote [query]` - Motivational quotes + matching GIFs
- `/schedule [time] [query]` - Schedule GIF posts
- `/info` - Get GIF technical details
- `/random` - Completely random GIF surprise

### 🎨 **Visual Experience**
- Beautiful Rich terminal logging with colors
- Typing animations before sending GIFs
- Markdown formatting with emojis
- Interactive help system with buttons
- Clean, professional message formatting

## 🚀 Quick Setup

### 1. **Prerequisites**
```bash
# Python 3.8 or higher
python3 --version

# Git (to clone repository)
git --version
```

### 2. **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd telegram-gif-bot

# Install dependencies
pip install -r requirements.txt
```

### 3. **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
```ini
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TENOR_API_KEY=your_tenor_api_key_here
```

### 4. **Getting API Keys**

#### **Telegram Bot Token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Choose a name and username for your bot
4. Copy the provided token to `.env`

#### **Tenor API Key:**
1. Visit [Tenor Developer Portal](https://developers.google.com/tenor)
2. Create a new project
3. Enable Tenor API v2
4. Generate API key and add to `.env`

### 5. **Launch Bot**
```bash
# Start the bot
python3 bot.py
```

You should see beautiful colored output indicating the bot is running!

## 📖 Command Reference

### **Search Commands**
| Command | Description | Example |
|---------|-------------|---------|
| `/s [query]` | Search for GIF | `/s dancing cat` |
| `/s [query] [n]` | Multiple GIFs | `/s funny dogs 3` |
| `/r [query]` | Random GIF | `/r celebration` |
| `/trending` | Trending GIFs | `/trending` |

### **Favorites Management**
| Command | Description | Usage |
|---------|-------------|-------|
| `/fav add` | Save GIF | Reply to GIF with command |
| `/fav list` | Show favorites | `/fav list` |
| `/fav remove [n]` | Remove favorite | `/fav remove 3` |

### **Quick Access**
| Command | Description | Example |
|---------|-------------|---------|
| `/label [keyword]` | Label a GIF | Reply to GIF: `/label happy` |
| `/gif [keyword]` | Access labeled GIF | `/gif happy` |
| `/gif` | List all labels | `/gif` |

### **Admin Commands**
| Command | Description | Access |
|---------|-------------|--------|
| `/toggle passive` | Auto-reactions on/off | Admin only |
| `/setmax [1-5]` | Default GIF count | Admin only |
| `/safe` | NSFW filter toggle | Admin only |

### **Fun Features**
| Command | Description | Example |
|---------|-------------|---------|
| `/quote [query]` | Quote + GIF | `/quote motivation` |
| `/schedule [time] [query]` | Schedule GIF | `/schedule 15:30 party` |
| `/stats` | Usage statistics | `/stats` |
| `/info` | GIF details | Reply to GIF |
| `/random` | Random surprise | `/random` |

## 🔧 Advanced Configuration

### **Custom Trigger Words**
Edit the `triggers` dictionary in `bot.py`:
```python
self.triggers = {
    'lol': ['funny', 'laugh', 'lmao'],
    'custom_trigger': ['search', 'terms'],
    # Add your own triggers
}
```

### **Motivational Quotes**
Add custom quotes in `enhanced_features.py`:
```python
self.motivational_quotes = [
    "Your custom quote here - Author",
    # Add more quotes
]
```

### **Safe Mode Defaults**
Modify group settings in `bot.py`:
```python
self.group_settings = defaultdict(lambda: {
    'passive_mode': False,    # Auto-reactions
    'max_gifs': 3,           # Default count
    'safe_mode': True        # Content filtering
})
```

## 📁 File Structure
```
telegram-gif-bot/
├── bot.py                  # Main bot application
├── tenor_api.py           # Tenor API handler
├── enhanced_features.py   # Additional features
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── README.md            # This file
├── bot_data.json        # Persistent data (auto-created)
└── logs/               # Log files (auto-created)
```

## 🛠️ Troubleshooting

### **Common Issues**

**Bot doesn't respond:**
- Check if `TELEGRAM_BOT_TOKEN` is correct
- Verify bot is added to group and has permissions
- Check terminal for error messages

**No GIFs found:**
- Verify `TENOR_API_KEY` is valid
- Check internet connection
- Try different search queries

**Permission errors:**
- Ensure bot is admin in groups for admin commands
- Check file permissions for `bot_data.json`

**Rich formatting issues:**
```bash
# Install Rich if colors don't show
pip install rich --upgrade
```

### **Debug Mode**
Enable detailed logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🌟 Features in Detail

### **Passive Mode Intelligence**
When enabled, the bot intelligently detects context and responds with appropriate GIFs:
- Sentiment analysis of messages
- Context-aware GIF selection
- Customizable trigger words
- Rate limiting to avoid spam

### **Advanced Favorites**
- Unlimited favorites per user
- Automatic duplicate detection
- Dead link cleanup
- Export/import functionality (planned)

### **Smart Scheduling**
- Natural language time parsing
- Timezone support (planned)
- Recurring schedules (planned)
- Schedule management commands

### **Analytics & Stats**
- User engagement tracking
- Popular query analysis
- Usage patterns
- Group activity metrics

## 🔮 Roadmap

- [ ] **Database Integration** (PostgreSQL/SQLite)
- [ ] **Web Dashboard** for bot management
- [ ] **Multiple API Sources** (Giphy, custom)
- [ ] **GIF Editing** (crop, resize, filters)
- [ ] **User Permissions** system
- [ ] **Webhook Support** for better performance
- [ ] **Multi-language** support
- [ ] **GIF Collections** and playlists

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Telegram Bot API** for the excellent bot framework
- **Tenor API** for providing high-quality GIFs
- **Rich Library** for beautiful terminal output
- **python-telegram-bot** for the amazing Python wrapper

## 📞 Support

Having issues? Here's how to get help:

1. **Check the logs** - Terminal output shows detailed information
2. **Read the docs** - This README covers most scenarios  
3. **Search issues** - Someone might have had the same problem
4. **Create an issue** - Provide logs and steps to reproduce

---

**Made with ❤️ for the Telegram community**

*Happy GIF hunting! 🎬*
