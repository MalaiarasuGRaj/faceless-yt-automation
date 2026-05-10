"""
╔══════════════════════════════════════════════════════════════╗
║  YouTube Shorts Automation - Main Pipeline Runner           ║
║  Runs the complete automation: Trend → Script → Video → Upload  ║
║  100% FREE tools only                                       ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import NICHES, OUTPUT_DIR, VIDEOS_PER_DAY, SCHEDULED_PUBLISH_HOURS_IST
from modules.trend_scraper import get_all_trends
from modules.ai_engine import (
    generate_viral_idea,
    generate_script,
    optimize_hook,
    generate_seo,
    generate_search_keywords,
)
from modules.voice_generator import generate_voice
from modules.footage_fetcher import fetch_footage_for_keywords
from modules.video_builder import build_final_video, extract_thumbnail, cleanup_temp_files
from modules.youtube_upload import upload_video, set_thumbnail
from modules.analytics_engine import (
    record_video, refresh_all_stats, generate_ai_feedback,
    compute_niche_weights, get_winning_hooks, get_recent_titles, save_performance_snapshot,
)
from modules.script_quality import validate_script, improve_script
from modules.music_manager import get_background_music
from utils import get_logger

log = get_logger("main")


def clean_output_dir():
    """Remove previous temp files from output directory."""
    cleanup_temp_files()
    for ext in ["*.mp3", "*.wav"]:
        for f in OUTPUT_DIR.glob(ext):
            try:
                f.unlink()
            except Exception:
                pass


def pick_niche_by_weight() -> dict:
    """
    Pick a niche using analytics-driven weights.
    Higher weight = picked more often. Falls back to random if weights unavailable.
    """
    try:
        weights = compute_niche_weights()
        niche_names = [n["name"] for n in NICHES]
        niche_weights = [weights.get(n["name"], 1.0) for n in NICHES]
        chosen = random.choices(NICHES, weights=niche_weights, k=1)[0]
        log.info(f"Niche selected by weight: {chosen['name']} (weight={weights.get(chosen['name'], 1.0):.2f})")
        return chosen
    except Exception as e:
        log.warning(f"Weighted niche selection failed ({e}), falling back to random")
        return random.choice(NICHES)


def get_publish_schedule(count: int) -> list:
    """
    Generate UTC publish timestamps for 'count' videos.
    Uses SCHEDULED_PUBLISH_HOURS_IST from settings (e.g. [8, 13, 18, 21]).
    
    If the first scheduled time has already passed today, shifts to tomorrow.
    YouTube requires publishAt to be at least 5 minutes in the future.
    
    Returns:
        List of ISO 8601 UTC strings like "2026-04-27T02:30:00Z"
    """
    IST_OFFSET = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(IST_OFFSET)
    
    schedules = []
    hours = SCHEDULED_PUBLISH_HOURS_IST[:count]  # Take only as many as needed
    
    for i, hour in enumerate(hours):
        # Build target datetime in IST
        target_ist = now_ist.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # If time has already passed today (or within 10 minutes), move to next day
        if target_ist <= now_ist + timedelta(minutes=10):
            target_ist = target_ist + timedelta(days=1)
        
        # Convert to UTC for the API
        target_utc = target_ist.astimezone(timezone.utc)
        schedules.append(target_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    return schedules


def create_single_video(niche: dict = None, dry_run: bool = False,
                        publish_at: str = None, recent_titles: list = None) -> dict:
    """
    Create a single YouTube Short - full pipeline.
    
    Args:
        niche: Content niche config dict. If None, picks randomly.
        dry_run: If True, does everything except upload.
    
    Returns:
        dict with video info and status.
    """
    result = {
        "success": False,
        "niche": "",
        "idea": "",
        "video_path": "",
        "video_id": "",
        "publish_at": publish_at or "immediate",
        "error": "",
    }

    try:
        # ── Step 0: Clean up ──
        clean_output_dir()

        # ── Step 1: Pick niche ──
        if niche is None:
            niche = pick_niche_by_weight()
        result["niche"] = niche["name"]
        log.info(f"{'='*60}")
        log.info(f"NICHE: {niche['name']}")
        log.info(f"{'='*60}")

        # ── Step 2: Discover trends ──
        log.info("Step 1/8: Discovering trends...")
        trends = get_all_trends(subreddits=niche.get("subreddits", []))
        if not trends:
            log.warning("No trends found, using niche keywords as fallback")
            trends = [{"title": kw, "score": 50} for kw in niche["keywords"]]

        # ── Step 3: Generate viral idea ──
        log.info("Step 2/8: Generating viral idea...")
        idea = generate_viral_idea(trends, niche, recent_titles=recent_titles)
        if not idea:
            result["error"] = "Failed to generate idea"
            return result
        result["idea"] = idea
        log.info(f"Idea: {idea}")

        # ── Step 4: Generate script ──
        log.info("Step 3/8: Generating script...")
        script = generate_script(idea)
        if not script or len(script) < 20:
            result["error"] = "Failed to generate script"
            return result

        # ── Step 5: Optimize hook ──
        log.info("Step 4/9: Optimizing hook...")
        script = optimize_hook(script)
        log.info(f"Script ({len(script.split())} words): {script[:150]}...")

        # ── Step 5b: Quality check ──
        log.info("Step 5/9: Quality checking script...")
        quality = validate_script(script, title=seo.get("title", "") if 'seo' in dir() else "",
                                  recent_titles=recent_titles)
        if not quality["approved"]:
            log.warning(f"Script quality low ({quality['score']}%), improving...")
            issues = [c["message"] for c in quality["checks"].values() if not c["pass"]]
            script = improve_script(script, issues)
            log.info(f"Script improved. Re-checking...")
            quality = validate_script(script)
        log.info(f"Script quality: {quality['score']}%")

        # ── Step 6: Generate SEO ──
        log.info("Step 6/10: Generating SEO metadata...")
        seo = generate_seo(idea, script)

        # ── Step 7: Generate voice ──
        log.info("Step 7/10: Generating voiceover...")
        voice_path = generate_voice(script, "voice.mp3")
        if not voice_path:
            result["error"] = "Failed to generate voice"
            return result

        # ── Step 8: Fetch stock footage ──
        log.info("Step 8/10: Fetching stock footage...")
        keywords = generate_search_keywords(script)
        clips = fetch_footage_for_keywords(keywords, clips_per_keyword=1)

        # ── Step 8b: Get background music ──
        bg_music = get_background_music()
        if bg_music:
            log.info(f"Background music: {bg_music}")

        # ── Step 9: Build video ──
        log.info("Step 9/10: Building final video...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"short_{timestamp}.mp4"
        video_path = build_final_video(clips, voice_path, script, video_filename, bg_music_path=bg_music)

        if not video_path:
            result["error"] = "Failed to build video"
            return result

        result["video_path"] = video_path

        # ── Step 10: Extract thumbnail ──
        thumb_path = extract_thumbnail(video_path, f"thumb_{timestamp}.jpg")

        # ── Step 10b: Upload ──
        if dry_run:
            log.info("DRY RUN - Skipping upload")
            result["success"] = True
            result["video_id"] = "DRY_RUN"
        else:
            if publish_at:
                log.info(f"Uploading as SCHEDULED (publishes at {publish_at} UTC)...")
            else:
                log.info("Uploading to YouTube as PUBLIC immediately...")

            video_id = upload_video(
                video_path=video_path,
                title=seo.get("title", idea),
                description=seo.get("description", ""),
                tags=seo.get("tags", []),
                publish_at=publish_at,  # None = go live immediately
            )

            if video_id:
                result["video_id"] = video_id
                result["success"] = True

                # Set thumbnail
                if thumb_path:
                    set_thumbnail(video_id, thumb_path)

                # Record in analytics
                record_video(
                    video_id=video_id,
                    title=seo.get("title", idea),
                    idea=idea,
                    niche=niche["name"],
                    script=script,
                    seo_data=seo,
                )

                log.info(f"SUCCESS! Video uploaded: https://youtube.com/shorts/{video_id}")
            else:
                result["error"] = "Upload failed"

    except Exception as e:
        log.error(f"Pipeline error: {e}", exc_info=True)
        result["error"] = str(e)

    finally:
        # Cleanup temp files
        cleanup_temp_files()

    return result


def run_daily_batch(count: int = None, dry_run: bool = False, schedule: bool = True):
    """
    ╔══════════════════════════════════════════════════════════════╗
    ║  BATCH + SCHEDULE MODE                                       ║
    ║  Creates ALL videos in one run, uploads them as SCHEDULED.   ║
    ║  YouTube auto-publishes at the configured times.             ║
    ║  Laptop only needs to be ON during this script run.          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    count = count or VIDEOS_PER_DAY
    log.info(f"{'='*60}")
    log.info(f"BATCH MODE: {count} videos | Schedule: {schedule} | Dry run: {dry_run}")
    log.info(f"{'='*60}")

    # ── Phase 6: Auto-refresh YouTube stats before generating ideas ──
    # This ensures the analytics feedback loop has fresh data so the AI
    # knows which niches and hook types are winning right now.
    log.info("Refreshing channel stats (for AI feedback loop)...")
    try:
        refresh_all_stats()
        log.info("✅ Stats refreshed — AI will use latest performance data")
    except Exception as e:
        log.warning(f"Stats refresh skipped ({e}) — continuing with cached data")

    # ── Pre-fetch shared resources for all videos ──
    log.info("Pre-fetching trends (shared across all videos)...")
    trends = get_all_trends()
    if not trends:
        log.warning("No trends found, will use niche keywords as fallback per video")

    # ── Load recent titles for novelty checking ──
    recent_titles = get_recent_titles(limit=15)
    if recent_titles:
        log.info(f"Loaded {len(recent_titles)} recent titles for novelty check")

    # ── Generate publish schedule ──
    if schedule and not dry_run:
        publish_times = get_publish_schedule(count)
        log.info(f"Scheduled publish times (UTC):")
        for i, t in enumerate(publish_times):
            # Display in IST for readability
            from datetime import datetime, timezone, timedelta
            IST = timezone(timedelta(hours=5, minutes=30))
            utc_dt = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            ist_dt = utc_dt.astimezone(IST)
            log.info(f"  Video {i+1}: {ist_dt.strftime('%Y-%m-%d %I:%M %p IST')} ({t} UTC)")
    else:
        publish_times = [None] * count  # Upload immediately

    # ── Create all videos ──
    results = []
    for i in range(count):
        log.info(f"\n{'#'*60}")
        log.info(f"# VIDEO {i+1}/{count}")
        log.info(f"{'#'*60}")

        result = create_single_video(
            niche=None,              # pick_niche_by_weight() is called inside
            dry_run=dry_run,
            publish_at=publish_times[i],
            recent_titles=recent_titles,
        )
        results.append(result)

        # Add successful title to recent_titles so next video avoids it
        if result["success"] and result.get("idea"):
            recent_titles.insert(0, result.get("idea", ""))

        if result["success"]:
            scheduled_info = f" → publishes at {publish_times[i]}" if publish_times[i] else " → live immediately"
            log.info(f"Video {i+1} ✅ SUCCESS: {result['idea']}{scheduled_info}")
        else:
            log.error(f"Video {i+1} ❌ FAILED: {result['error']}")

    # ── Summary ──
    success = sum(1 for r in results if r["success"])
    log.info(f"\n{'='*60}")
    log.info(f"BATCH COMPLETE: {success}/{count} videos created & uploaded")

    if schedule and not dry_run and success > 0:
        log.info(f"\n📅 SCHEDULED VIDEOS:")
        for i, r in enumerate(results):
            if r["success"] and publish_times[i]:
                from datetime import datetime, timezone, timedelta
                IST = timezone(timedelta(hours=5, minutes=30))
                utc_dt = datetime.strptime(publish_times[i], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                ist_dt = utc_dt.astimezone(IST)
                log.info(f"  ✅ {r.get('idea', 'N/A')[:50]}")
                log.info(f"     → Auto-publishes: {ist_dt.strftime('%Y-%m-%d %I:%M %p IST')}")
        log.info("\n💡 Laptop can be turned off now. YouTube will publish automatically.")

    log.info(f"{'='*60}")

    # ── Save performance snapshot for future AI learning ──
    try:
        save_performance_snapshot()
        log.info("Performance snapshot saved for AI optimization")
    except Exception as e:
        log.warning(f"Snapshot save failed: {e}")

    return results


def run_analytics_cycle():
    """Run analytics refresh and get AI feedback."""
    log.info("Running analytics cycle...")
    refresh_all_stats()
    feedback = generate_ai_feedback()
    if feedback:
        log.info(f"AI Feedback:\n{feedback}")
    return feedback


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="YouTube Shorts Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode batch --count 4          # Create 4 videos, schedule on YouTube
  python main.py --mode batch --count 4 --dry-run  # Test without uploading
  python main.py --mode batch --no-schedule      # Upload all 4 immediately (old behaviour)
  python main.py --mode single                   # Create 1 video and upload now
  python main.py --mode analytics                # Refresh stats + AI feedback
"""
    )
    parser.add_argument("--mode", choices=["single", "batch", "analytics", "test"],
                        default="single", help="Run mode")
    parser.add_argument("--count", type=int, default=VIDEOS_PER_DAY,
                        help=f"Number of videos for batch mode (default: {VIDEOS_PER_DAY})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Create videos but skip YouTube upload")
    parser.add_argument("--no-schedule", action="store_true",
                        help="Upload immediately instead of scheduling (batch mode only)")
    parser.add_argument("--niche", type=int, default=None,
                        help=f"Niche index 0-{len(NICHES)-1} (default: auto-weighted)")

    args = parser.parse_args()

    if args.mode == "single":
        niche = NICHES[args.niche] if args.niche is not None else None
        result = create_single_video(niche=niche, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))

    elif args.mode == "batch":
        use_schedule = not args.no_schedule
        results = run_daily_batch(
            count=args.count,
            dry_run=args.dry_run,
            schedule=use_schedule,
        )
        print(f"\n{'='*60}")
        for r in results:
            status = "✅ OK" if r["success"] else "❌ FAIL"
            sched = f" | publishes: {r.get('publish_at', 'immediate')}" if r["success"] else ""
            print(f"[{status}] [{r.get('niche', 'N/A')}] {r.get('idea', r.get('error', 'N/A'))}{sched}")

    elif args.mode == "analytics":
        run_analytics_cycle()

    elif args.mode == "test":
        print("Running test (dry run, 1 video)...")
        result = create_single_video(dry_run=True)
        print(json.dumps(result, indent=2, default=str))
