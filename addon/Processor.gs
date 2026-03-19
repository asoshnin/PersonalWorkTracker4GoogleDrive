const Processor = {
  sessionize: function(activities, gapMinutes) {
    if (!activities || activities.length === 0) return [];
    
    activities.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    
    let sessionId = 1;
    let enriched = [];
    
    enriched.push({
      ...activities[0],
      sessionId: sessionId
    });
    
    for (let i = 1; i < activities.length; i++) {
      let prev = activities[i-1].timestamp.getTime();
      let curr = activities[i].timestamp.getTime();
      
      let diffMins = (curr - prev) / (1000 * 60);
      if (diffMins > gapMinutes) {
        sessionId++;
      }
      
      enriched.push({
        ...activities[i],
        sessionId: sessionId
      });
    }
    
    return enriched;
  },
  
  deduplicate: function(activities) {
    if (!activities || activities.length === 0) return [];
    
    const dedupedMap = {};
    
    for (let i = 0; i < activities.length; i++) {
      let act = activities[i];
      let key = `${act.sessionId}_${act.fileName}_${act.actionType}`;
      
      if (!dedupedMap[key]) {
        dedupedMap[key] = act;
      } else {
        if (act.timestamp.getTime() > dedupedMap[key].timestamp.getTime()) {
          dedupedMap[key] = act;
        }
      }
    }
    
    let result = Object.values(dedupedMap);
    result.sort((a, b) => {
      if (a.sessionId !== b.sessionId) return a.sessionId - b.sessionId;
      return a.timestamp.getTime() - b.timestamp.getTime();
    });
    
    return result;
  }
};
