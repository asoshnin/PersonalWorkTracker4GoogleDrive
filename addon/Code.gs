function onOpen(e) {
  // If we are in a Document
  try {
    DocumentApp.getUi().createMenu("PA Assistant")
      .addItem("Open Sidebar", "showSidebar")
      .addItem("View Setup Guide", "showSetupGuide")
      .addSeparator()
      .addItem("Clean Up: Delete Substrings", "showDeleteSubstringDialog")
      .addToUi();
  } catch (err) {
    // Alternatively Spreadsheet
    try {
      SpreadsheetApp.getUi().createMenu("PA Assistant")
        .addItem("Open Sidebar", "showSidebar")
        .addItem("View Setup Guide", "showSetupGuide")
        .addSeparator()
        .addItem("Clean Up: Delete Substrings", "showDeleteSubstringDialog")
        .addToUi();
    } catch(err2) {
      // Ignore
    }
  }
}

function showSidebar() {
  const html = HtmlService.createTemplateFromFile("Sidebar").evaluate()
    .setTitle("PA Assistant");
  
  try {
    DocumentApp.getUi().showSidebar(html);
  } catch (err) {
    try {
      SpreadsheetApp.getUi().showSidebar(html);
    } catch(err2) {
      // Fallback
    }
  }
}

function showSetupGuide() {
  const html = HtmlService.createTemplateFromFile('SetupGuide').evaluate()
    .setWidth(750)
    .setHeight(600)
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);

  try {
    DocumentApp.getUi().showModalDialog(html, 'PA Assistant Setup Guide');
  } catch(e) {
    try {
      SpreadsheetApp.getUi().showModalDialog(html, 'PA Assistant Setup Guide');
    } catch(e2) {
      DriveApp.getUi 
        ? DriveApp.getUi().showModalDialog(html, 'PA Assistant Setup Guide')
        : SlidesApp.getUi().showModalDialog(html, 'PA Assistant Setup Guide');
    }
  }
}

function getUserTimezone() {
  return Session.getScriptTimeZone();
}

function getOAuthToken() {
  return ScriptApp.getOAuthToken();
}

function getDeveloperKey() {
  const key = PropertiesService.getScriptProperties()
    .getProperty('DEVELOPER_KEY');
  return key;
}

function showPickerDialog() {
  const oauthToken = ScriptApp.getOAuthToken();
  const developerKey = PropertiesService.getScriptProperties()
    .getProperty('DEVELOPER_KEY');
  
  const html = HtmlService.createTemplateFromFile('Picker');
  html.oauthToken = oauthToken;
  html.developerKey = developerKey;
  
  const dialog = html.evaluate()
    .setWidth(800)
    .setHeight(600)
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);

  try {
    DocumentApp.getUi().showModalDialog(dialog, 'Select folder to scan');
  } catch(e) {
    try {
      SpreadsheetApp.getUi().showModalDialog(dialog, 'Select folder to scan');
    } catch(e2) {
      DriveApp.getUi 
        ? DriveApp.getUi().showModalDialog(dialog, 'Select folder to scan')
        : SlidesApp.getUi().showModalDialog(dialog, 'Select folder to scan');
    }
  }
}

function setSelectedFolder(folderId, folderName) {
  PropertiesService.getUserProperties()
    .setProperties({
      'selectedFolderId': folderId,
      'selectedFolderName': folderName
    });
}

function getSelectedFolder() {
  const props = PropertiesService.getUserProperties()
    .getProperties();
  if (props.selectedFolderId) {
    return {
      folderId: props.selectedFolderId,
      folderName: props.selectedFolderName
    };
  }
  return null;
}

