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


def fetch_youtube_trending_topics(max_results: int = 15) -> List[Dict]:
    """
    Fetch YouTube's own trending videos as trend signals.
    Uses the already-authenticated YouTube Data API (no extra quota needed).
    Category IDs: 24=Entertainment, 28=Science&Tech, 22=People&Blogs.
    """
    topics = []
    try:
        from modules.youtube_upload import get_authenticated_service
        youtube = get_authenticated_service()
        if not youtube:
            return []

        category_ids = ["24", "28", "22"]  # Entertainment, Science&Tech, People&Blogs
        seen_ids = set()

        for cat_id in category_ids:
            try:
                response = youtube.videos().list(
                    part="snippet,statistics",
                    chart="mostPopular",
                    regionCode="US",
                    videoCategoryId=cat_id,
                    maxResults=max_results,
                ).execute()

                for item in response.get("items", []):
                    vid_id = item.get("id", "")
                    if vid_id in seen_ids:
                        continue
                    seen_ids.add(vid_id)

                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    topics.append({
                        "source": "youtube_trending",
                        "title": snippet.get("title", ""),
                        "score": int(stats.get("viewCount", 0)) // 1000,  # Views / 1k as score
                        "comments": int(stats.get("commentCount", 0)),
                        "url": f"https://youtube.com/watch?v={vid_id}",
                    })
            except Exception as e:
                log.warning(f"YouTube trending cat {cat_id} failed: {e}")

        log.info(f"Fetched {len(topics)} YouTube trending topics")
    except Exception as e:
        log.warning(f"YouTube trending fetch failed: {e}")

    return topics


def get_all_trends(subreddits: List[str] = None) -> List[Dict]:
    """
    Combine all trend sources with weighted scoring.
    YouTube Trending gets 3× weight (most relevant signal for Shorts).
    Reddit gets 1.5×. HackerNews gets 1×.
    """
    if subreddits is None:
        subreddits = ["technology", "artificial", "science", "todayilearned",
                      "mildlyinteresting", "Damnthatsinteresting"]

    log.info("Fetching trends from all sources...")

    all_topics = []

    # YouTube Trending — strongest signal, weight ×3
    yt_trends = fetch_youtube_trending_topics()
    for t in yt_trends:
        t["weighted_score"] = (t.get("score", 0) + t.get("comments", 0)) * 3
    all_topics.extend(yt_trends)

    # Reddit — weight ×1.5
    reddit_trends = fetch_reddit_trends(subreddits)
    for t in reddit_trends:
        t["weighted_score"] = (t.get("score", 0) + t.get("comments", 0)) * 1.5
    all_topics.extend(reddit_trends)

    # HackerNews — weight ×1
    hn_trends = fetch_hackernews_trends()
    for t in hn_trends:
        t["weighted_score"] = t.get("score", 0) + t.get("comments", 0)
    all_topics.extend(hn_trends)

    # Google Trends — weight ×1
    gt_trends = fetch_google_trends_rss()
    for t in gt_trends:
        t["weighted_score"] = t.get("score", 0)
    all_topics.extend(gt_trends)

    # Sort by weighted score
    all_topics.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)

    # Deduplicate: by first 50 chars AND by leading word (prevent near-duplicates)
    seen_keys = set()
    seen_first_words = {}
    unique = []
    for t in all_topics:
        title = t.get("title", "")
        key = title.lower()[:50]
        first_word = title.lower().split()[0] if title.split() else ""

        # Skip exact duplicates
        if key in seen_keys:
            continue

        # Limit 2 topics per leading word to avoid near-duplicates
        if seen_first_words.get(first_word, 0) >= 2:
            continue

        seen_keys.add(key)
        seen_first_words[first_word] = seen_first_words.get(first_word, 0) + 1
        unique.append(t)

    # Shuffle top 15 for variety across 4 daily videos
    top_vibrant = unique[:15]
    random.shuffle(top_vibrant)

    log.info(f"Found {len(unique)} unique trends (YouTube: {len(yt_trends)}, "
             f"Reddit: {len(reddit_trends)}, HN: {len(hn_trends)}, GT: {len(gt_trends)})")
    return top_vibrant + unique[15:30]


if __name__ == "__main__":
    trends = get_all_trends()
    for i, t in enumerate(trends[:10], 1):
        print(f"{i}. [{t['source']}] {t['title']} (score: {t['score']})")
