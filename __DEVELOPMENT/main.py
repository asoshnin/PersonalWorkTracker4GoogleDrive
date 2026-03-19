#!/usr/bin/env python3
"""
Personal Work Summarizer - Main Entry Point

This module provides the main functionality for aggregating user activity
across Google Gemini, Perplexity, and Google Cloud platforms into a unified
Markdown-formatted temporal log.

Usage:
    python main.py --start-date 2024-03-01 --end-date 2024-03-15 --output summary.md

Author: Multi-Agent Pipeline
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported platforms for activity aggregation."""
    GEMINI = "Gemini"
    PERPLEXITY = "Perplexity"
    GOOGLE_CLOUD = "Google Cloud"


@dataclass
class ActivityEntry:
    """Represents a single activity entry from any platform."""
    timestamp: datetime
    platform: Platform
    work_done: str
    file_links: List[str] = field(default_factory=list)
    comments: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown_row(self) -> str:
        """Convert activity entry to a Markdown table row."""
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        file_links_str = ", ".join(self.file_links) if self.file_links else "-"
        return f"| {timestamp_str} | {self.platform.value} | {self.work_done} | {file_links_str} | {self.comments} |"


@dataclass
class AggregationConfig:
    """Configuration for activity aggregation."""
    start_date: datetime
    end_date: datetime
    output_file: str = "summary.md"
    include_gemini: bool = True
    include_perplexity: bool = True
    include_google_cloud: bool = True
    api_key_gemini: Optional[str] = None
    api_key_perplexity: Optional[str] = None
    google_credentials_path: Optional[str] = None


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1"

    def __init__(self, api_key: str):
        """Initialize Gemini client with API key."""
        self.api_key = api_key
        self.headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }
        self._activities: List[ActivityEntry] = []

    async def fetch_activities(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ActivityEntry]:
        """
        Fetch activities from Gemini for the specified date range.

        Note: Gemini API doesn't provide direct chat history access.
        This implementation assumes local conversation logging.
        """
        logger.info(f"Fetching Gemini activities from {start_date} to {end_date}")

        try:
            # Check for local conversation log
            log_path = Path.home() / ".personal-summarizer" / "gemini_history.json"
            
            if log_path.exists():
                with open(log_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                            
                            if start_date <= timestamp <= end_date:
                                entry = ActivityEntry(
                                    timestamp=timestamp,
                                    platform=Platform.GEMINI,
                                    work_done=data.get("prompt", "AI Query")[:500],
                                    file_links=data.get("files", []),
                                    comments=f"Model: {data.get('model', 'unknown')}",
                                    metadata={"model": data.get("model")}
                                )
                                self._activities.append(entry)
            
            logger.info(f"Found {len(self._activities)} Gemini activities")
            return self._activities

        except Exception as e:
            logger.error(f"Error fetching Gemini activities: {e}")
            return []

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Gemini models."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("models", [])


class PerplexityClient:
    """Client for interacting with Perplexity API."""

    BASE_URL = "https://api.perplexity.ai"

    def __init__(self, api_key: str):
        """Initialize Perplexity client with API key."""
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._activities: List[ActivityEntry] = []

    async def fetch_activities(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ActivityEntry]:
        """
        Fetch activities from Perplexity for the specified date range.

        Note: Perplexity API doesn't provide direct chat history access.
        This implementation assumes local conversation logging.
        """
        logger.info(f"Fetching Perplexity activities from {start_date} to {end_date}")

        try:
            # Check for local conversation log
            log_path = Path.home() / ".personal-summarizer" / "perplexity_history.json"
            
            if log_path.exists():
                with open(log_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                            
                            if start_date <= timestamp <= end_date:
                                entry = ActivityEntry(
                                    timestamp=timestamp,
                                    platform=Platform.PERPLEXITY,
                                    work_done=data.get("query", "Research Query")[:500],
                                    file_links=[],
                                    comments=f"Citations: {len(data.get('citations', []))}",
                                    metadata={"citations": data.get("citations", [])}
                                )
                                self._activities.append(entry)
            
            logger.info(f"Found {len(self._activities)} Perplexity activities")
            return self._activities

        except Exception as e:
            logger.error(f"Error fetching Perplexity activities: {e}")
            return []

    async def list_models(self) -> List[str]:
        """List available Perplexity models."""
        return [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online"
        ]


class GoogleCloudClient:
    """Client for interacting with Google Cloud APIs (Drive, Docs)."""

    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents.readonly"
    ]

    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Google Cloud client with credentials."""
        self.credentials_path = credentials_path
        self._credentials = None
        self._drive_service = None
        self._docs_service = None
        self._activities: List[ActivityEntry] = []

    def _authenticate(self):
        """Authenticate with Google Cloud using OAuth 2.0."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            if self.credentials_path and os.path.exists(self.credentials_path):
                self._credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=self.SCOPES
                )
                self._drive_service = build('drive', 'v3', credentials=self._credentials)
                self._docs_service = build('docs', 'v1', credentials=self._credentials)
                logger.info("Google Cloud authentication successful")
            else:
                logger.warning("Google Cloud credentials not found")

        except ImportError:
            logger.error("google-api-python-client not installed")
        except Exception as e:
            logger.error(f"Google Cloud authentication failed: {e}")

    async def fetch_activities(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ActivityEntry]:
        """Fetch activities from Google Cloud for the specified date range."""
        logger.info(f"Fetching Google Cloud activities from {start_date} to {end_date}")

        if not self._drive_service:
            self._authenticate()

        if not self._drive_service:
            logger.warning("Drive service not initialized, skipping")
            return []

        try:
            # Fetch Drive file modifications
            await self._fetch_drive_activities(start_date, end_date)
            
            logger.info(f"Found {len(self._activities)} Google Cloud activities")
            return self._activities

        except Exception as e:
            logger.error(f"Error fetching Google Cloud activities: {e}")
            return []

    async def _fetch_drive_activities(
        self,
        start_date: datetime,
        end_date: datetime
    ):
        """Fetch Drive file modification activities."""
        try:
            # Query for files modified in date range
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
            
            query = f"modifiedTime >= '{start_str}' AND modifiedTime <= '{end_str}'"
            
            results = self._drive_service.files().list(
                q=query,
                fields="files(id, name, modifiedTime, webViewLink, mimeType)",
                pageSize=100
            ).execute()

            files = results.get('files', [])

            for file in files:
                timestamp = datetime.fromisoformat(
                    file['modifiedTime'].replace('Z', '+00:00')
                )
                
                entry = ActivityEntry(
                    timestamp=timestamp,
                    platform=Platform.GOOGLE_CLOUD,
                    work_done=f"Modified: {file['name']}",
                    file_links=[file.get('webViewLink', '')],
                    comments=f"Type: {file.get('mimeType', 'unknown')}"
                )
                self._activities.append(entry)

        except Exception as e:
            logger.error(f"Error fetching Drive activities: {e}")


