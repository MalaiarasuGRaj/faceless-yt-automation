"""
YouTube Authentication Script
Run this on your local machine to generate 'config/youtube_token.json'.
This allows the automation system to upload videos without a browser.
"""

import os
import sys
from pathlib import Path

# Add project root to path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from config.settings import YOUTUBE_CLIENT_SECRET_FILE, YOUTUBE_TOKEN_FILE
except ImportError:
    print("Error: Missing required packages. Please run:")
    print("pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

# Scopes required for uploading to YouTube
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def authenticate():
    print("=== YouTube Authentication Setup ===")
    
    if not os.path.exists(YOUTUBE_CLIENT_SECRET_FILE):
        print(f"Error: '{YOUTUBE_CLIENT_SECRET_FILE}' not found.")
        print("Please download it from Google Cloud Console and place it in the 'config' folder.")
        return

    print(f"Loading client secrets from: {YOUTUBE_CLIENT_SECRET_FILE}")
    
    try:
        # Create the flow using the client secrets file
        flow = InstalledAppFlow.from_client_secrets_file(
            YOUTUBE_CLIENT_SECRET_FILE, SCOPES
        )
        
        # Run the local server for the OAuth flow
        # This will open a browser window for login
        print("Opening browser for authentication...")
        creds = flow.run_local_server(port=0)
        
        # Save the credentials to the token file in JSON format
        print(f"Saving token to: {YOUTUBE_TOKEN_FILE}")
        with open(YOUTUBE_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
            
        print("\nSUCCESS: YouTube authentication complete!")
        print(f"Token saved to {YOUTUBE_TOKEN_FILE}")
        print("You can now run the automation system.")
        
    except Exception as e:
        print(f"\nERROR: Authentication failed: {e}")

if __name__ == "__main__":
    authenticate()
