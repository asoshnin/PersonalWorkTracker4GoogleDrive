from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

from .models import ActivityEntry

logger = logging.getLogger(__name__)

ACTION_ICONS = {
    "EDIT": "✏️",
    "CREATE": "📄",
    "VIEW": "👁️",
    "COMMENT": "💬",
    "RENAME": "🏷️",
    "MOVE": "📦",
    "DELETE": "🗑️",
}

ACTION_VERBS = {
    "EDIT": "Editing",
    "CREATE": "Creating",
    "VIEW": "Viewing",
    "COMMENT": "Commenting",
    "RENAME": "Renaming",
    "MOVE": "Moving",
    "DELETE": "Deleting",
}

@dataclass
class GroupedActivity:
    time_range: str
    actions: str
    file_name: str
    link: str

def convert_to_tz(dt: datetime, tz_name: str) -> datetime:
    """Safe timezone conversion handling naive UTC source objects cleanly."""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(tz_name))
    
def group_session_activities(activities: List[ActivityEntry], tz_name: str) -> List[GroupedActivity]:
    grouped_map = {}
    
    for act in activities:
        desc = act.description.replace("\n", " ").strip()
        if ":" in desc:
            file_name = desc.split(":", 1)[1].strip()
        else:
            file_name = desc
            
        if file_name not in grouped_map:
            grouped_map[file_name] = []
        grouped_map[file_name].append(act)
        
    results = []
    
    for file_name, acts in grouped_map.items():
        acts.sort(key=lambda a: a.timestamp)
        first_t = convert_to_tz(acts[0].timestamp, tz_name)
        last_t = convert_to_tz(acts[-1].timestamp, tz_name)
        
        t1_str = first_t.strftime("%H:%M")
        if first_t == last_t:
            time_range = t1_str
        else:
            t2_str = last_t.strftime("%H:%M")
            time_range = f"{t1_str}–{t2_str}"
            
        action_chain_icons = []
        action_chain_texts = []
        seen_actions = set()
        
        for a in acts:
            action_type_upper = a.action_type.upper()
            if action_type_upper not in seen_actions:
                seen_actions.add(action_type_upper)
                action_chain_icons.append(ACTION_ICONS.get(action_type_upper, "🔹"))
                action_chain_texts.append(a.action_type.capitalize())
        
        actions_str = f"{''.join(action_chain_icons)} {' → '.join(action_chain_texts)}"
        
        link = acts[-1].file_links[0] if acts[-1].file_links else "-"
        
        results.append(GroupedActivity(
            time_range=time_range,
            actions=actions_str,
            file_name=file_name,
            link=link
        ))
        
    return sorted(results, key=lambda g: g.time_range)