class ActivityAggregator:
    """Main aggregator class for combining activities from all platforms."""

    def __init__(self, config: AggregationConfig):
        """Initialize aggregator with configuration."""
        self.config = config
        self.gemini_client: Optional[GeminiClient] = None
        self.perplexity_client: Optional[PerplexityClient] = None
        self.google_cloud_client: Optional[GoogleCloudClient] = None

        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize platform clients based on configuration."""
        if self.config.include_gemini and self.config.api_key_gemini:
            self.gemini_client = GeminiClient(self.config.api_key_gemini)

        if self.config.include_perplexity and self.config.api_key_perplexity:
            self.perplexity_client = PerplexityClient(self.config.api_key_perplexity)

        if self.config.include_google_cloud:
            self.google_cloud_client = GoogleCloudClient(
                self.config.google_credentials_path
            )

    async def aggregate(self) -> List[ActivityEntry]:
        """Aggregate activities from all configured platforms."""
        all_activities: List[ActivityEntry] = []

        # Fetch from all platforms concurrently
        tasks = []

        if self.gemini_client:
            tasks.append(self.gemini_client.fetch_activities(
                self.config.start_date,
                self.config.end_date
            ))

        if self.perplexity_client:
            tasks.append(self.perplexity_client.fetch_activities(
                self.config.start_date,
                self.config.end_date
            ))

        if self.google_cloud_client:
            tasks.append(self.google_cloud_client.fetch_activities(
                self.config.start_date,
                self.config.end_date
            ))

        # Execute all fetches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_activities.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Platform fetch error: {result}")

        # Sort by timestamp
        all_activities.sort(key=lambda x: x.timestamp)

        return all_activities

    def generate_markdown_output(
        self,
        activities: List[ActivityEntry]
    ) -> str:
        """Generate Markdown table output from activities."""
        lines = [
            "# Personal Work Summary",
            "",
            f"**Period**: {self.config.start_date.date()} to {self.config.end_date.date()}",
            f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Activity Log",
            "",
            "| Date/Time | Platform | Work Done | File Links | Comments |",
            "|-----------|----------|-----------|------------|----------|"
        ]

        for activity in activities:
            lines.append(activity.to_markdown_row())

        lines.extend([
            "",
            "---",
            f"*Total activities: {len(activities)}*"
        ])

        return "\n".join(lines)

    async def save_output(self, content: str, filepath: str):
        """Save output content to file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Output saved to {filepath}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Personal Work Summarizer - Aggregate AI platform activity"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="summary.md",
        help="Output file path (default: summary.md)"
    )

    parser.add_argument(
        "--gemini-key",
        type=str,
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )

    parser.add_argument(
        "--perplexity-key",
        type=str,
        help="Perplexity API key (or set PERPLEXITY_API_KEY env var)"
    )

    parser.add_argument(
        "--google-credentials",
        type=str,
        help="Path to Google Cloud credentials JSON file"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        sys.exit(1)

    # Build configuration
    config = AggregationConfig(
        start_date=start_date,
        end_date=end_date,
        output_file=args.output,
        api_key_gemini=args.gemini_key or os.environ.get("GEMINI_API_KEY"),
        api_key_perplexity=args.perplexity_key or os.environ.get("PERPLEXITY_API_KEY"),
        google_credentials_path=args.google_credentials
    )

    # Create aggregator and run
    aggregator = ActivityAggregator(config)
    
    logger.info("Starting activity aggregation...")
    activities = await aggregator.aggregate()
    
    logger.info(f"Aggregated {len(activities)} activities")

    # Generate and save output
    markdown = aggregator.generate_markdown_output(activities)
    await aggregator.save_output(markdown, config.output_file)

    print(f"\n✅ Summary generated: {config.output_file}")
    print(f"   Total activities: {len(activities)}")


if __name__ == "__main__":
    asyncio.run(main())
