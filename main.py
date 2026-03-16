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
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import NICHES, OUTPUT_DIR, VIDEOS_PER_DAY
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
from modules.analytics_engine import record_video, refresh_all_stats, generate_ai_feedback
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


def create_single_video(niche: dict = None, dry_run: bool = False) -> dict:
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
        "error": "",
    }

    try:
        # ── Step 0: Clean up ──
        clean_output_dir()

        # ── Step 1: Pick niche ──
        if niche is None:
            niche = random.choice(NICHES)
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
        idea = generate_viral_idea(trends, niche)
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
        quality = validate_script(script)
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
            log.info("Uploading to YouTube...")
            video_id = upload_video(
                video_path=video_path,
                title=seo.get("title", idea),
                description=seo.get("description", ""),
                tags=seo.get("tags", []),
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


def run_daily_batch(count: int = None, dry_run: bool = False):
    """
    Run a batch of video creations.
    Rotates through niches.
    """
    count = count or VIDEOS_PER_DAY
    log.info(f"Starting daily batch: {count} videos")
    log.info(f"Dry run: {dry_run}")

    results = []
    for i in range(count):
        niche = NICHES[i % len(NICHES)]
        log.info(f"\n{'#'*60}")
        log.info(f"# VIDEO {i+1}/{count}")
        log.info(f"{'#'*60}")

        result = create_single_video(niche=niche, dry_run=dry_run)
        results.append(result)

        if result["success"]:
            log.info(f"Video {i+1} SUCCESS: {result['idea']}")
        else:
            log.error(f"Video {i+1} FAILED: {result['error']}")

        # Wait between videos
        if i < count - 1:
            wait = random.randint(30, 120)
            log.info(f"Waiting {wait}s before next video...")
            time.sleep(wait)

    # Summary
    success = sum(1 for r in results if r["success"])
    log.info(f"\n{'='*60}")
    log.info(f"BATCH COMPLETE: {success}/{count} videos created")
    log.info(f"{'='*60}")

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

    parser = argparse.ArgumentParser(description="YouTube Shorts Automation")
    parser.add_argument("--mode", choices=["single", "batch", "analytics", "test"],
                        default="single", help="Run mode")
    parser.add_argument("--count", type=int, default=1, help="Number of videos for batch mode")
    parser.add_argument("--dry-run", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--niche", type=int, default=None,
                        help="Niche index (0-4)")

    args = parser.parse_args()

    if args.mode == "single":
        niche = NICHES[args.niche] if args.niche is not None else None
        result = create_single_video(niche=niche, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, default=str))

    elif args.mode == "batch":
        results = run_daily_batch(count=args.count, dry_run=args.dry_run)
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            print(f"[{status}] {r.get('niche', 'N/A')}: {r.get('idea', r.get('error', 'N/A'))}")

    elif args.mode == "analytics":
        run_analytics_cycle()

    elif args.mode == "test":
        print("Running test (dry run, 1 video)...")
        result = create_single_video(dry_run=True)
        print(json.dumps(result, indent=2, default=str))
