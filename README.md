# 📊 PA Assistant (Activity Tracker & Document Cleaner)

PA Assistant is an integrated toolkit for Google Workspace designed to help you track your productivity across Google Drive and clean up your documents with surgical precision.

-----

## 🛠️ Included Tools

The project provides two distinct modules accessible from a single menu in Google Docs.

### 1\. The Activity Tracker

A smart logger that monitors your work across "My Drive" and **Shared Drives** to summarize your output.

* **Session Grouping:** It automatically groups file edits into logical "work sessions" rather than long, flat lists.
* **Comprehensive Logging:** Generates a Google Sheet with a full audit trail and folder paths.
* **Narrative Reports:** (Optional) Creates a readable Google Doc summarizing your progress and where to "Resume".
* **Visual Selection:** Uses the Google Picker to let you target specific folders for tracking.

### 2\. The Document Cleaner

A specialized utility designed to find and remove specific blocks of text based on custom markers.

* **Targeted Deletion:** Quickly removes text between delimiters like `[brackets]` or `{braces}`.
* **Content Scrubbing:** Useful for stripping internal "TODO" notes, citations, or placeholder text before sharing a final document.
* **Formatting Cleanup:** Automatically removes double spaces created during the deletion process.

-----

## 🚀 How to Use It

### Option 1: Google Docs Add-on (Recommended)

If the add-on has been shared with you, open any Google Doc and go to **Extensions** → **PA Assistant** → **Open Sidebar**.

> [\!IMPORTANT]
> If you are setting this up for the first time, please follow the **2-Minute Setup Guide** below.

### Option 2: CLI for Developers

The original Python tool is still available for local tracking.

1. **Requirements:** Python 3.10+, `client_secret.json` from Google Cloud.
2. **Setup:** Run `pip install -r requirements.txt` and configure `pa_config.yaml`.
3. **Auth:** Run `python setup_auth.py` to authenticate via OAuth 2.0.
4. **Run:** `python -m pa_assistant.cli --period last-week`.

-----

## 🏁 2-Minute Setup Guide (Internal Team Only)

Follow these steps to activate the tools in your account. You only need to do this once.

1. **Open the Project:** Click this direct link: **[PASTE YOUR DIRECT SCRIPT LINK HERE]**.
2. **Install:** Click the blue **Deploy** button → **Test deployments** → click **Install** next to "Editor Add-on".
3. **Launch:** Open any Google Doc, refresh the page, and go to **Extensions** → **PA Assistant**.
4. **Authorize:** When the "Google hasn't verified this app" screen appears, click **Advanced** → **Go to PA Assistant (unsafe)** → **Allow**.

-----

## 🚀 Backlog & Roadmap

### Phase 3: Marketplace Publication

We are currently working toward making this a one-click install for the entire world:

* **OAuth Verification:** Finalizing privacy policies and demo videos.
* **Consent Screen:** Switching user types from Internal to External.
* **Marketplace SDK:** Configuring store listings and high-resolution icons.
* **Public Release:** Once approved, users can install via the Marketplace without manual script access.

-----

**For Administrators:** For manual deployment or server-side configuration, see the [Add-on Setup Guide](../ADDON_SETUP_GUIDE.md).
