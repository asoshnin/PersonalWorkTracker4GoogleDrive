from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from .connectors import (
    fetch_drive_activities,
    fetch_gemini_activities,
    fetch_perplexity_activities,
)
from .models import ActivityEntry
from .processor import sessionize, deduplicate
from .report import generate_markdown

logger = logging.getLogger(__name__)


@dataclass
class RunnerConfig:
    reports_dir: Path
    enable_drive: bool = True
    enable_gemini_logs: bool = True
    enable_perplexity_logs: bool = True
    google_credentials_path: Optional[Path] = None
    token_path: Optional[Path] = None
    gemini_log_path: Optional[Path] = None
    perplexity_log_path: Optional[Path] = None
    default_start_offset_days: int = 1
    default_end_offset_days: int = 0
    session_gap_minutes: int = 30
    timezone: str = "UTC"


def load_config(path: Optional[str]) -> RunnerConfig:
    """
    Load configuration from a small YAML file.

    Expected minimal keys:
    - reports_dir (string, required)
    - enable_drive / enable_gemini_logs / enable_perplexity_logs (bool, optional)
    - google_credentials_path (string, optional)
    - token_path (string, optional)
    """
    if path is None:
        raise ValueError("Config path must be provided for the runner.")

    cfg_path = Path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    reports_dir = Path(raw.get("reports_dir", "./reports"))
    enable_drive = bool(raw.get("enable_drive", True))
    enable_gemini_logs = bool(raw.get("enable_gemini_logs", True))
    enable_perplexity_logs = bool(raw.get("enable_perplexity_logs", True))
    google_credentials = raw.get("google_credentials_path")
    token = raw.get("token_path", "token.json")
    connectors = raw.get("connectors", {})
    
    gem_path = connectors.get("gemini_log_path") or raw.get("gemini_log_path")
    perp_path = connectors.get("perplexity_log_path") or raw.get("perplexity_log_path")

    # Set default paths if not provided
    default_gem_path = Path.home() / ".personal-summarizer" / "gemini_history.json"
    default_perp_path = Path.home() / ".personal-summarizer" / "perplexity_history.json"

    return RunnerConfig(
        reports_dir=reports_dir,
        enable_drive=enable_drive,
        enable_gemini_logs=enable_gemini_logs,
        enable_perplexity_logs=enable_perplexity_logs,
        google_credentials_path=Path(google_credentials) if google_credentials else None,
        token_path=Path(token) if token else None,
        gemini_log_path=Path(gem_path).expanduser() if gem_path else default_gem_path,
        perplexity_log_path=Path(perp_path).expanduser() if perp_path else default_perp_path,
        default_start_offset_days=int(raw.get("default_start_offset_days", 1)),
        default_end_offset_days=int(raw.get("default_end_offset_days", 0)),
        session_gap_minutes=int(raw.get("session_gap_minutes", 30)),
        timezone=str(raw.get("timezone", "UTC")),
    )


def run_summary(
    start_date: datetime,
    end_date: datetime,
    config_path: str,
    focus_prompt: Optional[str] = None,
) -> tuple[List[ActivityEntry], str, Path]:
    """
    High-level helper used by CLI or DeerFlow orchestration.

    Returns:
        (activities, markdown, output_path)
    """
    cfg = load_config(config_path)

    activities: List[ActivityEntry] = []

    if cfg.enable_drive:
        activities.extend(
            fetch_drive_activities(
                start=start_date,
                end=end_date,
                config=cfg,
            )
        )

    if cfg.enable_gemini_logs:
        activities.extend(fetch_gemini_activities(start_date, end_date, config=cfg))

    if cfg.enable_perplexity_logs:
        activities.extend(fetch_perplexity_activities(start_date, end_date, config=cfg))

    # Phase 1 Grouping & Deduplication
    activities = sessionize(activities, gap_minutes=cfg.session_gap_minutes)
    activities = deduplicate(activities)

    # Generate Markdown
    markdown = generate_markdown(
        activities=activities,
        start_date=start_date,
        end_date=end_date,
        focus_prompt=focus_prompt,
        timezone_str=cfg.timezone
    )

    # Determine report filename logic securely prioritizing ISO weeks bounding securely
    is_week_report = False
    
    # 1. Exactly Monday to Sunday (last-week or exactly one ISO week)
    if start_date.weekday() == 0 and start_date.hour == 0 and start_date.minute == 0:
        if end_date.weekday() == 6 and end_date.hour == 23 and end_date.minute == 59:
            is_week_report = True
        # 2. this-week (Monday to today's current time, where today is within the same week)
        elif (end_date - start_date).days < 7 and end_date.date() >= start_date.date():
             is_week_report = True

    if is_week_report:
        iso_year, iso_week, _ = start_date.isocalendar()
        report_filename = f"PA_Report_{iso_year}-W{iso_week:02d}.md"
    else:
        if start_date.date() == end_date.date():
            report_filename = f"PA_Report_{start_date.date().isoformat()}.md"
        else:
            report_filename = f"PA_Report_{start_date.date().isoformat()}_to_{end_date.date().isoformat()}.md"

    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(cfg.reports_dir) / report_filename

    with out_path.open("w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info("Summary written to %s", out_path)
    return activities, markdown, out_path


