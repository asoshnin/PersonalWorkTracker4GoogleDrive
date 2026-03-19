const DriveActivityApi = {
  fetchActivities: function(startTime, endTime) {
    const activities = [];
    let pageToken = null;
    
    const startStr = startTime.toISOString();
    const endStr = endTime.toISOString();
    const filterStr = `time >= "${startStr}" AND time <= "${endStr}"`;
    
    const url = "https://driveactivity.googleapis.com/v2/activity:query";
    
    do {
      const payload = {
        filter: filterStr,
        pageSize: 100
      };
      
      if (pageToken) {
        payload.pageToken = pageToken;
      }
      
      const options = {
        method: "post",
        contentType: "application/json",
        headers: {
          "Authorization": "Bearer " + ScriptApp.getOAuthToken()
        },
        payload: JSON.stringify(payload),
        muteHttpExceptions: true
      };
      
      const response = UrlFetchApp.fetch(url, options);
      if (response.getResponseCode() !== 200) {
        throw new Error("Drive Activity API error: " + response.getContentText());
      }
      
      const data = JSON.parse(response.getContentText());
      const acts = data.activities;
      
      if (acts && acts.length > 0) {
        for (let i = 0; i < acts.length; i++) {
          const act = acts[i];
          
          let timestampStr = act.timestamp;
          if (!timestampStr && act.timeRange) {
            timestampStr = act.timeRange.endTime;
          }
          if (!timestampStr) continue;
          
          const timestamp = new Date(timestampStr);
          
          let fileName = "Unknown";
          let fileId = "";
          
          if (act.targets && act.targets.length > 0 && act.targets[0].driveItem) {
            fileName = act.targets[0].driveItem.title || "Unknown";
            const nameField = act.targets[0].driveItem.name;
            if (nameField) {
              fileId = nameField.replace("items/", "");
            }
          }
          
          let actionType = "EDIT";
          if (act.primaryActionDetail) {
            if (act.primaryActionDetail.create) actionType = "CREATE";
            else if (act.primaryActionDetail.comment) actionType = "COMMENT";
            else if (act.primaryActionDetail.rename) actionType = "RENAME";
            else if (act.primaryActionDetail.move) actionType = "MOVE";
            else if (act.primaryActionDetail.delete) actionType = "DELETE";
            else if (act.primaryActionDetail.restore) actionType = "RESTORE";
          }
          
          let webViewLink = "-";
          if (fileId) {
            webViewLink = `https://drive.google.com/file/d/${fileId}/view`;
          }
          
          activities.push({
            timestamp: timestamp,
            fileName: fileName,
            fileId: fileId,
            actionType: actionType,
            webViewLink: webViewLink
          });
        }
      }
      pageToken = data.nextPageToken;
      
    } while (pageToken);
    
    console.log(`Fetched ${activities.length} activities.`);
    return activities;
  }
};
