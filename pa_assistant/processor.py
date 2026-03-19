from typing import List
from .models import ActivityEntry

def sessionize(activities: List[ActivityEntry], gap_minutes: int) -> List[ActivityEntry]:
    """
    Groups a list of ActivityEntry instances into sessions based on temporal proximity.
    
    If the gap between chronologically sorted subsequent activities exceeds gap_minutes,
    the session counter increments.
    """
    if not activities:
        return activities

    sorted_activities = sorted(activities, key=lambda a: a.timestamp)
    
    session_id = 1
    sorted_activities[0].session_id = session_id
    
    for i in range(1, len(sorted_activities)):
        curr = sorted_activities[i]
        prev = sorted_activities[i - 1]
        
        delta = (curr.timestamp - prev.timestamp).total_seconds() / 60.0
        
        if delta > gap_minutes:
            session_id += 1
            
        curr.session_id = session_id

    return sorted_activities
