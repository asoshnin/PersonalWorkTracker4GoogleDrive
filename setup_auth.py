import argparse
import os
from pathlib import Path
import yaml

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.activity.readonly",
]

def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    parser = argparse.ArgumentParser(description="Authenticate Personal Work Summarizer with Google Drive")
    parser.add_argument("--config", type=str, default="pa_config.yaml", help="Path to YAML configuration file")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Authentication failed: Config file not found: {config_path}")
        return

    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ Authentication failed: Could not parse config file: {e}")
        return

    credentials_path = raw.get("google_credentials_path")
    token_path = raw.get("token_path", "token.json")

    if not credentials_path:
        print("❌ Authentication failed: google_credentials_path not found in config")
        return

    if not os.path.exists(credentials_path):
        print(f"❌ Authentication failed: Credentials file not found at {credentials_path}")
        return

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, DRIVE_SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return

        try:
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
        except Exception as e:
            print(f"❌ Authentication failed saving token: {e}")
            return
            
    print(f"✅ Authentication complete. Token saved to: {token_path}")

if __name__ == "__main__":
    main()
