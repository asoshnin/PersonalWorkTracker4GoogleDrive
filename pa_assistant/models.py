from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class Platform(str, Enum):
    """Supported platforms for activity aggregation."""

    GEMINI = "Gemini"
    PERPLEXITY = "Perplexity"
    DRIVE = "Google Drive"


@dataclass
class ActivityEntry:
    """Represents a single normalized activity entry."""

    timestamp: datetime
    platform: Platform
    description: str
    file_links: List[str] = field(default_factory=list)
    comments: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 1: Grouping
    session_id: int = 0
    action_type: str = "EDIT"
