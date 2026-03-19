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

function generateReport(params) {
  try {
    const period = params.period || "24h";
    const focus = params.focus || "";
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
    
    const rawActivities = DriveActivityApi.fetchActivities(startTime, endTime);
    
    let sessionized = Processor.sessionize(rawActivities, sessionGap);
    let deduplicated = Processor.deduplicate(sessionized);
    
    let result = ReportGenerator.generate(deduplicated, {
      period: period,
      focus: focus,
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
    period: "24h",
    focus: "",
    sessionGap: 30
  };
  const result = generateReport(params);
  console.log("Result:", JSON.stringify(result));
}
