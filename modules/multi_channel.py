"""
Multi-Channel Manager
Manage multiple YouTube channels from one system.
Each channel gets its own niche, credentials, and schedule.

SETUP:
1. Create separate YouTube OAuth credentials for each channel
2. Put each client_secret as client_secret_channel1.json, etc.
3. Configure channels below
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import NICHES, BASE_DIR
from utils import get_logger

log = get_logger("multi_channel")

CHANNELS_CONFIG_FILE = str(BASE_DIR / "config" / "channels.json")

# Default channel configuration
DEFAULT_CHANNELS = [
    {
        "id": "channel_1",
        "name": "AI & Tech Facts",
        "niche_index": 0,  # AI & Technology
        "client_secret": "config/client_secret_ch1.json",
        "token_file": "config/youtube_token_ch1.json",
        "videos_per_day": 4,
        "enabled": True,
    },
    {
        "id": "channel_2",
        "name": "Money & Business",
        "niche_index": 1,  # Money & Business
        "client_secret": "config/client_secret_ch2.json",
        "token_file": "config/youtube_token_ch2.json",
        "videos_per_day": 4,
        "enabled": False,  # Enable when you add credentials
    },
    {
        "id": "channel_3",
        "name": "Psychology Facts",
        "niche_index": 2,
        "client_secret": "config/client_secret_ch3.json",
        "token_file": "config/youtube_token_ch3.json",
        "videos_per_day": 4,
        "enabled": False,
    },
    {
        "id": "channel_4",
        "name": "Space & Science",
        "niche_index": 3,
        "client_secret": "config/client_secret_ch4.json",
        "token_file": "config/youtube_token_ch4.json",
        "videos_per_day": 4,
        "enabled": False,
    },
    {
        "id": "channel_5",
        "name": "History Facts",
        "niche_index": 4,
        "client_secret": "config/client_secret_ch5.json",
        "token_file": "config/youtube_token_ch5.json",
        "videos_per_day": 4,
        "enabled": False,
    },
]


def load_channels_config() -> List[Dict]:
    """Load channels configuration."""
    if os.path.exists(CHANNELS_CONFIG_FILE):
        try:
            with open(CHANNELS_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CHANNELS


def save_channels_config(channels: List[Dict]):
    """Save channels configuration."""
    with open(CHANNELS_CONFIG_FILE, "w") as f:
        json.dump(channels, f, indent=2)


def init_channels_config():
    """Create default channels.json if it doesn't exist."""
    if not os.path.exists(CHANNELS_CONFIG_FILE):
        save_channels_config(DEFAULT_CHANNELS)
        log.info(f"Created default channels config: {CHANNELS_CONFIG_FILE}")


def get_enabled_channels() -> List[Dict]:
    """Get list of enabled channels."""
    channels = load_channels_config()
    return [ch for ch in channels if ch.get("enabled", False)]


def run_multi_channel_batch(dry_run: bool = False):
    """
    Run video creation for all enabled channels.
    Each channel creates videos in its assigned niche.
    """
    from main import create_single_video
    import config.settings as settings

    channels = get_enabled_channels()
    if not channels:
        log.warning("No channels enabled! Edit config/channels.json to enable channels.")
        return []

    log.info(f"Running multi-channel batch: {len(channels)} channels")
    all_results = []

    for ch in channels:
        log.info(f"\n{'='*60}")
        log.info(f"Channel: {ch['name']} ({ch['id']})")
        log.info(f"{'='*60}")

        niche = NICHES[ch["niche_index"] % len(NICHES)]

        # Temporarily swap YouTube credentials
        original_secret = settings.YOUTUBE_CLIENT_SECRET_FILE
        original_token = settings.YOUTUBE_TOKEN_FILE

        ch_secret = str(BASE_DIR / ch["client_secret"])
        ch_token = str(BASE_DIR / ch["token_file"])

        if os.path.exists(ch_secret):
            settings.YOUTUBE_CLIENT_SECRET_FILE = ch_secret
            settings.YOUTUBE_TOKEN_FILE = ch_token
        else:
            log.warning(f"Client secret not found for {ch['name']}: {ch_secret}")
            if not dry_run:
                log.warning("Skipping this channel (no credentials)")
                continue

        # Create video for this channel
        result = create_single_video(niche=niche, dry_run=dry_run)
        result["channel"] = ch["name"]
        all_results.append(result)

        # Restore original credentials
        settings.YOUTUBE_CLIENT_SECRET_FILE = original_secret
        settings.YOUTUBE_TOKEN_FILE = original_token

    # Summary
    success = sum(1 for r in all_results if r["success"])
    log.info(f"\nMulti-channel batch complete: {success}/{len(all_results)} videos")

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Channel Manager")
    parser.add_argument("--init", action="store_true", help="Create default channels config")
    parser.add_argument("--list", action="store_true", help="List all channels")
    parser.add_argument("--run", action="store_true", help="Run multi-channel batch")
    parser.add_argument("--dry-run", action="store_true", help="Skip uploads")

    args = parser.parse_args()

    if args.init:
        init_channels_config()
        print(f"Channels config created: {CHANNELS_CONFIG_FILE}")

    elif args.list:
        channels = load_channels_config()
        print("\nConfigured Channels:")
        for ch in channels:
            status = "ENABLED" if ch["enabled"] else "disabled"
            niche = NICHES[ch["niche_index"]]["name"]
            has_creds = os.path.exists(str(BASE_DIR / ch["client_secret"]))
            cred_status = "credentials OK" if has_creds else "NO CREDENTIALS"
            print(f"  [{status}] {ch['name']} → {niche} ({cred_status})")

    elif args.run:
        results = run_multi_channel_batch(dry_run=args.dry_run)
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            print(f"[{status}] {r.get('channel', 'N/A')}: {r.get('idea', r.get('error', ''))}")

    else:
        parser.print_help()
