# Technical Audit: Personal Activity Tracking Assistant (Current State)
**Date**: 2026-03-19
**Project**: PersonalWorkTrackerApp
**Status**: Phase 1 MVP (CLI-based)

---

### 1. PROJECT STRUCTURE
- **Top-level Folders/Files**:
    - `pa_assistant/`: Core source package containing logic, models, and connectors.
    - `__DEVELOPMENT/`: Legacy reference implementations, PRDs, and implementation plans.
    - `reports/`: Default directory for generated Markdown reports.
    - `pa_config.yaml`: Active configuration file.
    - `pa_config.example.yaml`: Template for configuration.
    - `requirements.txt`: Python dependencies.
    - `README.md`: Project overview and rationale.
- **Entry Point**: `pa_assistant/cli.py` (contains `main()` function) or `python -m pa_assistant.cli`.
- **App Type**: A **CLI tool** (Command Line Interface).
- **Languages & Runtimes**: **Python 3.10+** is the primary runtime.

---

### 2. GOOGLE DRIVE / WORKSPACE INTEGRATION
- **Google APIs used**: 
    - **Google Drive API v3**: Specifically the `files().list()` method (`pa_assistant/connectors/drive.py:L64`).
- **OAuth 2.0 Scopes**: 
    - `https://www.googleapis.com/auth/drive.readonly` (`pa_assistant/connectors/drive.py:L16`).
- **Authentication**: 
    - Handled via **Service Account** JSON key file (`pa_assistant/connectors/drive.py:L41`). It uses `google.oauth2.service_account.Credentials.from_service_account_file`.
- **Credential Storage**: 
    - The path to the JSON key file is stored in `pa_config.yaml` under the `google_credentials_path` key (or interpreted from the config file).
- **Account Design**: Currently designed for a **single account** (the one the service account can access/masquerade as, or where it has shared permissions). It does not currently support multi-tenant OAuth flow for personal users.
- **Activity Data Fetched**: 
    - Fetches files matching a `modifiedTime` range (`pa_assistant/connectors/drive.py:L57`).
    - Fields requested: `id, name, modifiedTime, webViewLink, mimeType`.
- **Response Parsing**: 
    - The code iterates through the `files` list from the Drive response.
    - Maps `modifiedTime` to a Python `datetime` object.
    - Sets `description` as "Modified: [name]".
    - Captures `webViewLink` for the report and `mimeType` for metadata/comments.

---

### 3. DATA PROCESSING & LOGIC
- **Core Pipeline**: 
    1. CLI parses `start-date` and `end-date`.
    2. `runner.py` loads `pa_config.yaml`.
    3. Connectors (Drive, Gemini, Perplexity) fetch activities in parallel-ish sequence.
    4. Activities are normalized into `ActivityEntry` objects (`pa_assistant/models.py:L18`).
    5. `report.py` sorts all entries by timestamp.
    6. Markdown table is generated and written to a file in the `reports/` folder.
- **Sessionization**: **None**. There is no logic to group events by time gaps (e.g., "Session 1: 9:00 - 10:30").
- **Project/Folder Grouping**: **None**. It is a flat chronological list.
- **Time Range**: User-provided via CLI arguments `--start-date` and `--end-date` (`pa_assistant/cli.py:L50-51`).
- **LLM/AI Usage**: **None for summarization**. The tool *reads* logs from other AI tools (Gemini/Perplexity) but does not use an LLM API to interpret them yet.
- **Caching**: **None**. Every run fetches fresh data from APIs and local log files.

---

### 4. OUTPUT & REPORTING
- **Output Format**: **Markdown** file (`pa_assistant/report.py`).
- **Output Location**: Local file in the directory specified by `reports_dir` in `pa_config.yaml` (defaulting to `./reports`).
- **Template System**: Hardcoded string concatenation in `generate_markdown` (`pa_assistant/report.py:L27-63`). No external templating engine (like Jinja2) is used.
- **Customization**: Partially. Users can provide a `--focus` prompt via CLI which adds a "Focus" header to the report, but the table structure is fixed.

