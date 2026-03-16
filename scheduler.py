"""
Scheduler - Runs the automation pipeline on a schedule.
No n8n needed! This runs directly on your computer.

Usage:
    python scheduler.py              # Run every 6 hours
    python scheduler.py --interval 4 # Run every 4 hours
    python scheduler.py --once       # Run once and exit
"""

import time
import sys
import signal
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import SCHEDULE_INTERVAL_HOURS, VIDEOS_PER_DAY, UPLOAD_HOUR_START, UPLOAD_HOUR_END
from main import create_single_video, run_analytics_cycle
from config.settings import NICHES
from utils import get_logger

log = get_logger("scheduler")

running = True


def signal_handler(sig, frame):
    global running
    log.info("Shutdown signal received. Stopping scheduler...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_upload_window() -> bool:
    """Check if current time is within upload window."""
    hour = datetime.now().hour
    return UPLOAD_HOUR_START <= hour <= UPLOAD_HOUR_END


def run_scheduler(interval_hours: int = None, dry_run: bool = False):
    """
    Main scheduler loop.
    Runs video creation at regular intervals.
    """
    interval = interval_hours or SCHEDULE_INTERVAL_HOURS
    video_count = 0
    niche_index = 0

    log.info(f"{'='*60}")
    log.info(f"YouTube Shorts Automation Scheduler Started")
    log.info(f"Interval: every {interval} hours")
    log.info(f"Upload window: {UPLOAD_HOUR_START}:00 - {UPLOAD_HOUR_END}:00")
    log.info(f"Dry run: {dry_run}")
    log.info(f"{'='*60}")

    while running:
        now = datetime.now()

        if is_upload_window():
            log.info(f"\n{'='*60}")
            log.info(f"Starting video creation at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            log.info(f"{'='*60}")

            # Pick niche (rotate through them)
            niche = NICHES[niche_index % len(NICHES)]
            niche_index += 1

            result = create_single_video(niche=niche, dry_run=dry_run)

            if result["success"]:
                video_count += 1
                log.info(f"Video #{video_count} created successfully!")
            else:
                log.error(f"Video creation failed: {result.get('error', 'unknown')}")

            # Run analytics every 4 videos
            if video_count > 0 and video_count % 4 == 0:
                log.info("Running analytics cycle...")
                try:
                    run_analytics_cycle()
                except Exception as e:
                    log.warning(f"Analytics cycle failed: {e}")

        else:
            log.info(f"Outside upload window ({UPLOAD_HOUR_START}:00-{UPLOAD_HOUR_END}:00). Waiting...")

        # Wait for next cycle
        next_run = now + timedelta(hours=interval)
        log.info(f"Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        log.info(f"Total videos created today: {video_count}")

        # Sleep in small chunks so we can respond to signals
        wait_seconds = interval * 3600
        for _ in range(wait_seconds):
            if not running:
                break
            time.sleep(1)

    log.info(f"Scheduler stopped. Total videos created: {video_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Automation Scheduler")
    parser.add_argument("--interval", type=int, default=None,
                        help=f"Hours between runs (default: {SCHEDULE_INTERVAL_HOURS})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip YouTube upload")
    parser.add_argument("--once", action="store_true",
                        help="Run once and exit")
    parser.add_argument("--multi-channel", action="store_true",
                        help="Run for all enabled channels (see config/channels.json)")

    args = parser.parse_args()

    if args.multi_channel:
        from modules.multi_channel import run_multi_channel_batch, init_channels_config
        init_channels_config()
        if args.once:
            results = run_multi_channel_batch(dry_run=args.dry_run)
            for r in results:
                status = "OK" if r["success"] else "FAIL"
                print(f"[{status}] {r.get('channel', 'N/A')}: {r.get('idea', r.get('error', ''))}")
        else:
            log.info("Multi-channel scheduler started")
            while running:
                results = run_multi_channel_batch(dry_run=args.dry_run)
                success = sum(1 for r in results if r["success"])
                log.info(f"Multi-channel batch: {success}/{len(results)} videos")
                wait_seconds = (args.interval or SCHEDULE_INTERVAL_HOURS) * 3600
                for _ in range(wait_seconds):
                    if not running:
                        break
                    time.sleep(1)
    elif args.once:
        from main import create_single_video
        result = create_single_video(dry_run=args.dry_run)
        status = "SUCCESS" if result["success"] else "FAILED"
        print(f"\n{status}: {result.get('idea', result.get('error', 'N/A'))}")
    else:
        run_scheduler(interval_hours=args.interval, dry_run=args.dry_run)
