"""
Stock Footage Fetcher
Downloads free stock videos from Pexels API.
Free tier: 200 requests/hour, no watermark.
Sign up: https://www.pexels.com/api/
"""

import requests
import os
import time
import random
from pathlib import Path
from typing import List, Optional
from config.settings import PEXELS_API_KEY, OUTPUT_DIR, VIDEO_WIDTH, VIDEO_HEIGHT
from utils import get_logger

log = get_logger("footage")


def search_pexels_videos(
    query: str,
    count: int = 3,
    orientation: str = "portrait",
    min_duration: int = 5,
    max_duration: int = 30,
) -> List[dict]:
    """Search for videos on Pexels."""

    if PEXELS_API_KEY == "YOUR_PEXELS_KEY":
        log.warning("Pexels API key not set! Get one free at https://www.pexels.com/api/")
        return []

    # Boost quality by adding aesthetic modifiers if not present
    quality_boost = " cinematic dramatic"
    if quality_boost not in query.lower():
        query += quality_boost

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": orientation,
        "per_page": count * 2,  # Fetch extra in case some don't work
        "size": "medium",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            log.warning(f"Pexels API error: {resp.status_code}")
            return []

        data = resp.json()
        videos = []

        for video in data.get("videos", []):
            duration = video.get("duration", 0)
            if min_duration <= duration <= max_duration:
                # Get the best quality video file
                video_files = video.get("video_files", [])
                # Prefer HD portrait
                best_file = None
                for vf in video_files:
                    w = vf.get("width", 0)
                    h = vf.get("height", 0)
                    if h > w and vf.get("quality") in ["hd", "sd"]:
                        best_file = vf
                        break

                if not best_file and video_files:
                    best_file = video_files[0]

                if best_file:
                    videos.append({
                        "id": video.get("id"),
                        "url": best_file.get("link"),
                        "width": best_file.get("width"),
                        "height": best_file.get("height"),
                        "duration": duration,
                        "quality": best_file.get("quality"),
                    })

            if len(videos) >= count:
                break

        log.info(f"Found {len(videos)} videos for '{query}'")
        return videos

    except Exception as e:
        log.error(f"Pexels search failed: {e}")
        return []


def download_video(url: str, filename: str) -> str:
    """Download a video file."""
    output_path = str(OUTPUT_DIR / filename)

    try:
        log.info(f"Downloading: {filename}")
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        log.info(f"Downloaded: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Download failed: {e}")
        return ""


def fetch_footage_for_keywords(keywords: List[str], clips_per_keyword: int = 1) -> List[str]:
    """
    Fetch stock footage for multiple keywords.
    Tries Pexels first, falls back to Pixabay.
    Returns list of downloaded file paths.
    """
    downloaded = []

    for i, kw in enumerate(keywords):
        # Try Pexels first
        videos = search_pexels_videos(kw, count=clips_per_keyword, orientation="portrait")

        # Fallback to Pixabay if Pexels fails
        if not videos:
            try:
                from modules.pixabay_fetcher import search_pixabay_videos
                videos = search_pixabay_videos(kw, count=clips_per_keyword)
                log.info(f"Using Pixabay fallback for '{kw}'")
            except ImportError:
                pass

        for j, video in enumerate(videos):
            filename = f"clip_{i}_{j}.mp4"
            path = download_video(video["url"], filename)
            if path:
                downloaded.append(path)

        time.sleep(0.5)  # Rate limiting

    log.info(f"Total clips downloaded: {len(downloaded)}")
    return downloaded


def search_pexels_images(query: str, count: int = 1, orientation: str = "portrait") -> List[dict]:
    """Search for images on Pexels (for thumbnails/backgrounds)."""

    if PEXELS_API_KEY == "YOUR_PEXELS_KEY":
        return []

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": orientation,
        "per_page": count,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            images = []
            for photo in data.get("photos", []):
                images.append({
                    "id": photo.get("id"),
                    "url": photo.get("src", {}).get("large2x", ""),
                    "url_medium": photo.get("src", {}).get("medium", ""),
                })
            return images
    except Exception as e:
        log.error(f"Pexels image search failed: {e}")

    return []


if __name__ == "__main__":
    # Test
    keywords = ["technology", "robot", "future city"]
    clips = fetch_footage_for_keywords(keywords, clips_per_keyword=1)
    print(f"Downloaded {len(clips)} clips")
