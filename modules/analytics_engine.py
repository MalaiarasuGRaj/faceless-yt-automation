"""
Analytics Engine
Tracks video performance and generates AI feedback for optimization.
Stores data in local JSON (no database needed).
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from config.settings import OUTPUT_DIR, LOGS_DIR
from utils import get_logger

log = get_logger("analytics")

ANALYTICS_FILE = str(LOGS_DIR / "video_analytics.json")
PERFORMANCE_FILE = str(LOGS_DIR / "performance_history.json")


def load_analytics() -> list:
    """Load analytics data from file."""
    try:
        if os.path.exists(ANALYTICS_FILE):
            with open(ANALYTICS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_analytics(data: list):
    """Save analytics data."""
    try:
        with open(ANALYTICS_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        log.error(f"Failed to save analytics: {e}")


def record_video(
    video_id: str,
    title: str,
    idea: str,
    niche: str,
    script: str,
    seo_data: dict,
) -> dict:
    """Record a new video in analytics."""
    entry = {
        "video_id": video_id,
        "title": title,
        "idea": idea,
        "niche": niche,
        "script_preview": script[:200],
        "seo": seo_data,
        "created_at": datetime.now().isoformat(),
        "views": 0,
        "likes": 0,
        "comments": 0,
        "watch_time_hours": 0,
        "ctr": 0,
        "last_checked": None,
    }

    data = load_analytics()
    data.append(entry)
    save_analytics(data)

    log.info(f"Recorded video: {video_id} - {title}")
    return entry


def update_video_stats(video_id: str, stats: dict):
    """Update stats for a specific video."""
    data = load_analytics()
    for entry in data:
        if entry.get("video_id") == video_id:
            entry.update({
                "views": stats.get("views", entry.get("views", 0)),
                "likes": stats.get("likes", entry.get("likes", 0)),
                "comments": stats.get("comments", entry.get("comments", 0)),
                "watch_time_hours": stats.get("watch_time_hours", 0),
                "ctr": stats.get("ctr", 0),
                "last_checked": datetime.now().isoformat(),
            })
            break
    save_analytics(data)


def fetch_youtube_stats(video_ids: list) -> dict:
    """Fetch latest stats from YouTube API."""
    try:
        from modules.youtube_upload import get_authenticated_service
        youtube = get_authenticated_service()
        if not youtube:
            return {}

        stats = {}
        # YouTube API allows up to 50 IDs per request
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            response = youtube.videos().list(
                part="statistics",
                id=",".join(batch),
            ).execute()

            for item in response.get("items", []):
                vid = item["id"]
                s = item.get("statistics", {})
                stats[vid] = {
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                }

        return stats
    except Exception as e:
        log.warning(f"Stats fetch failed: {e}")
        return {}


def refresh_all_stats():
    """Refresh stats for all recorded videos."""
    data = load_analytics()
    if not data:
        log.info("No videos to refresh")
        return

    video_ids = [e["video_id"] for e in data if e.get("video_id")]
    if not video_ids:
        return

    stats = fetch_youtube_stats(video_ids)
    for vid, s in stats.items():
        update_video_stats(vid, s)

    log.info(f"Refreshed stats for {len(stats)} videos")


def get_performance_summary() -> dict:
    """Get summary of all video performance."""
    data = load_analytics()
    if not data:
        return {"total_videos": 0}

    total_views = sum(e.get("views", 0) for e in data)
    total_likes = sum(e.get("likes", 0) for e in data)
    avg_views = total_views / len(data) if data else 0

    # Find best performing videos
    sorted_by_views = sorted(data, key=lambda x: x.get("views", 0), reverse=True)

    # Find best niche
    niche_views = {}
    for e in data:
        niche = e.get("niche", "unknown")
        niche_views[niche] = niche_views.get(niche, 0) + e.get("views", 0)

    best_niche = max(niche_views, key=niche_views.get) if niche_views else "unknown"

    return {
        "total_videos": len(data),
        "total_views": total_views,
        "total_likes": total_likes,
        "avg_views_per_video": round(avg_views),
        "best_niche": best_niche,
        "top_videos": sorted_by_views[:5],
        "niche_performance": niche_views,
    }


def compute_niche_weights() -> dict:
    """
    Compute upload probability weights for each niche based on real view performance.
    Returns a dict mapping niche name -> weight (higher = picked more often).
    Falls back to config weights if no analytics data yet.
    """
    from config.settings import NICHES

    data = load_analytics()

    # If no analytics data yet, use config weights as default
    if not data:
        return {n["name"]: n.get("weight", 1.0) for n in NICHES}

    # Calculate avg views per niche from real data
    niche_views = {}
    niche_counts = {}
    for e in data:
        niche = e.get("niche", "unknown")
        niche_views[niche] = niche_views.get(niche, 0) + e.get("views", 0)
        niche_counts[niche] = niche_counts.get(niche, 0) + 1

    niche_avg = {
        n: niche_views[n] / niche_counts[n]
        for n in niche_views
        if niche_counts.get(n, 0) > 0
    }

    # Build weight dict: blend config weight + real avg views
    weights = {}
    config_names = {n["name"]: n.get("weight", 1.0) for n in NICHES}
    for niche in NICHES:
        name = niche["name"]
        config_w = niche.get("weight", 1.0)
        # If we have real data: 50% config + 50% real performance (normalized)
        if name in niche_avg:
            max_avg = max(niche_avg.values()) or 1
            perf_w = (niche_avg[name] / max_avg) * 3.0  # Scale to same range as config weights
            weights[name] = round((config_w + perf_w) / 2, 2)
        else:
            weights[name] = config_w

    log.info(f"Computed niche weights: {weights}")
    return weights


def get_winning_hooks(top_n: int = 10) -> dict:
    """
    Scan top performing videos and extract which hook patterns are winning.
    Returns a dict with counts of each hook type found in top titles.
    """
    data = load_analytics()
    if not data:
        return {}

    # Get top N videos by views
    top = sorted(data, key=lambda x: x.get("views", 0), reverse=True)[:top_n]
    top_titles = [e.get("title", "") for e in top if e.get("views", 0) > 0]

    hook_counts = {
        "negative": 0,
        "statistical": 0,
        "curiosity_gap": 0,
        "real_news": 0,
        "geographic": 0,
    }
    example_titles = {
        "negative": [],
        "statistical": [],
        "curiosity_gap": [],
        "real_news": [],
        "geographic": [],
    }

    geo_keywords = ["japan", "china", "kenya", "underground", "city", "cave", "country", "world"]
    news_keywords = ["microsoft", "google", "apple", "amazon", "ceo", "fbi", "nasa", "elon", "bezos"]
    stat_keywords = ["99%", "90%", "million", "billion", "$", "1,000", "10k", "100", "1m", "%"]

    for title in top_titles:
        tl = title.lower()
        if tl.startswith("stop ") or tl.startswith("don't ") or "until you see" in tl:
            hook_counts["negative"] += 1
            example_titles["negative"].append(title[:60])
        elif any(k in tl for k in stat_keywords):
            hook_counts["statistical"] += 1
            example_titles["statistical"].append(title[:60])
        elif any(k in tl for k in geo_keywords):
            hook_counts["geographic"] += 1
            example_titles["geographic"].append(title[:60])
        elif any(k in tl for k in news_keywords):
            hook_counts["real_news"] += 1
            example_titles["real_news"].append(title[:60])
        else:
            hook_counts["curiosity_gap"] += 1
            example_titles["curiosity_gap"].append(title[:60])

    return {
        "hook_counts": hook_counts,
        "examples": {k: v[:2] for k, v in example_titles.items()},
        "top_titles": top_titles[:5],
    }


def get_recent_titles(limit: int = 15) -> list:
    """Return the most recently uploaded video titles (for novelty checking)."""
    data = load_analytics()
    if not data:
        return []
    recent = sorted(data, key=lambda x: x.get("created_at", ""), reverse=True)
    return [e.get("title", "") for e in recent[:limit] if e.get("title")]


def get_performance_context() -> str:
    """
    Build a concise, prompt-injectable performance context string from real channel data.
    Tells the AI what hook types, niches, and title patterns are actually winning
    on THIS channel right now — not generic best practices.

    Returns an empty string if no analytics data exists yet (new channel).
    Used by ai_engine.generate_viral_idea() to bias idea generation toward
    proven patterns instead of generic viral formulas.
    """
    summary = get_performance_summary()
    if summary.get("total_videos", 0) == 0:
        return ""  # No data yet — don't inject empty context

    hooks = get_winning_hooks(top_n=10)
    top_titles = hooks.get("top_titles", [])
    best_niche = summary.get("best_niche", "")
    avg_views = summary.get("avg_views_per_video", 0)
    total_views = summary.get("total_views", 0)

    # Find the single most successful hook type from real data
    hook_counts = hooks.get("hook_counts", {})
    winning_hook = max(hook_counts, key=hook_counts.get) if hook_counts else "curiosity_gap"
    winning_hook_count = hook_counts.get(winning_hook, 0)

    # Find the single top-viewed video for reference
    top_videos = summary.get("top_videos", [])
    top_video = top_videos[0] if top_videos else None

    lines = [
        "CHANNEL PERFORMANCE CONTEXT (use this data to guide your output — this is what's working):",
        f"- Best performing niche on this channel: {best_niche}",
        f"- Channel average: {avg_views} views/video across {summary['total_videos']} uploads",
        f"- Winning hook type ({winning_hook_count} of top 10 videos): {winning_hook}",
    ]

    if top_video:
        lines.append(
            f"- Best single video: '{top_video.get('title', '')}' — {top_video.get('views', 0):,} views"
        )

    if top_titles:
        lines.append("- Top performing titles (copy their STYLE and specificity, NOT the topic):")
        for t in top_titles[:3]:
            lines.append(f"    * {t}")

    lines.append(
        "Use this data to make your output consistent with what this channel's audience responds to."
    )

    return "\n".join(lines)


def save_performance_snapshot():
    """
    Save a rolling performance snapshot after each batch run.
    Used by ai_engine.py to bias prompts toward winning patterns.
    """
    summary = get_performance_summary()
    hooks = get_winning_hooks()
    weights = compute_niche_weights()

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "niche_weights": weights,
        "hook_analysis": hooks,
        "summary": {
            "total_videos": summary.get("total_videos", 0),
            "total_views": summary.get("total_views", 0),
            "avg_views": summary.get("avg_views_per_video", 0),
            "best_niche": summary.get("best_niche", "unknown"),
        },
    }

    snapshot_file = str(LOGS_DIR / "performance_data.json")
    try:
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)
        log.info(f"Performance snapshot saved → {snapshot_file}")
    except Exception as e:
        log.error(f"Failed to save snapshot: {e}")


def generate_ai_feedback() -> str:
    """Generate AI-powered optimization feedback."""
    from modules.ai_engine import ask_ollama

    summary = get_performance_summary()
    if summary["total_videos"] == 0:
        return "No videos yet. Start creating to get feedback!"

    data = load_analytics()
    recent = data[-10:]  # Last 10 videos

    video_info = "\n".join([
        f"- {v.get('title', 'N/A')}: {v.get('views', 0)} views, niche: {v.get('niche', 'N/A')}"
        for v in recent
    ])

    prompt = f"""You are a YouTube Shorts analytics expert.

CHANNEL PERFORMANCE:
Total videos: {summary['total_videos']}
Total views: {summary['total_views']}
Average views/video: {summary['avg_views_per_video']}
Best niche: {summary['best_niche']}

RECENT VIDEOS:
{video_info}

NICHE PERFORMANCE:
{json.dumps(summary.get('niche_performance', {}), indent=2)}

Analyze this data and provide:
1. Which niche is working best and why
2. What type of hooks are getting most views
3. 3 specific recommendations to increase views
4. 5 new video ideas based on what's working

Be specific and actionable. Keep it concise."""

    feedback = ask_ollama(prompt)
    
    # Save feedback
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "feedback": feedback,
    }
    
    try:
        history = []
        if os.path.exists(PERFORMANCE_FILE):
            with open(PERFORMANCE_FILE, "r") as f:
                history = json.load(f)
        history.append(feedback_data)
        # Keep last 30 entries
        history = history[-30:]
        with open(PERFORMANCE_FILE, "w") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception:
        pass

    log.info("AI feedback generated")
    return feedback


if __name__ == "__main__":
    summary = get_performance_summary()
    print(json.dumps(summary, indent=2, default=str))
