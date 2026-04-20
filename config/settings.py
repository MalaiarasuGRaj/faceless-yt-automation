"""
YouTube Shorts Automation - Configuration
All settings in one place. Fill in your API keys.
"""

import os
from pathlib import Path

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv is optional

# ============================================================
# PROJECT PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# Create dirs if missing
for d in [ASSETS_DIR, OUTPUT_DIR, TEMPLATES_DIR, LOGS_DIR]:
    d.mkdir(exist_ok=True)

# ============================================================
# FREE API KEYS (Get these for free)
# ============================================================

# Pexels - Free stock video/images
# Sign up: https://www.pexels.com/api/
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "QQiaLu3hY6CyKsB3JnttbUutfzGxwxXGeBBdkJ7UPszx8d5V1GhH2Hbx")

# Pixabay - Free stock video/images (backup)
# Sign up: https://pixabay.com/api/docs/
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "QQiaLu3hY6CyKsB3JnttbUutfzGxwxXGeBBdkJ7UPszx8d5V1GhH2Hbx")

# YouTube Data API - Free quota (10,000 units/day)
# Setup: https://console.cloud.google.com
# Enable: YouTube Data API v3
# Create: OAuth 2.0 Client ID (Desktop app)
# Download: client_secret.json → put in config/ folder
YOUTUBE_CLIENT_SECRET_FILE = str(BASE_DIR / "config" / "client_secret.json")
YOUTUBE_TOKEN_FILE = str(BASE_DIR / "config" / "youtube_token.json")

# ============================================================
# LOCAL AI (Ollama - 100% FREE)
# Install: https://ollama.com
# Then: ollama pull llama3.2:1b
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

# ============================================================
# LANGUAGE SETTINGS
# ============================================================
CONTENT_LANGUAGE = "english"  # "hindi" or "english"
# Hindi me scripts likhega, Hinglish style (Hindi + English mix)
# Jo Indian audience ko sabse zyada pasand aata hai

# ============================================================
# FREE VOICE (edge-tts - Microsoft Edge TTS, completely free)
# pip install edge-tts
# ============================================================
VOICE_NAME = "en-US-GuyNeural"  # Hindi male - deep dramatic voice
# Other options:
# "hi-IN-SwaraNeural"         - Hindi female
# "en-US-ChristopherNeural"   - English male dramatic
# "en-US-JennyNeural"         - English female
# "en-IN-PrabhatNeural"       - Indian English male

# ============================================================
# VIDEO SETTINGS
# ============================================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 9:16 vertical for Shorts
VIDEO_FPS = 30
VIDEO_MAX_DURATION = 59  # YouTube Shorts limit
VIDEO_TARGET_DURATION = 40  # Target length (longer = more watch time)
FONT_SIZE = 18  # Subtitle font size (smaller for Hindi = more readable)
FONT_COLOR = "white"
FONT_BORDER_COLOR = "black"
FONT_BORDER_WIDTH = 4
SUBTITLE_STYLE = "bold"  # bold subtitles for professional look
BACKGROUND_MUSIC_VOLUME = 0.12  # 12% volume for bg music (slightly louder)

# ============================================================
# CONTENT NICHES (Success Shortcuts - Mystery Focus)
# ============================================================
NICHES = [
    {
        "name": "AI Power Hacks",
        "keywords": ["ChatGPT hacks", "AI automation secrets", "best AI tools 2024", "AI productivity tricks", "midjourney prompts tips", "AI video generation secrets"],
        "subreddits": ["ChatGPT", "automation", "ArtificialInteligence", "midjourney", "tech", "futurology"],
    },
    {
        "name": "Money Saving Secrets",
        "keywords": ["frugal living hacks", "money saving tips", "budgeting secrets", "save money fast", "financial freedom hacks", "hidden grocery savings"],
        "subreddits": ["Frugal", "personalfinance", "budget", "savemoney", "LifeProTips", "ConsumerReports"],
    },
    {
        "name": "Easy Side Hustles",
        "keywords": ["easy side hustles 2024", "make money online fast", "passive income ideas", "lazy side hustles", "remote work secrets", "side hustle revenue revealed"],
        "subreddits": ["beermoney", "sidehustle", "PassiveIncome", "onlinebiz", "WorkOnline", "slatestarcodex"],
    },
    {
        "name": "AI Wealth Generation",
        "keywords": ["how to make money with AI", "AI business ideas", "AI side hustles", "automate wealth with AI", "AI trading secrets", "generate passive income with AI"],
        "subreddits": ["ArtificialInteligence", "sidehustle", "entrepreneur", "PassiveIncome", "business", "startups"],
    },
    {
        "name": "Billionaire Money Mindset",
        "keywords": ["billionaire mindset secrets", "wealth building habits", "financial secrets of the rich", "how to think like a billionaire", "investing tips for beginners", "habits of the top 1%"],
        "subreddits": ["finance", "investing", "entrepreneur", "success", "wealth", "business"],
    },
]

# ============================================================
# SCHEDULING
# ============================================================
VIDEOS_PER_DAY = 4
SCHEDULE_INTERVAL_HOURS = 6  # Every 6 hours = 4 videos/day
UPLOAD_HOUR_START = 7  # Upload window start (AM)
UPLOAD_HOUR_END = 21  # Upload window end (PM)

# ============================================================
# LOGGING
# ============================================================
LOG_FILE = str(LOGS_DIR / "automation.log")
LOG_LEVEL = "INFO"