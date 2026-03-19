const ReportGenerator = {
  formatTimestamp: function(date, tz) {
    let hours = date.getHours().toString().padStart(2, '0');
    let mins = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${mins}`;
  },

  formatDuration: function(minutes) {
    if (minutes < 1) return "< 1m";
    const hrs = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    if (hrs > 0) return `${hrs}h ${mins}m`;
    return `${mins}m`;
  },
  
  getActionIcon: function(actionType) {
    const icons = {
      EDIT: "✏️",
      CREATE: "📄",
      VIEW: "👁️",
      COMMENT: "💬",
      RENAME: "🏷️",
      MOVE: "📦",
      DELETE: "🗑️"
    };
    return icons[actionType.toUpperCase()] || "🔹";
  },
  
  getDominantAction: function(activities) {
    if (!activities || activities.length === 0) return "Unknown";
    const counts = {};
    for (const a of activities) {
      counts[a.actionType] = (counts[a.actionType] || 0) + 1;
    }
    let max = 0;
    let dom = "";
    for (const [key, val] of Object.entries(counts)) {
      if (val > max) {
        max = val;
        dom = key;
      }
    }
    const verbs = {
      EDIT: "Editing",
      CREATE: "Creating",
      VIEW: "Viewing",
      COMMENT: "Commenting",
      RENAME: "Renaming",
      MOVE: "Moving",
      DELETE: "Deleting"
    };
    return verbs[dom] || dom;
  },
  
  generate: function(activities, params) {
    const timeZone = Session.getScriptTimeZone();
    
    const sessions = {};
    for (const act of activities) {
      if (!sessions[act.sessionId]) sessions[act.sessionId] = [];
      sessions[act.sessionId].push(act);
    }
    
    // Create Google Sheet
    const startDateStr = Utilities.formatDate(params.startDate, timeZone, "yyyy-MM-dd");
    const endDateStr = Utilities.formatDate(params.endDate, timeZone, "yyyy-MM-dd");
    
    const sheetName = `PA Assistant · ${startDateStr} to ${endDateStr}`;
    const ss = SpreadsheetApp.create(sheetName);
    const sheet1 = ss.getSheets()[0];
    sheet1.setName("Sessions");
    sheet1.appendRow(["Session #", "Date", "Start", "End", "Duration", "Files", "Dominant Action"]);
    
    const sheet2 = ss.insertSheet("Activity Log");
    sheet2.appendRow(["Session #", "Date", "Time", "Action", "File Name", "Open Link"]);
    
    let totalMinutes = 0;
    
    Object.keys(sessions).forEach(sId => {
      const acts = sessions[sId];
      const start = acts[0].timestamp;
      const end = acts[acts.length - 1].timestamp;
      const durationMins = (end.getTime() - start.getTime()) / 60000;
      totalMinutes += durationMins;
      
      const fileSet = new Set();
      acts.forEach(a => fileSet.add(a.fileName));
      
      const sessionDate = Utilities.formatDate(start, timeZone, "yyyy-MM-dd");
      const startTimeStr = this.formatTimestamp(start, timeZone);
      const endTimeStr = this.formatTimestamp(end, timeZone);
      
      sheet1.appendRow([
        sId,
        sessionDate,
        startTimeStr,
        endTimeStr,
        this.formatDuration(durationMins),
        fileSet.size,
        this.getDominantAction(acts)
      ]);
      
      acts.forEach(a => {
        const actDate = Utilities.formatDate(a.timestamp, timeZone, "yyyy-MM-dd");
        const actTime = this.formatTimestamp(a.timestamp, timeZone);
        let linkVal = "-";
        if (a.webViewLink && a.webViewLink !== "-") {
          linkVal = `=HYPERLINK("${a.webViewLink}", "Open ↗")`;
        }
        const actionStr = `${this.getActionIcon(a.actionType)} ${a.actionType}`;
        sheet2.appendRow([sId, actDate, actTime, actionStr, a.fileName, linkVal]);
      });
    });
    
    // Formatting Helper
    const formatSheet = (sh, widths) => {
      sh.setFrozenRows(1);
      const header = sh.getRange(1, 1, 1, sh.getLastColumn());
      header.setBackground("#1a73e8").setFontColor("#ffffff").setFontWeight("bold");
      
      const lastRow = sh.getLastRow();
      if (lastRow > 1) {
        sh.getDataRange().createFilter();
        const bgColors = [];
        for (let r = 2; r <= lastRow; r++) {
          const color = (r % 2 === 0) ? "#f8f9fa" : "#ffffff";
          bgColors.push(Array(sh.getLastColumn()).fill(color));
        }
        sh.getRange(2, 1, lastRow - 1, sh.getLastColumn()).setBackgrounds(bgColors);
      }
      widths.forEach((w, i) => sh.setColumnWidth(i + 1, w));
    };
    
    formatSheet(sheet1, [80, 120, 80, 80, 90, 60, 140]);
    formatSheet(sheet2, [80, 100, 80, 100, 250, 90]);
    
    ss.setActiveSheet(sheet1);
    
    PropertiesService.getUserProperties().setProperty("pa_last_sheet_id", ss.getId());
    
    // Create Google Doc
    const docName = `PA Report · ${startDateStr} to ${endDateStr}`;
    const doc = DocumentApp.create(docName);
    const body = doc.getBody();
    
    body.insertParagraph(0, `📋 PA REPORT · ${startDateStr} to ${endDateStr}`)
      .setHeading(DocumentApp.ParagraphHeading.HEADING1);
    
    const numSessions = Object.keys(sessions).length;
    let editedCount = 0, createdCount = 0;
    const allFiles = new Set();
    
    activities.forEach(a => {
      allFiles.add(a.fileName);
      if (a.actionType === "EDIT") editedCount++;
      if (a.actionType === "CREATE") createdCount++;
    });
    
    const otherCount = activities.length - editedCount - createdCount;
    const durGlobal = this.formatDuration(totalMinutes);
    const dayName = Utilities.formatDate(params.startDate, timeZone, "EEEE");
    
    const summary = `⏱ ${durGlobal} across ${numSessions} sessions · 📁 ${allFiles.size} files (${editedCount} edited, ${createdCount} created, ${otherCount} other) · 🔥 ${dayName} most active · 📌 ${params.focus || "none"}`;
    
    body.appendParagraph(summary);
    body.appendHorizontalRule();
    
    Object.keys(sessions).forEach(sId => {
      const acts = sessions[sId];
      const start = acts[0].timestamp;
      const end = acts[acts.length - 1].timestamp;
      const durationMins = (end.getTime() - start.getTime()) / 60000;
      
      const sDay = Utilities.formatDate(start, timeZone, "EEEE yyyy-MM-dd");
      const sStart = this.formatTimestamp(start, timeZone);
      const sEnd = this.formatTimestamp(end, timeZone);
      
      const domAct = this.getDominantAction(acts);
      const headingText = `🟦 Session ${sId} · ${sDay} · ${sStart}–${sEnd} · ${this.formatDuration(durationMins)} · Mostly ${domAct}`;
      
      body.appendParagraph(headingText)
        .setHeading(DocumentApp.ParagraphHeading.HEADING2);
        
      const tableRows = [];
      tableRows.push(["Time", "Action", "File", "Link"]);
      
      acts.forEach(a => {
        const timeStr = this.formatTimestamp(a.timestamp, timeZone);
        const icon = this.getActionIcon(a.actionType);
        tableRows.push([timeStr, `${icon} ${a.actionType}`, a.fileName, a.webViewLink]);
      });
      
      const table = body.appendTable(tableRows);
      
      const headerRow = table.getRow(0);
      for (let c = 0; c < headerRow.getNumCells(); c++) {
        const cell = headerRow.getCell(c);
        cell.setBackgroundColor("#f3f3f3");
        cell.editAsText().setBold(true);
      }
      
      table.setColumnWidth(0, 60);
      table.setColumnWidth(1, 80);
      table.setColumnWidth(2, 200);
      table.setColumnWidth(3, 60);
      
      for (let r = 1; r < table.getNumRows(); r++) {
        const row = table.getRow(r);
        const linkCell = row.getCell(3);
        const urlRaw = linkCell.getText();
        if (urlRaw && urlRaw !== "-") {
          linkCell.setText("Open ↗");
          linkCell.editAsText().setLinkUrl(urlRaw);
        }
      }
    });
    
    body.appendHorizontalRule();
    body.appendParagraph("🚀 Resume Here").setHeading(DocumentApp.ParagraphHeading.HEADING2);
    
    let lastEdited = null;
    let lastCreated = null;
    
    for (let i = activities.length - 1; i >= 0; i--) {
      if (!lastEdited && activities[i].actionType === "EDIT") lastEdited = activities[i];
      if (!lastCreated && activities[i].actionType === "CREATE") lastCreated = activities[i];
      if (lastEdited && lastCreated) break;
    }
    
    const resumeTable = [["", "File", "Link", "Time"]];
    if (lastEdited) {
      resumeTable.push(["Last edited", lastEdited.fileName, lastEdited.webViewLink, Utilities.formatDate(lastEdited.timestamp, timeZone, "EEE d MMM, HH:mm z")]);
    }
    if (lastCreated) {
      resumeTable.push(["Last created", lastCreated.fileName, lastCreated.webViewLink, Utilities.formatDate(lastCreated.timestamp, timeZone, "EEE d MMM, HH:mm z")]);
    }
    
    if (resumeTable.length > 1) {
      const rTable = body.appendTable(resumeTable);
      
      const rHeaderRow = rTable.getRow(0);
      for (let c = 0; c < rHeaderRow.getNumCells(); c++) {
        const cell = rHeaderRow.getCell(c);
        cell.setBackgroundColor("#f3f3f3");
        cell.editAsText().setBold(true);
      }
      
      for (let r = 1; r < rTable.getNumRows(); r++) {
        const row = rTable.getRow(r);
        const linkCell = row.getCell(2);
        const urlRaw = linkCell.getText();
        if (urlRaw && urlRaw !== "-") {
          linkCell.setText("Open ↗");
          linkCell.editAsText().setLinkUrl(urlRaw);
        }
      }
    }
    
    if (activities.length > 0) {
      const lastSessionAct = activities[activities.length - 1];
      const endStr = Utilities.formatDate(lastSessionAct.timestamp, timeZone, "EEEE yyyy-MM-dd 'at' HH:mm z");
      body.appendParagraph(`Last session ended: ${endStr}`).setBold(true);
    } else {
      body.appendParagraph("Last session ended: No activity in this period.").setBold(true);
    }
    
    const pSheet = body.appendParagraph("📊 Full activity data: ");
    pSheet.appendText("Open Sheet ↗").setLinkUrl(ss.getUrl());
    
    PropertiesService.getUserProperties().setProperty("pa_last_doc_id", doc.getId());
    
    return {
      docUrl: doc.getUrl(),
      sheetUrl: ss.getUrl()
    };
  }
};
