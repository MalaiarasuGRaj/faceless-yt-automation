"""
YouTube Uploader
Uploads videos to YouTube using the Data API v3.
FREE: 10,000 API units/day (enough for ~6 uploads/day).

SETUP:
1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create OAuth 2.0 credentials (Desktop application)
5. Download client_secret.json → put in config/ folder
6. First run will open browser for authentication
"""

import os
import json
import pickle
from pathlib import Path
from typing import Optional
from config.settings import YOUTUBE_CLIENT_SECRET_FILE, YOUTUBE_TOKEN_FILE, OUTPUT_DIR
from utils import get_logger

log = get_logger("youtube")


def get_authenticated_service():
    """Get authenticated YouTube service."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        log.error(
            "Missing packages. Run:\n"
            "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
        return None

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
              "https://www.googleapis.com/auth/youtube"]

    creds = None

    # Load saved token
    if os.path.exists(YOUTUBE_TOKEN_FILE):
        try:
            with open(YOUTUBE_TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)
        except Exception:
            pass

    # If no valid token, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(YOUTUBE_CLIENT_SECRET_FILE):
                log.error(
                    f"client_secret.json not found at {YOUTUBE_CLIENT_SECRET_FILE}\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials"
                )
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=8090)

        # Save token
        with open(YOUTUBE_TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list = None,
    category_id: str = "28",  # 28 = Science & Technology
    privacy: str = "public",
    is_short: bool = True,
) -> Optional[str]:
    """
    Upload a video to YouTube.
    Returns the video ID if successful.
    """
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    youtube = get_authenticated_service()
    if not youtube:
        return None

    if not os.path.exists(video_path):
        log.error(f"Video file not found: {video_path}")
        return None

    # Ensure #Shorts in title/description for Shorts
    if is_short:
        if "#Shorts" not in title:
            title = f"{title} #Shorts"
        if "#Shorts" not in description:
            description = f"{description}\n\n#Shorts"

    tags = tags or ["shorts", "viral", "facts"]

    body = {
        "snippet": {
            "title": title[:100],  # YouTube limit
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,  # 1MB chunks
    )

    try:
        log.info(f"Uploading: {title}")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id", "")
        log.info(f"Upload complete! Video ID: {video_id}")
        log.info(f"URL: https://youtube.com/shorts/{video_id}")

        return video_id

    except HttpError as e:
        log.error(f"YouTube API error: {e}")
    except Exception as e:
        log.error(f"Upload failed: {e}")

    return None


def set_thumbnail(video_id: str, thumbnail_path: str) -> bool:
    """Set custom thumbnail for a video."""
    from googleapiclient.http import MediaFileUpload

    youtube = get_authenticated_service()
    if not youtube or not os.path.exists(thumbnail_path):
        return False

    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path),
        ).execute()
        log.info(f"Thumbnail set for video {video_id}")
        return True
    except Exception as e:
        log.warning(f"Thumbnail set failed: {e}")
        return False


def get_channel_analytics() -> dict:
    """Fetch basic channel stats."""
    youtube = get_authenticated_service()
    if not youtube:
        return {}

    try:
        request = youtube.channels().list(
            part="statistics,snippet",
            mine=True,
        )
        response = request.execute()

        if response.get("items"):
            channel = response["items"][0]
            stats = channel.get("statistics", {})
            return {
                "channel_name": channel.get("snippet", {}).get("title", ""),
                "subscribers": stats.get("subscriberCount", 0),
                "total_views": stats.get("viewCount", 0),
                "video_count": stats.get("videoCount", 0),
            }
    except Exception as e:
        log.warning(f"Analytics fetch failed: {e}")

    return {}


if __name__ == "__main__":
    print("YouTube Uploader module loaded.")
    print(f"Client secret: {YOUTUBE_CLIENT_SECRET_FILE}")
    print(f"Token file: {YOUTUBE_TOKEN_FILE}")
