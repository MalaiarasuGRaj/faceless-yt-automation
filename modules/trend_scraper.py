"""
Trend Discovery Engine
Scrapes trending topics from multiple FREE sources:
  - Reddit (no API key needed for public JSON)
  - Hacker News (free API)
  - Google Trends RSS (free)
"""

import requests
import json
import time
import random
from typing import List, Dict
from utils import get_logger

log = get_logger("trends")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_reddit_trends(subreddits: List[str], limit: int = 10) -> List[Dict]:
    """Fetch hot posts from Reddit (free, no auth needed)."""
    topics = []
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for post in data.get("data", {}).get("children", []):
                    pdata = post.get("data", {})
                    topics.append({
                        "source": "reddit",
                        "subreddit": sub,
                        "title": pdata.get("title", ""),
                        "score": pdata.get("score", 0),
                        "comments": pdata.get("num_comments", 0),
                        "url": pdata.get("url", ""),
                    })
            time.sleep(1)  # Rate limiting
        except Exception as e:
            log.warning(f"Reddit fetch failed for r/{sub}: {e}")
    return topics


def fetch_hackernews_trends(limit: int = 15) -> List[Dict]:
    """Fetch top stories from Hacker News (free API, no key)."""
    topics = []
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(url, timeout=10)
        story_ids = resp.json()[:limit]

        for sid in story_ids:
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                item = requests.get(item_url, timeout=10).json()
                if item and item.get("title"):
                    topics.append({
                        "source": "hackernews",
                        "title": item.get("title", ""),
                        "score": item.get("score", 0),
                        "comments": item.get("descendants", 0),
                        "url": item.get("url", ""),
                    })
            except Exception:
                continue
            time.sleep(0.2)
    except Exception as e:
        log.warning(f"HackerNews fetch failed: {e}")
    return topics


def fetch_google_trends_rss() -> List[Dict]:
    """Fetch Google Trends daily trends (free RSS)."""
    topics = []
    try:
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            # Simple XML parsing without external lib
            text = resp.text
            items = text.split("<item>")[1:]
            for item in items[:15]:
                title_start = item.find("<title>") + 7
                title_end = item.find("</title>")
                if title_start > 6 and title_end > title_start:
                    title = item[title_start:title_end].strip()
                    topics.append({
                        "source": "google_trends",
                        "title": title,
                        "score": 100,
                        "comments": 0,
                        "url": "",
                    })
    except Exception as e:
        log.warning(f"Google Trends fetch failed: {e}")
    return topics


def get_all_trends(subreddits: List[str] = None) -> List[Dict]:
    """
    Combine all trend sources and sort by engagement score.
    """
    if subreddits is None:
        subreddits = ["technology", "artificial", "science", "todayilearned"]

    log.info("Fetching trends from all sources...")

    all_topics = []
    all_topics.extend(fetch_reddit_trends(subreddits))
    all_topics.extend(fetch_hackernews_trends())
    all_topics.extend(fetch_google_trends_rss())

    # Sort by engagement (score + comments)
    all_topics.sort(key=lambda x: x.get("score", 0) + x.get("comments", 0), reverse=True)

    # Remove duplicates by title similarity
    seen = set()
    unique = []
    for t in all_topics:
        key = t["title"].lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(t)

    # Get top 15 and shuffle them to ensure variety for multiple daily videos
    top_vibrant = unique[:15]
    random.shuffle(top_vibrant)
    
    log.info(f"Picked {len(top_vibrant)} unique trends with variety shuffling")
    return top_vibrant + unique[15:30]  # Top shuffled + rest as backup


if __name__ == "__main__":
    trends = get_all_trends()
    for i, t in enumerate(trends[:10], 1):
        print(f"{i}. [{t['source']}] {t['title']} (score: {t['score']})")
