from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Any

from ..models import ActivityEntry, Platform

logger = logging.getLogger(__name__)


def _load_jsonl(path: Path) -> List[dict]:
    """Load a simple JSON-lines style file into a list of dicts."""
    records: List[dict] = []
    if not path.exists():
        logger.info("LLM log file not found: %s", path)
        return records

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping invalid JSON line in %s", path)
    except OSError as exc:
        logger.error("Failed to read LLM log file %s: %s", path, exc)

    return records


def fetch_gemini_activities(start: datetime, end: datetime, config: Any = None) -> List[ActivityEntry]:
    """
    Fetch Gemini activities from a local log file within the given date range.

    This mirrors the assumptions from the legacy Personal Work Summarizer:
    - Log file path: ~/.personal-summarizer/gemini_history.json
    - Each line: JSON with at least `timestamp` and `prompt` fields.
    """
    if config and getattr(config, "gemini_log_path", None):
        log_path = Path(config.gemini_log_path)
    else:
        log_path = Path.home() / ".personal-summarizer" / "gemini_history.json"
    records = _load_jsonl(log_path)

    activities: List[ActivityEntry] = []
    for data in records:
        ts_str = data.get("timestamp")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            continue

        if not (start <= ts <= end):
            continue

        description = (data.get("prompt") or "AI Query")[:500]
        file_links = data.get("files") or []
        model_name = data.get("model") or "unknown"

        activities.append(
            ActivityEntry(
                timestamp=ts,
                platform=Platform.GEMINI,
                description=description,
                file_links=file_links,
                comments=f"Model: {model_name}",
                metadata={"model": model_name},
            )
        )

    logger.info("Loaded %d Gemini activities from %s", len(activities), log_path)
    return activities


def fetch_perplexity_activities(start: datetime, end: datetime, config: Any = None) -> List[ActivityEntry]:
    """
    Fetch Perplexity activities from a local log file within the given date range.

    This mirrors the assumptions from the legacy Personal Work Summarizer:
    - Log file path: ~/.personal-summarizer/perplexity_history.json
    - Each line: JSON with at least `timestamp` and `query` fields.
    """
    if config and getattr(config, "perplexity_log_path", None):
        log_path = Path(config.perplexity_log_path)
    else:
        log_path = Path.home() / ".personal-summarizer" / "perplexity_history.json"
    records = _load_jsonl(log_path)

    activities: List[ActivityEntry] = []
    for data in records:
        ts_str = data.get("timestamp")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            continue

        if not (start <= ts <= end):
            continue

        description = (data.get("query") or "Research Query")[:500]
        citations = data.get("citations") or []

        activities.append(
            ActivityEntry(
                timestamp=ts,
                platform=Platform.PERPLEXITY,
                description=description,
                file_links=[],
                comments=f"Citations: {len(citations)}",
                metadata={"citations": citations},
            )
        )

    logger.info("Loaded %d Perplexity activities from %s", len(activities), log_path)
    return activities