function generateReport(params) {
  try {
    const period = params.period || "24h";
    const scanScope = params.scanScope || "my_drive";
    const folderId = params.folderId || "";
    const outputFormat = params.outputFormat || "sheet_only";
    const sessionGap = parseInt(params.sessionGap) || 30;
    
    const now = new Date();
    let startTime, endTime = new Date(now.getTime());
    
    if (period === "24h") {
      startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    } else if (period === "7d") {
      startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    } else if (period === "this-week") {
      let day = now.getDay();
      let diff = now.getDate() - day + (day == 0 ? -6 : 1);
      startTime = new Date(now.setDate(diff));
      startTime.setHours(0, 0, 0, 0);
      endTime = new Date(); 
    } else if (period === "last-week") {
      let day = now.getDay();
      let diffToThisMonday = now.getDate() - day + (day == 0 ? -6 : 1);
      
      startTime = new Date(now.getTime());
      startTime.setDate(diffToThisMonday - 7);
      startTime.setHours(0, 0, 0, 0);
      
      endTime = new Date(now.getTime());
      endTime.setDate(diffToThisMonday - 1);
      endTime.setHours(23, 59, 59, 999);
    } else {
      startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }
    
    const rawActivities = DriveActivityApi.fetchActivities(startTime, endTime, scanScope, folderId);
    
    let sessionized = Processor.sessionize(rawActivities, sessionGap);
    let deduplicated = Processor.deduplicate(sessionized);
    
    let result = ReportGenerator.generate(deduplicated, {
      period: period,
      scanScope: scanScope,
      outputFormat: outputFormat,
      startDate: startTime,
      endDate: endTime
    });
    
    return result;
    
  } catch(e) {
    return { error: e.toString() };
  }
}

function testGenerateReport() {
  const params = {
    period: "7d",
    scanScope: "all_drives",
    folderId: "",
    folderName: "",
    outputFormat: "sheet_only",
    sessionGap: 30
  };
  const result = generateReport(params);
  console.log("Result:", JSON.stringify(result));
}

/**
 * Shows a custom HTML dialog to get start sequence, end sequence, and condition.
 */
function showDeleteSubstringDialog() {
  const htmlOutput = HtmlService.createHtmlOutputFromFile('Dialog')
      .setWidth(400)
      .setHeight(300);
  DocumentApp.getUi().showModalDialog(htmlOutput, 'Configure Substring Deletion');
}

/**
 * Escapes special characters in a string for use in a regular expression.
 */
function escapeRegExp(str) {
  if (typeof str !== 'string') {
    return ''; // Or throw an error, but for robustness return empty string
  }
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}

/**
 * Processes the deletion request from the HTML dialog.
 */
function processDeletion(startChars, endChars, condition) {
  const ui = DocumentApp.getUi();
  // Basic validation
  if (typeof startChars !== 'string' || typeof endChars !== 'string' || typeof condition !== 'string') {
      ui.alert("Error", "Invalid input types received.", ui.ButtonSet.OK);
      return "Error: Invalid input types.";
  }
  if (!startChars.trim() || !endChars.trim()) { // Use trim to ensure they are not just spaces
    ui.alert("Error", "Starting and ending sequences cannot be empty or just spaces.", ui.ButtonSet.OK);
    return "Error: Start or end sequence empty or just spaces.";
  }
  deleteSubstrings(startChars, endChars, condition.trim());
  return "Deletion process completed or attempted.";
}

/**
 * Deletes substrings from the document body based on start/end delimiters and a condition.
 * Replaces double spaces with single spaces after deletion.
 */
