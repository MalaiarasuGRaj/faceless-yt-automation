"""
Backup Footage Fetcher - Pixabay API
Used when Pexels has no results or rate-limits you.
Free: 100 requests/min, no watermark.
Sign up: https://pixabay.com/api/docs/
"""

import requests
import time
from typing import List
from config.settings import PIXABAY_API_KEY, OUTPUT_DIR
from utils import get_logger

log = get_logger("pixabay")


def search_pixabay_videos(query: str, count: int = 3) -> List[dict]:
    """Search Pixabay for free stock videos."""
    if PIXABAY_API_KEY == "YOUR_PIXABAY_KEY":
        log.warning("Pixabay API key not set. Get one free at https://pixabay.com/api/docs/")
        return []

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": count,
        "safesearch": "true",
        "video_type": "film",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return []

        data = resp.json()
        videos = []
        for hit in data.get("hits", []):
            vids = hit.get("videos", {})
            # Prefer medium quality
            medium = vids.get("medium", vids.get("small", {}))
            if medium.get("url"):
                videos.append({
                    "id": hit.get("id"),
                    "url": medium["url"],
                    "width": medium.get("width", 0),
                    "height": medium.get("height", 0),
                    "duration": hit.get("duration", 0),
                })

        log.info(f"Pixabay found {len(videos)} videos for '{query}'")
        return videos

    except Exception as e:
        log.error(f"Pixabay search failed: {e}")
        return []


def search_pixabay_images(query: str, count: int = 3) -> List[dict]:
    """Search Pixabay for free images (for backgrounds/thumbnails)."""
    if PIXABAY_API_KEY == "YOUR_PIXABAY_KEY":
        return []

    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": count,
        "safesearch": "true",
        "image_type": "photo",
        "orientation": "vertical",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return [
                {
                    "id": hit.get("id"),
                    "url": hit.get("largeImageURL", ""),
                    "url_medium": hit.get("webformatURL", ""),
                }
                for hit in data.get("hits", [])
            ]
    except Exception as e:
        log.error(f"Pixabay image search failed: {e}")

    return []


if __name__ == "__main__":
    results = search_pixabay_videos("technology", count=3)
    for v in results:
        print(f"  ID: {v['id']}, Duration: {v['duration']}s, URL: {v['url'][:80]}...")
