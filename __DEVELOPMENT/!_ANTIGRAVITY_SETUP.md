# Antigravity Setup & Instructions for PA Assistant Refactoring

## Part 1 — Configure Antigravity Before You Start

### Step 1: Choose the Right Mode

Antigravity has three execution modes.  For this refactoring, use **Agent-assisted development** (the middle option): [codecademy](https://www.codecademy.com/article/how-to-set-up-and-use-google-antigravity)

- ✅ **Agent-assisted** — AI executes safe operations automatically, but asks for confirmation before anything risky. This is the right balance for refactoring existing working code. [codecademy](https://www.codecademy.com/article/how-to-set-up-and-use-google-antigravity)
- ❌ Avoid "Autopilot" (Agent-driven) — it will make sweeping changes without pausing, dangerous on a working codebase.
- ❌ Avoid "Review-driven" — it will ask permission for every tiny action, which slows everything down.

### Step 2: Configure Terminal Permissions

Go to **Settings → Terminal Command Auto Execution** and set it to **Request Review**, then add to the Allow List: [codelabs.developers.google](https://codelabs.developers.google.com/getting-started-google-antigravity)

```
pip install
python -m pytest
pip freeze
python -m pa_assistant.cli
```

Add to the Deny List for safety: [codelabs.developers.google](https://codelabs.developers.google.com/getting-started-google-antigravity)

```
rm -rf
sudo
git push
```

### Step 3: Set Up a Project Rule File

This is the most important configuration step. Rules are like permanent system instructions — you write them once and the agent follows them on every task.  In Antigravity, go to **Settings → Rules** and create a **project-level** rule (not global) by creating a file `.antigravity/rules.md` in your project root with this content: [youtube](https://www.youtube.com/watch?v=cIR0KS-a33I)

```markdown
# PA Assistant Project Rules

## Language & Runtime
- Python 3.10+
- All code must pass `python -m pytest` without errors

## Code Style
- Follow PEP8 strictly
- All functions must have docstrings
- Use type hints on all function signatures
- Use pathlib.Path for all file path operations, never raw strings

## Architecture Rules
- NEVER modify runner.py without explicit instruction — it is the orchestration core
- NEVER hardcode paths, credentials, or date values — all must come from pa_config.yaml
- token.json must ALWAYS be in .gitignore — verify this before completing any auth task
- New connectors must follow the same interface pattern as the existing drive.py connector

## Testing
- Write at minimum one unit test for every new function using pytest + unittest.mock
- Mock all Google API calls — never make real API calls in tests

## Scope Control
- Before starting any task, list the exact files you intend to modify
- If the task requires touching more than 5 files, produce a plan Artifact first and wait for approval
- Do not refactor code outside the defined task scope, even if you see improvements
```

### Step 4: Create a Context File

Create `__DEVELOPMENT/CONTEXT.md` in your repo and paste this in — Antigravity will read it when you reference it with `@`: [codelabs.developers.google](https://codelabs.developers.google.com/getting-started-google-antigravity)

```markdown
# Project Context

## What this project is
A Python CLI tool that fetches Google Drive activity and generates a Markdown report
to help users recall what they were working on. Entry point: pa_assistant/cli.py

## Current state
- Auth: Service Account (needs migration to OAuth 2.0 User Flow)
- Data source: Drive API v3 files.list() (needs migration to Drive Activity API v2)
- Output: Flat Markdown table (needs sessionization and structured report format)
- Tests: None currently exist

## Refactoring document
Full instructions are in: __DEVELOPMENT/2026-03-19_12-47_refactoring.md

## Key files
- pa_assistant/cli.py — entry point, CLI args
- pa_assistant/runner.py — orchestration, loads config (DO NOT MODIFY unless instructed)
- pa_assistant/connectors/drive.py — Google Drive integration (primary target for Phase 0)
- pa_assistant/connectors/llm_logs.py — log reader (has hardcoded paths to fix)
- pa_assistant/models.py — ActivityEntry data model
- pa_assistant/report.py — report generator (target for Phase 1)
- pa_config.yaml — single source of truth for configuration
```

***

## Part 2 — Instructions to Give Antigravity

Give these **one phase at a time**. Do not paste all phases at once — complete and verify each phase before moving to the next. [skywork](https://skywork.ai/blog/agent/best-prompts-antigravity/)

***

### 🔴 Phase 0, Task 1 — Fix Authentication

```
@CONTEXT.md @pa_assistant/connectors/drive.py @pa_config.yaml

TASK: Migrate Google Drive authentication from Service Account to OAuth 2.0 User Flow.

SCOPE (only these files):
- pa_assistant/connectors/drive.py
- pa_config.yaml (add new keys if needed)
- pa_config.example.yaml (mirror any changes)
- .gitignore (verify token.json is listed)

STEPS:
1. Replace google.oauth2.service_account.Credentials with google_auth_oauthlib.flow.InstalledAppFlow
2. Use scopes: drive.readonly and drive.activity.readonly
3. Store the resulting token in a path defined in pa_config.yaml (key: token_path)
4. Add token refresh logic so the token auto-renews without re-prompting the user
5. Verify token.json is in .gitignore — if not, add it

DO NOT touch runner.py, cli.py, or any other file outside the scope above.

Before writing any code, produce a plan Artifact showing exactly what will change in each file.
```

***

### 🔴 Phase 0, Task 2 — Drive Activity API

```
@CONTEXT.md @pa_assistant/connectors/drive.py @pa_assistant/models.py

TASK: Replace the current files().list() query with the Drive Activity API v2.

SCOPE:
- pa_assistant/connectors/drive.py (or create drive_activity.py in the same folder)
- pa_assistant/models.py (add action_type field to ActivityEntry)
- requirements.txt (add google-apps-activity if needed)

STEPS:
1. Replace the Drive API v3 files.list(modifiedTime) call with a Drive Activity API v2 query
2. Use the driveactivity service (google-apps-activity package)
3. Fetch activities for a given time range (passed as parameters, not hardcoded)
4. Map the following action types to ActivityEntry.action_type: EDIT, CREATE, VIEW, COMMENT, RENAME, MOVE, DELETE
5. Preserve all existing fields on ActivityEntry (id, name, timestamp, webViewLink, mimeType, description)
6. Add the new field: action_type (str)

DO NOT change how runner.py calls the connector — the interface must remain compatible.

Before writing any code, produce a plan Artifact.
```

***

### 🔴 Phase 0, Task 3 — Fix Hardcoded Paths + setup_auth.py

```
@CONTEXT.md @pa_assistant/connectors/llm_logs.py @pa_config.yaml @pa_assistant/runner.py

TASK: Fix all hardcoded file paths and create a one-command auth setup script.

SCOPE:
- pa_assistant/connectors/llm_logs.py
- pa_config.yaml (add gemini_log_path and perplexity_log_path keys)
- pa_config.example.yaml
- setup_auth.py (new file in project root)

STEPS:
1. In llm_logs.py, replace the hardcoded paths (~/.personal-summarizer/...) with values read from the config object passed by runner.py
2. Add gemini_log_path and perplexity_log_path keys to pa_config.yaml with the current hardcoded values as defaults
3. Add the same keys with comments to pa_config.example.yaml
4. Create setup_auth.py in the project root that:
   - Opens the OAuth browser flow
   - Writes token.json to the path defined in pa_config.yaml
   - Prints a success message with the token path when done
   - Can be run as: python setup_auth.py

DO NOT modify runner.py logic, only how it passes config to connectors.
```

***

### 🟠 Phase 1, Task 1 — Sessionization

```
@CONTEXT.md @pa_assistant/models.py @pa_assistant/report.py

TASK: Add sessionization logic and update the report to use grouped sessions.

SCOPE:
- pa_assistant/processor.py (new file)
- pa_assistant/models.py (add session_id field)
- pa_assistant/report.py (update to render sessions)
- pa_config.yaml (add session_gap_minutes key, default: 30)
- tests/test_processor.py (new file)

STEPS:
1. Create pa_assistant/processor.py with a function sessionize(activities, gap_minutes) that:
   - Sorts activities by timestamp ascending
   - Groups them into sessions: if gap between consecutive events > gap_minutes, start a new session
   - Assigns a session_id integer to each ActivityEntry
   - Returns the enriched list
2. Add session_id: int field to ActivityEntry in models.py
3. Add session_gap_minutes key to pa_config.yaml with default 30
4. Update report.py to render the new format:
   - Summary header block (total time, files touched, most active day)
   - Session blocks with header (session number, date, time range, duration, file count, dominant action_type)
   - Action type icons per activity line (✏️ EDIT, 📄 CREATE, 👁️ VIEW, 💬 COMMENT, etc.)
   - "Resume Here" section at the end (last edited file, last created file, last session end time)
5. Write unit tests for sessionize() in tests/test_processor.py covering:
   - Normal session grouping
   - Single activity (edge case)
   - All activities in one session
   - Gap exactly at threshold

Before writing any code, produce a plan Artifact.
```

***

### 🟠 Phase 1, Task 2 — Jinja2 Templates + Period Shortcuts

```
@CONTEXT.md @pa_assistant/report.py @pa_assistant/cli.py

TASK: Replace string concatenation in report.py with Jinja2 templates and add --period shortcuts to CLI.

SCOPE:
- pa_assistant/report.py
- templates/report.md.j2 (new file)
- pa_assistant/cli.py
- requirements.txt (add Jinja2)

STEPS:
1. Create templates/report.md.j2 implementing the same report structure currently in report.py, using Jinja2 syntax
2. Refactor report.py to use Jinja2 Environment to render the template instead of string concatenation
3. Add --period argument to cli.py supporting: today, yesterday, 7d, this-week, last-week
4. Map each --period value to start_date and end_date before passing to runner.py
5. When neither --period nor --start-date is provided, fall back to default_start_offset_days from pa_config.yaml

DO NOT change the report content or structure — only the rendering mechanism.
```

***

## Part 3 — After Each Task

After Antigravity completes each task, do this before moving to the next: [reddit](https://www.reddit.com/r/google_antigravity/comments/1qur1mr/practical_tips_to_improve_your_coding_workflow/)

1. **Read the plan Artifact** — verify it only touched the declared scope files
2. **Read the diff** — spot-check that no logic outside scope was altered
3. **Run the tests**: `python -m pytest`
4. **Do a quick manual test**: `python -m pa_assistant.cli --period yesterday`
5. **Commit**: `git commit -m "Phase 0 Task 1: OAuth 2.0 migration"` — one commit per task keeps rollback clean