---

### 5. CONFIGURATION
- **Options**:
    - `reports_dir`: Path to save reports.
    - `enable_drive`, `enable_gemini_logs`, `enable_perplexity_logs`: Boolean flags to toggle connectors.
    - `google_credentials_path`: Path to Service Account JSON.
- **How they are set**: Mostly via `pa_config.yaml`. Date ranges and focus prompts are set via CLI arguments.
- **Non-Technical User Requirements**: Would need to edit `pa_config.yaml` and provide a Service Account JSON (high friction).
- **Hardcoded Values**:
    - `~/.personal-summarizer/gemini_history.json` and `perplexity_history.json` are hardcoded as local source paths (`pa_assistant/connectors/llm_logs.py:L45, L88`).

---

### 6. CURRENT UX / INTERFACE
- **Workflow (Clone to Output)**:
    1. Clone repo.
    2. Create a virtual environment and `pip install -r requirements.txt`.
    3. Setup Google Cloud Project, enable Drive API, create Service Account, download JSON key.
    4. Configure `pa_config.yaml` with the JSON key path.
    5. Run: `python -m pa_assistant.cli --start-date 2026-03-18 --end-date 2026-03-19 --config pa_config.yaml`.
- **Knowledge Required**: Python environment management, YAML editing, Google Cloud Console navigation (Service Accounts/IAM).
- **Error Handling**: Basic `try-except` blocks around API calls and file reading; errors are logged via Python `logging`.
- **UI**: **CLI only**.

---

### 7. DEPENDENCIES & DEPLOYMENT
- **Dependencies** (`requirements.txt`):
    - `google-api-python-client` (v2.0.0+)
    - `google-auth`, `google-auth-oauthlib` (v2.0.0+ / v1.0.0+)
    - `python-dateutil` (v2.8.0+)
    - `PyYAML` (v6.0.0+)
- **Deployment**: Local execution only. No Dockerfile or cloud deployment scripts currently exist.
- **Environment Assumptions**: Assumes a Unix-like home directory structure for LLM logs (`Path.home()`), though `pathlib` handles basic Windows compatibility.

---

### 8. KNOWN LIMITATIONS & TECH DEBT
- **Service Account Limitation**: Using a Service Account means the tool doesn't "see" a user's Drive unless files are explicitly shared with the service account email or Domain-Wide Delegation is set up.
- **Fragile Log Paths**: Local JSONL log paths for Gemini/Perplexity are hardcoded to a specific hidden folder in the home directory.
- **Memory Consumption**: Loads all activities for the date range into memory before generating the report.
- **No Drive Activity API**: It uses the standard Drive API `files.list` based on `modifiedTime`. This misses *reads*, *comments*, or *renames* that don't trigger a `modifiedTime` update on the file itself.
- **Security**: Service account keys stored as local files are a security risk if not managed correctly.

---

### 9. TEST COVERAGE
- **Automated Tests**: **None**.
- **Critical Areas to Test**: 
    - `drive.py`: Mocking the Google API response.
    - `llm_logs.py`: Parsing edge cases in JSONL files (malformed lines).
    - `runner.py`: Date range filtering logic.

---

### 10. GOOGLE DRIVE ADD-ON READINESS
- **Apps Script Compatibility**: **None**. The current code is 100% Python.
- **Migration Path**: 
    - **Logic to Apps Script**: Authentication (using `ScriptApp.getOAuthToken()`) and Drive querying (using `DriveApp` or `Drive` advanced service) are much easier in Apps Script. 
    - **Backend Requirement**: If sophisticated LLM processing or cross-platform log aggregation (Gemini/Perplexity) is required, a backend service (Google Cloud Functions / Cloud Run) would be needed as Apps Script has limited runtime and external library support.
- **Blocks/Limits**: 
    - Apps Script's 6-minute execution limit might be hit if a user has thousands of modifications in a day.
    - Drive Activity API (v2) would be a better fit for an Add-on than the current `modifiedTime` query.