function deleteSubstrings(startChars, endChars, condition) {
  const ui = DocumentApp.getUi();
  const body = DocumentApp.getActiveDocument().getBody();

  Logger.log(`Starting deletion process. Start: "${startChars}", End: "${endChars}", Condition: "${condition}"`);

  let replacementsMade = 0;
  let spaceCleaningError = null;
  let spacesWereCleaned = false; // Flag to track if space cleaning made changes

  try {
    // Construct the regular expression dynamically
    const escapedStartChars = escapeRegExp(startChars);
    const escapedEndChars = escapeRegExp(endChars);

    if (escapedStartChars === '' && escapedEndChars === '') {
        ui.alert("Configuration Error", "Cannot proceed with empty start and end delimiters after escaping.", ui.ButtonSet.OK);
        return;
    }
    const regexPattern = escapedStartChars + ".*?" + escapedEndChars;
    if (regexPattern === ".*?") {
        ui.alert("Configuration Error", "The effective regular expression is too broad (matches everything). Please check delimiters.", ui.ButtonSet.OK);
        return;
    }
    const regex = new RegExp(regexPattern, "g");
    Logger.log("Constructed regex: " + regex.toString());

    let text = body.getText();
    const matches = [];
    let match;
    while ((match = regex.exec(text)) !== null) {
      matches.push({
        text: match[0],
        index: match.index,
        length: match[0].length
      });
    }
    Logger.log(`Found ${matches.length} potential substrings to delete.`);

    for (let i = matches.length - 1; i >= 0; i--) {
      const currentMatch = matches[i];
      if (condition === "" || currentMatch.text.includes(condition)) {
        body.editAsText().deleteText(currentMatch.index, currentMatch.index + currentMatch.length - 1);
        replacementsMade++;
      }
    }
    Logger.log(`Made ${replacementsMade} deletions.`);

  } catch (e) {
    Logger.log("ERROR during main deletion phase: " + e.toString() + " Stack: " + e.stack);
    ui.alert('Error During Deletion', 'An unexpected error occurred during the substring deletion phase: ' + e.message, ui.ButtonSet.OK);
    return; // Stop further processing if main deletion fails
  }

  // Space Cleaning Phase
  try {
    const currentBodyText = body.getText(); // Get text once for length check and before cleaning
    Logger.log("Starting space cleaning. Body text length: " + currentBodyText.length);
    if (currentBodyText.length > 0) {
      // Use regex to replace sequences of 2 or more literal spaces with a single space.
      // This is generally more robust and efficient.
      body.replaceText(" {2,}", " ");
      const textAfterCleaning = body.getText();
      if (currentBodyText !== textAfterCleaning) { // Compare with the initial text of this phase
        spacesWereCleaned = true;
      }
    } else {
      Logger.log("Skipping space cleaning as body is empty.");
    }
    Logger.log(`Finished space cleaning. Spaces were cleaned: ${spacesWereCleaned}`);
  } catch (e) {
    Logger.log("ERROR during space cleaning: " + e.toString() + " Stack: " + e.stack);
    spaceCleaningError = e.message || "Unknown error during space cleaning.";
  }

  // Final Notification Logic
  let finalTitle = "";
  let finalMessage = "";

  if (spaceCleaningError) {
    finalTitle = 'Macro Partially Completed';
    finalMessage = `Deleted ${replacementsMade} substring(s). `;
    finalMessage += `However, an error occurred during the space cleaning phase: "${spaceCleaningError}". The main deletions should be complete. Please check the document.`;
  } else {
    if (replacementsMade > 0 && spacesWereCleaned) {
      finalTitle = 'Macro Finished';
      finalMessage = `Deleted ${replacementsMade} substring(s). Cleaned up extra spaces.`;
    } else if (replacementsMade > 0 && !spacesWereCleaned) {
      finalTitle = 'Macro Finished';
      finalMessage = `Deleted ${replacementsMade} substring(s). No extra spaces needed cleaning.`;
    } else if (replacementsMade === 0 && spacesWereCleaned) {
      finalTitle = 'Macro Finished';
      finalMessage = `No matching substrings were found to delete. Cleaned up extra spaces.`;
    } else { // replacementsMade === 0 && !spacesWereCleaned
      finalTitle = 'No Changes Made';
      if (condition !== "") {
        finalMessage = `No substrings starting with "${startChars}" and ending with "${endChars}" and containing "${condition}" were found. No extra spaces needed cleaning.`;
      } else {
        finalMessage = `No substrings starting with "${startChars}" and ending with "${endChars}" were found. No extra spaces needed cleaning.`;
      }
    }
  }
  Logger.log(`Final Alert: Title: "${finalTitle}", Message: "${finalMessage}"`);
  ui.alert(finalTitle, finalMessage, ui.ButtonSet.OK);
}

/**
 * Checks if this is the user's first time running the add-on.
 */
function checkFirstRun() {
  const props = PropertiesService.getUserProperties();
  const hasSeenWelcome = props.getProperty('HAS_SEEN_WELCOME');
  return hasSeenWelcome === 'true';
}

/**
 * Marks the welcome onboarding as seen for the current user.
 */
function setWelcomeSeen() {
  PropertiesService.getUserProperties().setProperty('HAS_SEEN_WELCOME', 'true');
}
