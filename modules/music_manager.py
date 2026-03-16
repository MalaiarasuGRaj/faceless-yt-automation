"""
Background Music Manager
Auto-downloads free royalty-free background music from Pixabay.
Also manages local music files in assets/music/ folder.
100% FREE - Pixabay music requires no attribution.
"""

import requests
import os
import random
import json
from pathlib import Path
from config.settings import OUTPUT_DIR, ASSETS_DIR
from utils import get_logger

log = get_logger("music")

MUSIC_DIR = ASSETS_DIR / "music"
MUSIC_DIR.mkdir(exist_ok=True)

# Free direct-download background music URLs (royalty-free, no attribution needed)
# These are from free music archives that allow direct linking
FREE_MUSIC_URLS = [
    {
        "name": "cinematic_dark",
        "url": "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
        "style": "dark cinematic",
    },
    {
        "name": "dramatic_tension",
        "url": "https://cdn.pixabay.com/audio/2022/10/25/audio_33f0258c61.mp3",
        "style": "dramatic tension",
    },
    {
        "name": "inspiring_ambient",
        "url": "https://cdn.pixabay.com/audio/2022/03/15/audio_4a28165a0a.mp3",
        "style": "inspiring ambient",
    },
    {
        "name": "tech_future",
        "url": "https://cdn.pixabay.com/audio/2023/07/19/audio_e55e8a7c0f.mp3",
        "style": "technology future",
    },
    {
        "name": "mystery_suspense",
        "url": "https://cdn.pixabay.com/audio/2022/11/22/audio_a1b9b5d4e4.mp3",
        "style": "mystery suspense",
    },
]


def download_music(url: str, filename: str) -> str:
    """Download a music file from URL."""
    output_path = str(MUSIC_DIR / filename)

    if os.path.exists(output_path):
        log.info(f"Music already exists: {filename}")
        return output_path

    try:
        log.info(f"Downloading background music: {filename}")
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            log.info(f"Music downloaded: {output_path}")
            return output_path
        else:
            log.warning(f"Music download failed: HTTP {resp.status_code}")
    except Exception as e:
        log.warning(f"Music download error: {e}")

    return ""


def auto_download_music() -> list:
    """Auto-download a few free background music tracks."""
    downloaded = []
    for track in FREE_MUSIC_URLS[:3]:  # Download first 3
        path = download_music(track["url"], f"{track['name']}.mp3")
        if path:
            downloaded.append(path)
    return downloaded


def get_background_music() -> str:
    """
    Get a background music file.
    1. First check for user-provided music in assets/music/
    2. If none found, auto-download free music
    Returns path to music file, or empty string.
    """
    # Check for existing music files
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))

    if not music_files:
        # No music found - try to auto-download
        log.info("No background music found. Auto-downloading free tracks...")
        downloaded = auto_download_music()
        if downloaded:
            music_files = [Path(p) for p in downloaded]

    if music_files:
        chosen = random.choice(music_files)
        log.info(f"Using background music: {chosen.name}")
        return str(chosen)

    log.info("No background music available. Videos will have voice only.")
    return ""


def generate_silence(duration: float, output_path: str = None) -> str:
    """Generate a silent audio file (fallback)."""
    import subprocess

    if output_path is None:
        output_path = str(OUTPUT_DIR / "silence.mp3")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duration),
        "-c:a", "libmp3lame",
        "-q:a", "9",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
        return output_path
    except Exception as e:
        log.warning(f"Silence generation failed: {e}")
        return ""


if __name__ == "__main__":
    print("Background Music Manager")
    print(f"Music directory: {MUSIC_DIR}")

    # Check existing
    existing = list(MUSIC_DIR.glob("*.mp3"))
    print(f"Existing tracks: {len(existing)}")

    # Try auto-download
    music = get_background_music()
    if music:
        print(f"Selected track: {music}")
    else:
        print("No music available.")
        print("Tip: Put .mp3 files in assets/music/ or run this script to auto-download.")