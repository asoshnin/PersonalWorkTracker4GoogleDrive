from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from .models import ActivityEntry


def generate_markdown(
    activities: Iterable[ActivityEntry],
    start_date: datetime,
    end_date: datetime,
    focus_prompt: Optional[str] = None,
) -> str:
    """
    Generate a simple Markdown activity report for the given entries.

    This is intentionally lightweight for the Phase 1 MVP:
    - Chronological table of activities.
    - Optional note about a focus/topic prompt (no LLM integration yet).
    """
    sorted_activities: List[ActivityEntry] = sorted(
        activities, key=lambda a: a.timestamp
    )

    lines: List[str] = []
    lines.append("# Personal Activity Summary")
    lines.append("")
    lines.append(
        f"**Period**: {start_date.date().isoformat()} to {end_date.date().isoformat()}"
    )
    lines.append(
        f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    if focus_prompt:
        lines.append("")
        lines.append(f"**Focus**: {focus_prompt}")
    lines.append("")
    lines.append("## Activity Log")
    lines.append("")
    lines.append(
        "| Date/Time | Source | Description | File Links | Comments |"
    )
    lines.append(
        "|-----------|--------|-------------|------------|----------|"
    )

    for activity in sorted_activities:
        ts_str = activity.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        file_links_str = ", ".join(activity.file_links) if activity.file_links else "-"
        # Basic sanitization to avoid newlines breaking the table
        description = activity.description.replace("\n", " ").strip()
        comments = activity.comments.replace("\n", " ").strip()

        lines.append(
            f"| {ts_str} | {activity.platform.value} | {description} | {file_links_str} | {comments} |"
        )

    lines.append("")
    lines.append("---")
    lines.append(f"*Total activities: {len(sorted_activities)}*")

    return "\n".join(lines)

