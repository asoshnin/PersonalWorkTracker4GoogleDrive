# PA Assistant — Personal Activity Tracker for Google Drive

> Track what you worked on and resume where you left off.
> Generates structured activity reports from your Google Drive.

## What it does
PA Assistant connects securely to your Google Drive and aggregates all the scattered file changes you've made over a given period into a clean, concise, human-readable summary. Whether you're tracking billable hours or simply recalling where you left off in your latest sprint, this tool parses your activity logs automatically and clusters them into distinct, chronological work sessions.

## Features
- **Sessionization**: Intelligently groups rapid sequential edits on the same file into unified work blocks gracefully defining continuous tracking chunks.
- **Deep Drive Support**: Natively accesses My Drive folders alongside Shared Drives extracting real hierarchical system pathways mapping identically into human outputs.
- **Visual Folder Selection**: Utilizes a fully interactive native Google Picker allowing granular scoping explicitly on targeted folders bypassing rigid search constraints.
- **Dynamic Outputs**: Generates comprehensive Google Sheets equipped with distinct overview reports alongside robust chronological Activity Logs, strictly augmented by optional rich Markdown-style Google Docs text reports.

## Two ways to use it

### Option 1: Google Docs Add-on (recommended)
No installation required. Works directly in Google Docs.
1. Deploy the Add-on explicitly pointing your Google Account context natively to the `addon/` root scripts via Google Apps Script. 
2. Set your `DEVELOPER_KEY` configuration natively in the Editor's Script Properties.
3. Open any Google Document, click **Extensions** > **PA Assistant** > **Open Sidebar**.
4. Configure your scan period, optional specific drives (via the Picker UI), and generate the final layout outputs completely automatically directly into your Drive environment!

### Option 2: Python CLI (for developers)
Run PA Assistant fully headless driving complex execution queries natively mapping JSON configuration contexts dynamically from your terminal.

## Setup (CLI only)

### Prerequisites
- Python 3.10+
- Google Cloud Project with Drive API and Drive Activity API enabled
- OAuth 2.0 credentials (`client_secret.json`)

### Installation
```bash
git clone https://github.com/asoshnin/PersonalWorkTracker4GoogleDrive
cd PersonalWorkTracker4GoogleDrive
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp pa_config.example.yaml pa_config.yaml
# Edit pa_config.yaml with your paths
python setup_auth.py
```

### Usage
```bash
# Last 24 hours
python -m pa_assistant.cli --period today

# Last week
python -m pa_assistant.cli --period last-week

# Custom date range
python -m pa_assistant.cli --start-date 2026-03-01 --end-date 2026-03-20
```

## Add-on Setup (for developers who want to self-host)
To deploy the Google Apps Script natively independently resolving local builds:
1. Ensure your Google Cloud Project has **Google Drive API**, **Google Drive Activity API**, and **Google Docs API** broadly enabled securely within the GCP constraints.
2. Initialize and deploy `addon/` executing `clasp push -f` straight into your new Script environment.
3. In the Apps Script Editor, traverse mapping **Project Settings** > **Script Properties**.
4. Insert exactly `DEVELOPER_KEY` securely caching your specific active Google Picker API configuration string.

## Configuration reference
| Key | Description | Default |
|-----|-------------|---------|
| `auth.client_secrets_file` | Absolute path mapping `client_secret.json` parameters. | `client_secret.json` |
| `auth.token_file` | Dynamic Output mapping parsing OAuth cache targets. | `token.json` |
| `output.dir` | Raw local filesystem root compiling CLI JSON log executions. | `reports` |
| `preferences.session_gap_minutes` | Number modeling grouping tolerance collapsing sequential Drive activity strings dynamically. | `30` |

## Project structure
- `addon/`: Source files explicitly defining the entire Google Apps Script HTML / GS logic deploying native modal Picker scopes securely mapping Sidebars directly.
- `pa_assistant/`: Root Python engine scripts evaluating Drive APIs headless iterating `Processor` heuristics manually.
- `tests/`: Structural Python test benches enforcing offline module resolutions cleanly.
- `pa_config.yaml`: The exclusive config map declaring internal system parameters securely away from GitHub version controls.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
MIT License
