# PA Assistant — Add-on Setup Guide

*This guide is also accessible directly within the PA Assistant add-on via the **Extensions → PA Assistant → View Setup Guide** menu.*

This guide walks you through the exact steps needed to deploy your own instance of the PA Assistant Add-on to your Google Workspace. You do not need any coding experience to complete this.

## Phase 1: Create the Apps Script Project
1. Go to [script.google.com](https://script.google.com).
2. Click **New project** in the top left corner.
3. Name the new project "PA Assistant".
4. Copy all `.gs` and `.html` files from the [addon/](addon/) directory into this new project. (Alternatively, developers can use the `clasp push` tool).
5. Open your `appsscript.json` manifest file in the Editor and replace its contents with the one provided in the `addon/` folder.

## Phase 2: Create a Google Cloud Project
Google requires a dedicated Cloud Project to access the Drive Activity logs and the Google Picker folder selection feature.
1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Click the project dropdown at the top and select **New Project**. Name it "PA Assistant Cloud" and click Create.
3. Ensure the project is selected. In the left menu, click **APIs & Services** → **Library**.
4. Search for and explicitly enable these three APIs:
   - **Google Drive API**
   - **Google Drive Activity API**
   - **Google Picker API**

## Phase 3: Link Apps Script to Google Cloud
1. In your Google Cloud Console, click the three dots in the top right and select **Project settings**. Copy the **Project number** (a long string of numbers).
2. Go back to your Apps Script Editor (script.google.com).
3. Click the gear icon (⚙️) for **Project Settings**.
4. Under "Google Cloud Platform (GCP) Project", click **Change project**.
5. Paste your Project number and click Set project.

## Phase 4: Get a Google Picker API Key
1. Go back to your Google Cloud Console.
2. Go to **APIs & Services** → **Credentials**.
3. Click **Create Credentials** at the top, then select **API Key**.
4. A popup will appear with your new key. Copy it.

## Phase 5: Set the Developer Key
1. Go back to your Apps Script Editor.
2. Click the gear icon (⚙️) for **Project Settings**.
3. Scroll down to the **Script Properties** section.
4. Click **Add script property**.
5. Set the Property name exactly as: `DEVELOPER_KEY`
6. Paste the API Key you copied from Phase 4 into the Value box.
7. Click **Save script properties**.

You are officially done! You can now open a Google Document in your drive, and the PA Assistant script will authenticate and run flawlessly.

## Sharing with your Team
Once the add-on is set up, you can easily share it with your colleagues so they don't have to repeat these steps.
1. Open the PA Assistant project at script.google.com.
2. Click the **Share** button in the top right corner.
3. Type in the Google email addresses of your team members.
4. Grant them **Editor** or **Viewer** access.
5. They can now run the Add-on instantly from their own Google Documents!
