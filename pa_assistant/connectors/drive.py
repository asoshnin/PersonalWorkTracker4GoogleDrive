from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import List, Optional, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..models import ActivityEntry, Platform

logger = logging.getLogger(__name__)


DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.activity.readonly",
]


def fetch_drive_activities(
    start: datetime,
    end: datetime,
    config: Any,
    page_size: int = 100,
) -> List[ActivityEntry]:
    """
    Fetch Google Drive file modification activities for a single account.

    Notes
    -----
    - This implementation uses OAuth 2.0 installed-app credentials
      and maintains a refreshable token at `token_path`.
    """
    credentials_path = str(config.google_credentials_path) if config.google_credentials_path else None
    token_path = str(getattr(config, "token_path", "token.json")) if getattr(config, "token_path", None) else "token.json"

    if not credentials_path:
        logger.warning("No Google credentials path provided; skipping Drive.")
        return []

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, DRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:
                logger.error("Failed to refresh token: %s", exc)
                creds = None
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, DRIVE_SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as exc:
                logger.error("Failed to run OAuth flow: %s", exc)
                return []
        
        try:
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
        except Exception as exc:
            logger.error("Failed to save token to %s: %s", token_path, exc)

    try:
        driveactivity_service = build("driveactivity", "v2", credentials=creds)
    except Exception as exc:
        logger.error("Failed to build Drive Activity service: %s", exc)
        return []

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    
    request_body = {
        "filter": f"time >= {start_ms} AND time <= {end_ms}",
        "pageSize": page_size
    }

    activities: List[ActivityEntry] = []

    try:
        results = driveactivity_service.activity().query(body=request_body).execute()
        drive_activities = results.get("activities", [])
    except Exception as exc:
        logger.error("Error querying Drive Activity API: %s", exc)
        return []

    for activity in drive_activities:
        try:
            if "timestamp" in activity:
                ts_str = activity["timestamp"]
            elif "timeRange" in activity:
                ts_str = activity["timeRange"].get("endTime")
            else:
                continue
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (KeyError, ValueError, AttributeError):
            continue

        primary_action = activity.get("primaryActionDetail", {})
        action_type = "EDIT"
        for key in ["edit", "create", "comment", "rename", "move", "delete", "restore"]:
            if key in primary_action:
                action_type = key.upper()
                break

        targets = activity.get("targets", [])
        if not targets:
            continue
            
        drive_item = targets[0].get("driveItem")
        if not drive_item:
            continue
            
        file_id_full = drive_item.get("name", "")
        file_id = file_id_full.replace("items/", "") if file_id_full else ""
        
        file_title = drive_item.get("title", "Untitled")
        mime_type = drive_item.get("mimeType", "")
        
        link = f"https://drive.google.com/file/d/{file_id}/view" if file_id else ""
        action_verbs = {
            "EDIT": "Edited",
            "CREATE": "Created",
            "COMMENT": "Commented on",
            "RENAME": "Renamed",
            "MOVE": "Moved",
            "DELETE": "Deleted",
            "RESTORE": "Restored"
        }
        verb = action_verbs.get(action_type, action_type.capitalize())
        description = f"{verb}: {file_title}"

        activities.append(
            ActivityEntry(
                timestamp=ts,
                platform=Platform.DRIVE,
                description=description,
                file_links=[link] if link else [],
                comments=f"Type: {mime_type}" if mime_type else "Type: unknown",
                metadata={"mimeType": mime_type, "id": file_id},
                action_type=action_type
            )
        )

    logger.info("Loaded %d Drive activities from API", len(activities))
    return activities

