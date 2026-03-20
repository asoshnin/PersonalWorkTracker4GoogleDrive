# PA Assistant (Apps Script Add-on)

This directory contains the entire source payload for the Google Apps Script Google Workspace Add-on implementation. It functions independently utilizing a robust Sidebar layout embedding a native Google Picker graphical interface, fetching explicitly nested folder structures sequentially straight from Google's Drive Activity v2 architectures natively.

## Project Structure
- **`Sidebar.html`**: The main frontend view rendering configuration dropdowns querying nested Modal bindings natively executing parameter calls up into the GS logic.
- **`Picker.html`**: A fully isolated Modal dialog securely capturing the `DEVELOPER_KEY` resolving visual Google Picker flows traversing cross-origin boundaries uniformly mapping Folder IDs back accurately.
- **`Stylesheet.html`**: Native CSS parameters mapping standard Google Material Design aesthetics visually harmonizing Sidebar executions efficiently.
- **`Code.gs`**: The centralized GS backend API natively binding REST arrays handling parameter routing dynamically querying Apps Script User Properties isolating session metrics locally.
- **`DriveActivity.gs`**: The exclusive driver for executing backend OAuth endpoints manipulating Drive Activity API v2 logic handling exact recursive chunk looping mapping folder targets synchronously.
- **`Processor.gs`**: The core heuristic evaluation mapping duplicate modifications explicitly aggregating identical sequence chunks mapping chronological sessions intelligently evaluating output readability.
- **`ReportGenerator.gs`**: A robust JSON-to-Document GS API binding compiling processed payload chunks into robust Google Sheets and visually polished Google Docs markdown natively.

## Deployment Instructions (clasp)
1. Initialize `clasp login` locally targeting your Google Account.
2. Ensure you have mapped `clasp create` pointing `scriptId` appropriately if binding an external repo dynamically matching `./.clasp.json`.
3. Directly deploy by executing `clasp push -f` from within this `addon/` root cleanly transferring architectures sequentially overriding Google Editors smoothly.

## Native Dependencies
### Required Script Properties
Open your Google Apps Script Editor > Project Settings > **Script Properties**.
You MUST insert the following property dynamically matching an active Google Cloud key locally:
- `DEVELOPER_KEY`: Represents your Picker API credential parameter validating interactive Shared View layouts natively securely without leaking over Git endpoints gracefully.

### Required APIs
Ensure your associated Google Cloud Project has the following endpoints strictly enabled mapping specific execution permissions smoothly:
- Google Drive API
- Google Drive Activity API
- Google Docs API
- Google Sheets API
- Google Script API
