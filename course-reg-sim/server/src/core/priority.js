/**
 * Higher score => earlier
 * Rule:
 * - classYear desc
 * - remainingCourses asc
 * - gpa desc
 */
export function studentPriorityScore(s) {
  const classScore = (s.classYear || 1) * 1_000_000;
  const remainingScore = (40 - Math.min(40, Math.max(0, s.remainingCourses || 0))) * 10_000;
  const gpaScore = Math.round((s.gpa || 0) * 100) * 10;
  return classScore + remainingScore + gpaScore;
}

export function sortStudentsByPriority(studentsArr) {
  return studentsArr.sort((a, b) => {
    const sa = studentPriorityScore(a);
    const sb = studentPriorityScore(b);
    return sb - sa;
  });
}
