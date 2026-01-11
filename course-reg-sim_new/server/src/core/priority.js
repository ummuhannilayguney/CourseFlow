/**
 * Higher score => earlier
 * Rule:
 * - classYear desc
 * - remainingCourses asc
 * - gpa desc
 */
export function studentPriorityScore(s) {
  const classYear = s.classYear || 1;
  const remaining = Math.min(40, Math.max(0, s.remainingCourses || 0));
  const gpa = s.gpa || 0;

  // Mandatory priority rule (project requirement):
  // "Mezuniyet aşamasındaki son sınıflar önce kaydolur"
  // We model "mezuniyet aşaması" as: 4. sınıf ve kalan ders <= 5.
  const graduatingBoost = (classYear === 4 && remaining <= 5) ? 50_000_000 : 0;

  // Base ordering:
  // - classYear desc
  // - remainingCourses asc (less remaining => earlier)
  // - gpa desc
  const classScore = classYear * 1_000_000;
  const remainingScore = (40 - remaining) * 10_000;
  const gpaScore = Math.round(gpa * 100) * 10;

  // Bonus special cases (very small influence):
  const specialScore = (s.special?.doubleMajor ? 500 : 0) + (s.special?.scholarship ? 250 : 0);

  return graduatingBoost + classScore + remainingScore + gpaScore + specialScore;
}

export function sortStudentsByPriority(studentsArr) {
  return studentsArr.sort((a, b) => {
    const sa = studentPriorityScore(a);
    const sb = studentPriorityScore(b);
    return sb - sa;
  });
}
