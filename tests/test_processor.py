import pytest
from datetime import datetime, timedelta
from typing import List

from pa_assistant.models import ActivityEntry, Platform
from pa_assistant.processor import sessionize, deduplicate

def create_activity(ts: datetime, desc: str = "test", session_id: int = 0) -> ActivityEntry:
    return ActivityEntry(
        timestamp=ts,
        platform=Platform.GEMINI,
        description=desc,
        file_links=[],
        comments="",
        metadata={},
        action_type="EDIT",
        session_id=session_id
    )

def test_single_activity():
    activities = [create_activity(datetime(2026, 3, 19, 10, 0, 0))]
    result = sessionize(activities, gap_minutes=30)
    assert len(result) == 1
    assert result[0].session_id == 1

def test_normal_grouping():
    # 3 activities: first two close, third after gap
    start = datetime(2026, 3, 19, 10, 0, 0)
    a1 = create_activity(start)
    a2 = create_activity(start + timedelta(minutes=5))
    a3 = create_activity(start + timedelta(hours=2))
    
    result = sessionize([a1, a2, a3], gap_minutes=30)
    
    assert result[0].session_id == 1
    assert result[1].session_id == 1
    assert result[2].session_id == 2

def test_all_within_gap():
    start = datetime(2026, 3, 19, 10, 0, 0)
    activities = [
        create_activity(start),
        create_activity(start + timedelta(minutes=10)),
        create_activity(start + timedelta(minutes=20)),
        create_activity(start + timedelta(minutes=29)),
    ]
    result = sessionize(activities, gap_minutes=30)
    
    for a in result:
        assert a.session_id == 1

def test_exactly_at_threshold():
    # Gap from a1 to a2 is 30 mins
    start = datetime(2026, 3, 19, 10, 0, 0)
    a1 = create_activity(start)
    a_gap1 = create_activity(start + timedelta(minutes=30))
    # Gap from a2 to a3 is 31 mins
    a_gap2 = create_activity(start + timedelta(minutes=30) + timedelta(minutes=31))
    
    result = sessionize([a1, a_gap1, a_gap2], gap_minutes=30)
    
    assert result[0].session_id == 1
    assert result[1].session_id == 1
    assert result[2].session_id == 2

def test_deduplicate_with_duplicates():
    start = datetime(2026, 3, 19, 10, 0, 0)
    a1 = create_activity(start, desc="Edited: file1.txt", session_id=1)
    a2 = create_activity(start + timedelta(minutes=5), desc="Edited: file1.txt", session_id=1)
    a3 = create_activity(start + timedelta(minutes=10), desc="Edited: file2.txt", session_id=1)
    
    result = deduplicate([a1, a2, a3])
    
    assert len(result) == 2
    # Ensure it kept a2 over a1 because it has the max timestamp
    assert result[0].timestamp == a2.timestamp
    assert result[1].timestamp == a3.timestamp

def test_deduplicate_without_duplicates():
    start = datetime(2026, 3, 19, 10, 0, 0)
    a1 = create_activity(start, desc="Edited: file1.txt", session_id=1)
    a2 = create_activity(start + timedelta(minutes=5), desc="Edited: file2.txt", session_id=1)
    a3 = create_activity(start + timedelta(minutes=10), desc="Edited: file1.txt", session_id=1)
    a3.action_type = "CREATE"
    
    result = deduplicate([a1, a2, a3])
    
    assert len(result) == 3
