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
# Weights are updated dynamically by analytics_engine.py
# based on real channel performance data.
# ============================================================
NICHES = [
    {
        # Real channel data (May 1-9): avg 5-85 views. Heavily saturated niche.
        "name": "AI Power Hacks",
        "weight": 0.5,
        "keywords": ["ChatGPT secret features", "AI automation nobody uses", "hidden AI tools 2025", "AI productivity tricks pros use", "midjourney advanced secrets", "AI tools that replace jobs"],
        "subreddits": ["ChatGPT", "automation", "ArtificialInteligence", "midjourney", "tech", "futurology"],
    },
    {
        # Real channel data: avg 0-49 views. Weak on this channel.
        "name": "Money Saving Secrets",
        "weight": 0.8,
        "keywords": ["frugal living hacks", "money saving tips", "budgeting secrets", "save money fast", "financial freedom hacks", "hidden grocery savings"],
        "subreddits": ["Frugal", "personalfinance", "budget", "savemoney", "LifeProTips", "ConsumerReports"],
    },
    {
        # Weak on this channel. Keep low weight.
        "name": "Easy Side Hustles",
        "weight": 0.5,
        "keywords": ["easy side hustles 2025", "make money online fast", "passive income ideas", "lazy side hustles", "remote work secrets", "side hustle revenue revealed"],
        "subreddits": ["beermoney", "sidehustle", "PassiveIncome", "onlinebiz", "WorkOnline", "slatestarcodex"],
    },
    {
        # Very weak — keep minimal presence.
        "name": "AI Wealth Generation",
        "weight": 0.3,
        "keywords": ["how to make money with AI", "AI business ideas", "AI side hustles", "automate wealth with AI", "AI trading secrets", "generate passive income with AI"],
        "subreddits": ["ArtificialInteligence", "sidehustle", "entrepreneur", "PassiveIncome", "business", "startups"],
    },
    {
        # Moderate performer. Real data: Elon Musk 49v, Tim Ferriss 14v, Warren Buffett 0v.
        "name": "Billionaire Money Mindset",
        "weight": 1.2,
        "keywords": ["billionaire habits nobody talks about", "wealth secrets of the ultra-rich", "how Elon Musk actually thinks", "what billionaires do before 6am", "hidden investing strategy of the 1%", "financial secrets from Warren Buffett"],
        "subreddits": ["finance", "investing", "entrepreneur", "success", "wealth", "business"],
    },
    {
        # STAR NICHE. Real data: Angkor Wat 725v, Petra 76v, Derinkuyu 38v, Tbilisi 87v.
        # This is 10-40x better than any other niche on this channel.
        "name": "Hidden Places & Mysteries",
        "weight": 5.0,  # Dominant weight — proven best performer
        "keywords": [
            "secret underground cities world", "hidden ancient civilizations discovered",
            "abandoned mysterious locations earth", "forbidden zones nobody can enter",
            "lost cities found underground", "what archaeologists found beneath ancient temples",
            "hidden tunnels beneath famous cities", "mysterious discoveries buried for centuries",
        ],
        "subreddits": ["mildlyinteresting", "Damnthatsinteresting", "todayilearned", "interestingasfuck", "geography", "history", "AncientCivilizations", "archaeology"],
    },
]

# ============================================================
# HOOK TYPE ROTATION WEIGHTS
# Controls which hook style the AI uses for each video.
# Prevents formula fatigue from over-using one pattern.
# ============================================================
HOOK_TYPE_WEIGHTS = {
    "negative": 0.25,      # "Stop doing X until you see this"
    "statistical": 0.20,   # "99% of people miss this..."
    "curiosity_gap": 0.25, # "What's hiding beneath your city?"
    "real_news": 0.15,     # "[Real company] just did something shocking"
    "geographic": 0.15,    # "Japan's secret underground revealed"
}

# ============================================================
# SCHEDULING
# All 4 videos are created at once, then uploaded to YouTube
# as SCHEDULED posts — laptop only needs to be on during
# the creation run. YouTube handles publishing automatically.
# ============================================================
VIDEOS_PER_DAY = 4
SCHEDULE_INTERVAL_HOURS = 6   # 6-hour gap between scheduled publishes
UPLOAD_HOUR_START = 9         # First video publish at 9:00 AM (IST)
UPLOAD_HOUR_END = 22          # Last video no later than 10:00 PM (IST)

# ── Research-backed optimal publish times (IST) ──────────────────────────
# Based on YouTube Shorts engagement data + India audience patterns:
#
#   9:00 AM  → Morning commuters + early risers. Low competition, algorithm
#               test pool is fresh. Good for curiosity/mystery hooks.
#
#   1:00 PM  → Lunch break. HIGHEST daily traffic window for Indian audience.
#               Peak CPM slot — advertisers are actively bidding at midday.
#               Best video of the day should go here.
#
#   6:00 PM  → Evening commute. Second-largest traffic spike. Viewers are
#               relaxed and in browse mode → higher completion rates.
#
#   9:00 PM  → Post-dinner prime time. Highest CPM window of the day
#               (advertisers pay 3-5× more at night). Long watch sessions.
#               Finance/money/tech niches earn the most at this slot.
#
# Why NOT 8am: Audience still waking up, lower CPM, weaker algorithm push.
# Why NOT 11pm+: Audience drops off sharply, algorithm deprioritizes late posts.
# ─────────────────────────────────────────────────────────────────────────
SCHEDULED_PUBLISH_HOURS_IST = [9, 13, 17, 21]  # 9am, 1pm, 5pm, 9pm IST (4-hour gaps)

# ============================================================
# LOGGING
# ============================================================
LOG_FILE = str(LOGS_DIR / "automation.log")
LOG_LEVEL = "INFO"