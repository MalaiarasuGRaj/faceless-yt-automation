"""
Voice Generator - Using edge-tts (100% FREE)
Microsoft Edge Text-to-Speech - high quality, no API key needed.
Install: pip install edge-tts
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
from config.settings import VOICE_NAME, OUTPUT_DIR
from utils import get_logger

log = get_logger("voice_gen")


async def _generate_voice_async(text: str, output_path: str, voice: str = None):
    """Internal async voice generation."""
    import edge_tts

    voice = voice or VOICE_NAME
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_voice(script: str, output_filename: str = "voice.mp3") -> str:
    """
    Generate voice from script text.
    Returns path to the generated audio file.
    """
    output_path = str(OUTPUT_DIR / output_filename)

    log.info(f"Generating voice with {VOICE_NAME}...")
    log.info(f"Script length: {len(script)} chars, {len(script.split())} words")

    try:
        asyncio.run(_generate_voice_async(script, output_path))
        log.info(f"Voice saved: {output_path}")

        # Get duration using ffprobe
        duration = get_audio_duration(output_path)
        if duration:
            log.info(f"Audio duration: {duration:.1f} seconds")

        return output_path

    except ImportError:
        log.error("edge-tts not installed. Run: pip install edge-tts")
        return ""
    except Exception as e:
        log.error(f"Voice generation failed: {e}")
        return ""


def get_audio_duration(filepath: str) -> float:
    """Get audio duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def list_available_voices():
    """List all available edge-tts voices."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "edge_tts", "--list-voices"],
            capture_output=True, text=True, timeout=30
        )
        print(result.stdout)
    except Exception as e:
        print(f"Error listing voices: {e}")


if __name__ == "__main__":
    test_text = "This AI just replaced 1000 employees overnight. And nobody even noticed."
    path = generate_voice(test_text, "test_voice.mp3")
    if path:
        print(f"Voice generated: {path}")
    else:
        print("Voice generation failed. Make sure edge-tts is installed.")
