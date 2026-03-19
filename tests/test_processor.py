import pytest
from datetime import datetime, timedelta
from typing import List

from pa_assistant.models import ActivityEntry, Platform
from pa_assistant.processor import sessionize

def create_activity(ts: datetime) -> ActivityEntry:
    return ActivityEntry(
        timestamp=ts,
        platform=Platform.GEMINI,
        description="test",
        file_links=[],
        comments="",
        metadata={},
        action_type="EDIT",
        session_id=0
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
    # Threshold creates a new session if delta > gap_minutes
    start = datetime(2026, 3, 19, 10, 0, 0)
    a1 = create_activity(start)
    a2 = create_activity(start + timedelta(minutes=30))
    a3 = create_activity(start + timedelta(minutes=31))
    
    # 30 mins is NOT > 30 mins, so a2 is in session 1
    # 31 mins from start + 30m, actually gap between a2 and a3 is 1 min!
    # Let's adjust to test the exactly threshold logic properly:
    
    # Gap from a1 to a2 is 30 mins
    a_gap1 = create_activity(start + timedelta(minutes=30))
    # Gap from a2 to a3 is 31 mins
    a_gap2 = create_activity(start + timedelta(minutes=30) + timedelta(minutes=31))
    
    result = sessionize([a1, a_gap1, a_gap2], gap_minutes=30)
    
    assert result[0].session_id == 1
    assert result[1].session_id == 1
    assert result[2].session_id == 2
