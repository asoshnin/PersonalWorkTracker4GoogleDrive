function onOpen(e) {
  // If we are in a Document
  try {
    DocumentApp.getUi().createMenu("PA Assistant")
      .addItem("Open Sidebar", "showSidebar")
      .addToUi();
  } catch (err) {
    // Alternatively Spreadsheet
    try {
      SpreadsheetApp.getUi().createMenu("PA Assistant")
        .addItem("Open Sidebar", "showSidebar")
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
