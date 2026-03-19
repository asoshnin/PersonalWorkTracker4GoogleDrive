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

def deduplicate(activities: List[ActivityEntry]) -> List[ActivityEntry]:
    """
    Within each session_id group, if the same file (same name) appears 
    multiple times with the same action_type, keep only the most recent 
    event (max timestamp) for that file+action_type combination.
    """
    if not activities:
        return activities
        
    # We want to group by (session_id, action_type, file_name)
    # the file_name can be extracted from description
    kept_activities = []
    
    # We can use a dictionary to keep the max timestamp entry
    # Key: (session_id, action_type, file_name)
    # Value: ActivityEntry
    tracker = {}
    
    for act in activities:
        # Default fallback to entire description if no filename structure exists
        desc = act.description.replace("\n", " ").strip()
        if ":" in desc:
            file_name = desc.split(":", 1)[1].strip()
        else:
            file_name = desc
            
        key = (act.session_id, act.action_type, file_name)
        
        if key not in tracker:
            tracker[key] = act
        else:
            if act.timestamp > tracker[key].timestamp:
                tracker[key] = act
                
    # Re-sort remaining items globally by session_id, then timestamp
    result = list(tracker.values())
    return sorted(result, key=lambda a: (a.session_id, a.timestamp))

