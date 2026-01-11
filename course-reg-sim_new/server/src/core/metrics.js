export function createMetrics() {
  return {
    totalDemanded: 0,           // total course requests
    fullCoursesCount: 0,        // courses at capacity
    rejectedByCapacity: 0,      // requests rejected for capacity
    rejectedByConflict: 0,      // requests rejected for conflict
    rejectedByPrereq: 0,        // requests rejected for missing prereq
    waitlistedCount: 0,         // requests placed on waitlist (bonus)
    droppedDueToConflict: 0,    // previously approved courses dropped by policy
    totalApproved: 0,           // total approved courses
    avgApprovedPerStudent: 0,   // average approved per student
    mandatoryCourseSuccessRate: 0, // % of required courses that student got
    overallSuccessRate: 0       // (totalApproved / totalDemanded) * 100
  };
}

export function finalizeMetrics(metrics, store, perStudentResults) {
  // full courses:
  let full = 0;
  for (const c of store.coursesByCode.values()) {
    if (c.enrolledStudentIds.size >= c.capacity) full++;
  }
  metrics.fullCoursesCount = full;

  // total demanded and approved
  let totalDemanded = 0;
  let totalApproved = 0;
  let totalMandatoryDemanded = 0;
  let totalMandatoryApproved = 0;

  for (const r of perStudentResults) {
    const totalCart = r.approved.length + r.rejected.length;
    totalDemanded += totalCart;
    totalApproved += r.approved.length;

    // count mandatory courses
    for (const code of r.approved) {
      if (store.requiredCourseCodes.has(code)) totalMandatoryApproved++;
    }

    for (const item of r.rejected) {
      if (store.requiredCourseCodes.has(item.code)) {
        totalMandatoryDemanded++;
      }
    }

    for (const code of r.approved) {
      if (store.requiredCourseCodes.has(code)) totalMandatoryDemanded++;
    }
  }

  metrics.totalDemanded = totalDemanded;
  metrics.totalApproved = totalApproved;

  // avg approved per student
  metrics.avgApprovedPerStudent = perStudentResults.length
    ? Math.round((totalApproved / perStudentResults.length) * 100) / 100
    : 0;

  // overall success rate: (approved / demanded) * 100
  metrics.overallSuccessRate = totalDemanded
    ? Math.round((totalApproved / totalDemanded) * 1000) / 10
    : 0;

  // mandatory success rate
  metrics.mandatoryCourseSuccessRate = totalMandatoryDemanded
    ? Math.round((totalMandatoryApproved / totalMandatoryDemanded) * 1000) / 10
    : 0;

  return metrics;
}