def generate_markdown(
    activities: Iterable[ActivityEntry],
    start_date: datetime,
    end_date: datetime,
    focus_prompt: Optional[str] = None,
    timezone_str: str = "UTC"
) -> str:
    activities_list = sorted(activities, key=lambda a: a.timestamp)
    
    edited = sum(1 for a in activities_list if a.action_type.upper() == "EDIT")
    created = sum(1 for a in activities_list if a.action_type.upper() == "CREATE")
    other = len(activities_list) - edited - created
    total = len(activities_list)
    
    sessions_map = defaultdict(list)
    for a in activities_list:
        if a.session_id:
            sessions_map[a.session_id].append(a)
    
    total_active_seconds = 0
    session_count_per_day = defaultdict(int)
    
    rendered_sessions = []
    
    for s_id in sorted(sessions_map.keys()):
        s_acts = sessions_map[s_id]
        if not s_acts:
            continue
        
        s_start_utc = s_acts[0].timestamp
        s_end_utc = s_acts[-1].timestamp
        duration_sec = (s_end_utc - s_start_utc).total_seconds()
        total_active_seconds += duration_sec
        
        s_start = convert_to_tz(s_start_utc, timezone_str)
        s_end = convert_to_tz(s_end_utc, timezone_str)
        
        day_str = s_start.date().isoformat()
        session_count_per_day[day_str] += 1
        
        dur_hrs, dur_rem = divmod(duration_sec, 3600)
        dur_mins, _ = divmod(dur_rem, 60)
        if duration_sec < 60:
            dur_str = "< 1m"
        elif dur_hrs > 0:
            dur_str = f"{int(dur_hrs)}h {int(dur_mins)}m"
        else:
            dur_str = f"{int(dur_mins)}m"
        
        action_counts = defaultdict(int)
        for act in s_acts:
            action_counts[act.action_type.upper()] += 1
        
        dom_key = max(action_counts.keys(), key=lambda k: action_counts[k]) if action_counts else "UNKNOWN"
        dominant_action = ACTION_VERBS.get(dom_key, dom_key.capitalize())
        
        grouped_acts = group_session_activities(s_acts, timezone_str)
            
        rendered_sessions.append({
            "id": s_id,
            "weekday": s_start.strftime("%A"),
            "date_str": s_start.date().isoformat(),
            "start_time": s_start.strftime("%H:%M"),
            "end_time": s_end.strftime("%H:%M"),
            "dur_str": dur_str,
            "dominant_action": dominant_action,
            "grouped_acts": grouped_acts
        })
        
    hours, remainder = divmod(total_active_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if total_active_seconds < 60 and total_active_seconds > 0:
        time_str = "< 1m"
    elif hours > 0:
        time_str = f"{int(hours)}h {int(minutes)}m"
    else:
        time_str = f"{int(minutes)}m"
    
    most_active_day = "None"
    most_active_count = 0
    if session_count_per_day:
        most_active_day_iso = max(session_count_per_day.keys(), key=lambda d: session_count_per_day[d])
        most_active_count = session_count_per_day[most_active_day_iso]
        mad_dt = convert_to_tz(datetime.fromisoformat(most_active_day_iso), timezone_str)
        most_active_day = f"{mad_dt.strftime('%A')} {most_active_day_iso}"

    last_edited = None
    last_created = None
    for a in activities_list:
        if a.action_type.upper() == "EDIT":
            last_edited = a
        elif a.action_type.upper() == "CREATE":
            last_created = a
            
    resume_here = {
        "last_edited_file": None,
        "last_created_file": None,
        "last_session_end": "-"
    }
    
    tz_abbr = convert_to_tz(start_date, timezone_str).tzname()
    
    if last_edited:
        desc = last_edited.description.split(":", 1)[-1].strip() if ":" in last_edited.description else last_edited.description
        link = last_edited.file_links[0] if last_edited.file_links else "-"
        resume_here["last_edited_file"] = desc
        resume_here["last_edited_link"] = link
        resume_here["last_edited_ts"] = f"{convert_to_tz(last_edited.timestamp, timezone_str).strftime('%a %d %b, %H:%M')} {tz_abbr}"
        
    if last_created:
        desc = last_created.description.split(":", 1)[-1].strip() if ":" in last_created.description else last_created.description
        link = last_created.file_links[0] if last_created.file_links else "-"
        resume_here["last_created_file"] = desc
        resume_here["last_created_link"] = link
        resume_here["last_created_ts"] = f"{convert_to_tz(last_created.timestamp, timezone_str).strftime('%a %d %b, %H:%M')} {tz_abbr}"
        
    if rendered_sessions:
        last_s_end = convert_to_tz(sessions_map[max(sessions_map.keys())][-1].timestamp, timezone_str)
        resume_here["last_session_end"] = f"{last_s_end.strftime('%A')} {last_s_end.date().isoformat()} at {last_s_end.strftime('%H:%M')} {tz_abbr}"

    templates_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("report.md.j2")
    
    # Safe date ISO rendering wrapper considering UTC bounds natively
    r_start = convert_to_tz(start_date, timezone_str)
    r_end = convert_to_tz(end_date, timezone_str)
    
    return template.render(
        start_date=r_start.date().isoformat(),
        end_date=r_end.date().isoformat(),
        time_str=time_str,
        sessions=rendered_sessions,
        total=total,
        edited=edited,
        created=created,
        other=other,
        most_active_day=most_active_day,
        most_active_count=most_active_count,
        focus_prompt=focus_prompt,
        resume_here=resume_here,
        tz_abbr=tz_abbr
    )
