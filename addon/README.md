Your draft is excellent—it strikes a perfect balance between a technical "map" and a user-friendly pointer to the main guide. I've polished it slightly to ensure the terminology matches the **Google Workspace** design language and clearly distinguishes between your two main features (the Tracker and the Cleaner).

Here is the refined version of your `addon/README.md`:

-----

# 🛠️ PA Assistant — Technical Add-on Summary

This directory contains the core source files for the Google Apps Script (GAS) deployment of the PA Assistant toolkit.

> [\!TIP]
> **Looking to install the Add-on?** \> Please follow the complete, step-by-step instructions in the **[Add-on Setup Guide](https://www.google.com/search?q=../ADDON_SETUP_GUIDE.md)** at the root of the project.

## 📂 File Architecture

This project is built using a hybrid architecture that combines local Python processing with native Google Apps Script UI elements.

| File | Module | Purpose |
| :--- | :--- | :--- |
| **`Code.gs`** | **Core** | Handles menu creation, server-side routing, and links the UI to the backend. |
| **`DriveActivity.gs`** | **Tracker** | Queries the Drive Activity API v2 and handles recursive folder mapping. |
| **`Processor.gs`** | **Tracker** | The "brain" of the tool; handles sessionization logic and data deduplication. |
| **`ReportGenerator.gs`** | **Tracker** | Generates the formatted Google Sheets and narrative Google Doc reports. |
| **`Sidebar.html`** | **Tracker** | The primary user interface for selecting periods, scopes, and session gaps. |
| **`Dialog.html`** | **Cleaner** | The UI for the "Substring Deleter," allowing custom delimiters and conditions. |
| **`Picker.html`** | **UI** | Manages the Google Picker API for visual folder selection. |
| **`SetupGuide.html`** | **Docs** | Provides the built-in setup instructions directly within the Workspace UI. |
| **`Stylesheet.html`** | **UI** | Enforces consistent Google Workspace styling across all tool menus. |

-----

## 💻 Developer Deployment (Clasp)

If you are a developer and want to skip the manual copy-pasting into the Apps Script editor, we support the `clasp` toolkit.

1. **Authorize:** Run `clasp login` to authenticate your terminal.
2. **Link:** Ensure your `.clasp.json` contains the correct `scriptId` for your project.
3. **Push:** Execute `clasp push -f` from this directory to upload the local source code to Google's servers.

> [\!WARNING]
> Remember to set your **`DEVELOPER_KEY`** inside the Script Properties at `script.google.com`. Without this, the Google Picker (folder selection) will not function.

-----
