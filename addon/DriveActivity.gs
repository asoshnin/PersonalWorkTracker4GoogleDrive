const DriveActivityApi = {
  fetchActivities: function(startTime, endTime, scanScope, folderId) {
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
      
      if (scanScope === "my_drive") {
        payload.ancestorName = "items/root";
      } else if (scanScope === "specific_folder" && folderId) {
        payload.ancestorName = "items/" + folderId;
      } else if (scanScope === "all_drives") {
        payload.consolidationStrategy = { none: {} };
      }
      
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
    
    this.enrichWithFolderNames(activities);
    
    console.log(`Fetched ${activities.length} activities.`);
    return activities;
  },
  
  enrichWithFolderNames: function(activities) {
    if (!activities || activities.length === 0) return activities;
    
    const uniqueIds = [...new Set(activities.map(a => a.fileId).filter(Boolean))];
    if (uniqueIds.length === 0) return activities;
    
    const token = ScriptApp.getOAuthToken();
    const pathCache = {};
    
    uniqueIds.forEach(id => {
      pathCache[id] = this.getFullPath(id, token);
    });

    activities.forEach(a => {
      a.folderName = pathCache[a.fileId] || 'My Drive';
    });
    
    return activities;
  },

  getFullPath: function(fileId, token) {
    const visited = new Set();
    const pathParts = [];
    let currentId = fileId;
    
    // Walk up the parent chain (max 6 levels to avoid infinite loop)
    for (let i = 0; i < 6; i++) {
      if (visited.has(currentId)) break;
      visited.add(currentId);
      
      const url = 'https://www.googleapis.com/drive/v3/files/' + 
        currentId + 
        '?fields=id,name,parents,driveId' +
        '&supportsAllDrives=true';
      
      try {
        const resp = UrlFetchApp.fetch(url, {
          headers: { 'Authorization': 'Bearer ' + token },
          muteHttpExceptions: true
        });
        
        if (resp.getResponseCode() !== 200) break;
        
        const file = JSON.parse(resp.getContentText());
        
        // If this is root or has no parents - stop
        if (!file.parents || file.parents.length === 0) {
          // If it has a driveId it's a Shared Drive root
          if (file.driveId) {
            // Get shared drive name
            const driveUrl = 
              'https://www.googleapis.com/drive/v3/drives/' + 
              file.driveId;
            const driveResp = UrlFetchApp.fetch(driveUrl, {
              headers: { 'Authorization': 'Bearer ' + token },
              muteHttpExceptions: true
            });
            if (driveResp.getResponseCode() === 200) {
              const drive = JSON.parse(driveResp.getContentText());
              pathParts.unshift(drive.name);
            }
          }
          break;
        }
        
        pathParts.unshift(file.name);
        currentId = file.parents[0];
        
      } catch(e) {
        break;
      }
    }
    
    // Remove the file's own name (last element) since we 
    // want the folder path, not the file itself
    pathParts.pop();
    
    return pathParts.length > 0 ? pathParts.join(' / ') : 'My Drive';
  }
};
