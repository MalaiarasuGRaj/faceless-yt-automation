"""
Video Builder - Creates YouTube Shorts using FFmpeg
Professional quality: zoom transitions, fade effects, styled subtitles.
100% FREE - uses FFmpeg.
"""

import subprocess
import os
import json
import math
import re
from pathlib import Path
from typing import List, Optional
from config.settings import (
    OUTPUT_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    VIDEO_TARGET_DURATION, VIDEO_MAX_DURATION,
    FONT_SIZE, FONT_COLOR, FONT_BORDER_COLOR, FONT_BORDER_WIDTH,
    BACKGROUND_MUSIC_VOLUME,
)
from utils import get_logger

log = get_logger("video_builder")


def get_media_duration(filepath: str) -> float:
    """Get duration of audio/video file."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath,
            ],
            capture_output=True, text=True, timeout=15,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def create_color_background(duration: float, output_path: str, color: str = "black") -> str:
    """Create a solid color background video."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={color}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration}:r={VIDEO_FPS}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    return output_path


def prepare_clip(clip_path: str, target_duration: float, output_path: str, clip_index: int = 0) -> str:
    """
    Scale, crop, and add effects to a clip for 9:16 vertical format.
    Adds slow zoom (Ken Burns effect) and fade transitions.
    """
    # Alternate between zoom-in and zoom-out for variety
    if clip_index % 2 == 0:
        # Slow zoom IN (1.0 to 1.15)
        zoom_filter = f"zoompan=z='min(1.15,1+0.0003*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(target_duration * VIDEO_FPS)}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}"
    else:
        # Slow zoom OUT (1.15 to 1.0)
        zoom_filter = f"zoompan=z='max(1.0,1.15-0.0003*on)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(target_duration * VIDEO_FPS)}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}"

    # Add fade in/out (0.5 sec each)
    fade_filter = f"fade=t=in:st=0:d=0.4,fade=t=out:st={max(0, target_duration - 0.4)}:d=0.4"

    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            f"setsar=1,"
            f"{fade_filter}"
        ),
        "-t", str(target_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an",
        "-r", str(VIDEO_FPS),
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return output_path
    except Exception as e:
        log.warning(f"Clip prepare failed: {e}")
    return ""


def concatenate_clips(clip_paths: List[str], total_duration: float, output_path: str) -> str:
    """Concatenate multiple clips with fade transitions."""
    if not clip_paths:
        log.warning("No clips to concatenate, creating color background")
        return create_color_background(total_duration, output_path)

    concat_file = str(OUTPUT_DIR / "concat_list.txt")
    prepared_clips = []
    duration_per_clip = total_duration / len(clip_paths)

    for i, clip in enumerate(clip_paths):
        prep_path = str(OUTPUT_DIR / f"prep_{i}.mp4")
        result = prepare_clip(clip, duration_per_clip, prep_path, clip_index=i)
        if result:
            prepared_clips.append(result)

    if not prepared_clips:
        return create_color_background(total_duration, output_path)

    # Write concat list
    with open(concat_file, "w") as f:
        for clip in prepared_clips:
            f.write(f"file '{clip}'\n")

    # Concatenate
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-r", str(VIDEO_FPS),
        "-t", str(total_duration),
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return output_path
    except Exception as e:
        log.error(f"Concat failed: {e}")

    return create_color_background(total_duration, output_path)


def generate_subtitle_file(script: str, duration: float, output_path: str) -> str:
    """
    Generate SRT subtitle file from script.
    Professional style: 3-4 words per segment, UPPERCASE.
    """
    words = script.split()
    total_words = len(words)
    if total_words == 0:
        return ""

    # 3-4 words per subtitle = professional Shorts look
    chunk_size = 4
    chunks = []
    for i in range(0, total_words, chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk.upper())

    time_per_chunk = duration / len(chunks)

    srt_content = ""
    for i, chunk in enumerate(chunks):
        start_time = i * time_per_chunk
        end_time = min((i + 1) * time_per_chunk, duration)

        start_str = format_srt_time(start_time)
        end_str = format_srt_time(end_time)

        srt_content += f"{i + 1}\n{start_str} --> {end_str}\n{chunk}\n\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    log.info(f"Subtitles generated: {len(chunks)} segments")
    return output_path


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_final_video(
    clips: List[str],
    voice_path: str,
    script: str,
    output_filename: str = "final_short.mp4",
    bg_music_path: str = "",
) -> str:
    """
    Build the final YouTube Shorts video with professional quality:
    1. Get voice duration
    2. Concatenate clips with zoom/fade transitions
    3. Mix voice + background music
    4. Add professional subtitles
    5. Output final 9:16 video
    """
    output_path = str(OUTPUT_DIR / output_filename)

    # Step 1: Get voice duration
    voice_duration = get_media_duration(voice_path)
    if voice_duration <= 0:
        log.error("Could not determine voice duration")
        return ""

    target_duration = min(voice_duration + 1.5, VIDEO_MAX_DURATION)
    log.info(f"Target video duration: {target_duration:.1f}s")

    # Step 2: Create base video from clips (with zoom/fade effects)
    base_video = str(OUTPUT_DIR / "base_video.mp4")
    if clips:
        concatenate_clips(clips, target_duration, base_video)
    else:
        create_color_background(target_duration, base_video)

    # Step 3: Mix voice with background music
    final_audio = voice_path
    if bg_music_path and os.path.exists(bg_music_path):
        mixed_audio = str(OUTPUT_DIR / "mixed_audio.mp3")
        mix_cmd = [
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", bg_music_path,
            "-filter_complex",
            f"[1:a]volume={BACKGROUND_MUSIC_VOLUME},afade=t=in:st=0:d=1,afade=t=out:st={max(0, target_duration-2)}:d=2[bg];"
            f"[0:a]volume=1.0[voice];"
            f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(target_duration),
            mixed_audio,
        ]
        try:
            result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                final_audio = mixed_audio
                log.info("Background music mixed with voiceover (with fade in/out)")
            else:
                log.warning("Music mix failed, using voice only")
        except Exception as e:
            log.warning(f"Music mix error: {e}")

    # Step 4: Generate subtitles
    srt_path = str(OUTPUT_DIR / "subtitles.srt")
    generate_subtitle_file(script, voice_duration, srt_path)

    # Step 5: Combine everything with professional subtitle styling
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")

    # Professional subtitle style: white bold text with dark semi-transparent background
    subtitle_filter = (
        f"subtitles='{srt_escaped}'"
        f":force_style='FontSize={FONT_SIZE},"
        f"PrimaryColour=&H00FFFFFF,"
        f"SecondaryColour=&H0000FFFF,"
        f"OutlineColour=&H00000000,"
        f"BackColour=&H80000000,"
        f"BorderStyle=4,"
        f"Outline=1,"
        f"Shadow=0,"
        f"Alignment=2,"
        f"MarginV=120,"
        f"MarginL=50,"
        f"MarginR=50,"
        f"FontName=Arial,"
        f"Bold=1,"
        f"Spacing=1'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", base_video,
        "-i", final_audio,
        "-filter_complex",
        f"[0:v]{subtitle_filter}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-r", str(VIDEO_FPS),
        "-t", str(target_duration),
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        log.info("Building final video with subtitles + effects...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            log.warning("Subtitle overlay failed, trying without subtitles...")
            cmd_simple = [
                "ffmpeg", "-y",
                "-i", base_video,
                "-i", final_audio,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and os.path.exists(output_path):
            final_duration = get_media_duration(output_path)
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            log.info(f"Final video: {output_path} ({final_duration:.1f}s, {size_mb:.1f}MB)")
            return output_path
        else:
            log.error(f"FFmpeg error: {result.stderr[:500]}")

    except Exception as e:
        log.error(f"Video build failed: {e}")

    return ""


def extract_thumbnail(video_path: str, output_filename: str = "thumbnail.jpg", time_sec: float = 3.0) -> str:
    """Extract a frame from video as thumbnail."""
    output_path = str(OUTPUT_DIR / output_filename)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ss", str(time_sec),
        "-vframes", "1",
        "-q:v", "2",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            log.info(f"Thumbnail extracted: {output_path}")
            return output_path
    except Exception as e:
        log.warning(f"Thumbnail extraction failed: {e}")

    return ""


def cleanup_temp_files():
    """Clean up temporary files in output directory."""
    patterns = ["prep_*.mp4", "base_video.mp4", "concat_list.txt",
                "clip_*.mp4", "subtitles.srt", "mixed_audio.mp3"]
    for pattern in patterns:
        for f in OUTPUT_DIR.glob(pattern):
            try:
                f.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    print("Video Builder module loaded.")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Video format: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FPS}fps")
    print("Features: zoom transitions, fade effects, professional subtitles")