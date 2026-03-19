from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional
from collections import defaultdict

from .models import ActivityEntry

ACTION_ICONS = {
    "EDIT": "✏️",
    "CREATE": "📄",
    "VIEW": "👁️",
    "COMMENT": "💬",
    "RENAME": "🏷️",
    "MOVE": "📦",
    "DELETE": "🗑️",
}

def generate_markdown(
    activities: Iterable[ActivityEntry],
    start_date: datetime,
    end_date: datetime,
    focus_prompt: Optional[str] = None,
) -> str:
    activities_list = sorted(activities, key=lambda a: a.timestamp)
    
    # Pre-calculate counts
    edited = sum(1 for a in activities_list if a.action_type.upper() == "EDIT")
    created = sum(1 for a in activities_list if a.action_type.upper() == "CREATE")
    other = len(activities_list) - edited - created
    total = len(activities_list)
    
    # Calculate sessions total active time
    sessions = defaultdict(list)
    for a in activities_list:
        if a.session_id:
            sessions[a.session_id].append(a)
    
    total_active_seconds = 0
    session_count_per_day = defaultdict(int)
    
    for s_id, s_acts in sessions.items():
        if not s_acts:
            continue
        s_start = s_acts[0].timestamp
        s_end = s_acts[-1].timestamp
        duration_sec = (s_end - s_start).total_seconds()
        total_active_seconds += duration_sec
        
        day_str = s_start.date().isoformat()
        session_count_per_day[day_str] += 1
        
    hours, remainder = divmod(total_active_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    time_str = f"{int(hours)}h {int(minutes)}min"
    
    most_active_day = "None"
    most_active_count = 0
    if session_count_per_day:
        most_active_day_iso = max(session_count_per_day.keys(), key=lambda d: session_count_per_day[d])
        most_active_count = session_count_per_day[most_active_day_iso]
        mad_dt = datetime.fromisoformat(most_active_day_iso)
        most_active_day = f"{mad_dt.strftime('%A')} {most_active_day_iso}"

    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📋 PA REPORT · {start_date.date().isoformat()} to {end_date.date().isoformat()}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"⏱  Total active time:   {time_str} across {len(sessions)} sessions")
    lines.append(f"📁 Files touched:        {total} ({edited} edited, {created} created, {other} other)")
    lines.append(f"🔥 Most active day:      {most_active_day} ({most_active_count} sessions)")
    lines.append(f"📌 Focus filter:         {focus_prompt or 'none'}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
        
    for s_id in sorted(sessions.keys()):
        s_acts = sessions[s_id]
        s_start = s_acts[0].timestamp
        s_end = s_acts[-1].timestamp
        dur_hrs, dur_rem = divmod((s_end - s_start).total_seconds(), 3600)
        dur_mins, _ = divmod(dur_rem, 60)
        dur_str = f"{int(dur_hrs)}h {int(dur_mins)}m" if dur_hrs > 0 else f"{int(dur_mins)}m"
        
        # Dominant action
        action_counts = defaultdict(int)
        for act in s_acts:
            action_counts[act.action_type.upper()] += 1
        dominant_action = max(action_counts.keys(), key=lambda k: action_counts[k]) if action_counts else "UNKNOWN"
        
        weekday = s_start.strftime("%A")
        date_str = s_start.date().isoformat()
        start_t = s_start.strftime("%H:%M")
        end_t = s_end.strftime("%H:%M")
        
        lines.append(f"🟦 SESSION {s_id} · {weekday} {date_str} · {start_t}–{end_t} · {dur_str} · {len(s_acts)} files · Mostly {dominant_action}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for act in s_acts:
            icon = ACTION_ICONS.get(act.action_type.upper(), "🔹")
            act_type = act.action_type.capitalize()
            desc = act.description.replace("\n", " ").strip()
            if ":" in desc:
                filename = desc.split(":", 1)[1].strip()
            else:
                filename = desc
                
            link = act.file_links[0] if act.file_links else "-"
            # use formatting tricks
            lines.append(f"  {icon}  {act_type:<10} · {filename:<40} → {link}")
        lines.append("")

    # Resume block
    last_edited = None
    last_created = None
    for a in activities_list:
        if a.action_type.upper() == "EDIT":
            last_edited = a
        elif a.action_type.upper() == "CREATE":
            last_created = a
            
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🚀 RESUME HERE")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if last_edited:
        desc = last_edited.description.split(":", 1)[-1].strip() if ":" in last_edited.description else last_edited.description
        link = last_edited.file_links[0] if last_edited.file_links else "-"
        lines.append(f"Last file edited:   {desc} → {link} · {last_edited.timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
    if last_created:
        desc = last_created.description.split(":", 1)[-1].strip() if ":" in last_created.description else last_created.description
        link = last_created.file_links[0] if last_created.file_links else "-"
        lines.append(f"Last file created:  {desc} → {link} · {last_created.timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
        
    last_session_end = "-"
    if sessions:
        last_s_id = max(sessions.keys())
        last_s_end = sessions[last_s_id][-1].timestamp
        last_session_end = f"{last_s_end.strftime('%A')} {last_s_end.date().isoformat()} at {last_s_end.strftime('%H:%M')}"
    lines.append(f"Last session ended: {last_session_end}")

    return "\n".join(lines)
