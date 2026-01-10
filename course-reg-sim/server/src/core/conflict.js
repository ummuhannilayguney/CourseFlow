function overlaps(a, b) {
  // same day assumed
  return a.startMin < b.endMin && b.startMin < a.endMin;
}

export function findConflicts(currentScheduleArr, newCourseScheduleArr) {
  const conflicts = [];
  for (const s1 of currentScheduleArr) {
    for (const s2 of newCourseScheduleArr) {
      if (s1.day === s2.day && overlaps(s1, s2)) {
        conflicts.push({
          day: s1.day,
          range: `${minToHHMM(Math.max(s1.startMin, s2.startMin))}-${minToHHMM(Math.min(s1.endMin, s2.endMin))}`
        });
      }
    }
  }
  return conflicts;
}

function minToHHMM(min) {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}
