/**
 * Prereq chain check with "same term counts".
 * completedCourses: Set<string>
 * thisTermRequested: Set<string> (cart codes approved/being processed)
 */
export function missingPrereqsForCourse(store, courseCode, completedCourses, thisTermRequested) {
  const visited = new Set();
  const missing = new Set();

  function dfs(code) {
    if (visited.has(code)) return;
    visited.add(code);

    const course = store.coursesByCode.get(code);
    if (!course) return;

    for (const pre of course.prereqs || []) {
      // If already completed OR will be taken this term, it's satisfied
      const satisfied = completedCourses.has(pre) || thisTermRequested.has(pre);
      if (!satisfied) {
        missing.add(pre);
      }
      dfs(pre);
    }
  }

  dfs(courseCode);
  return Array.from(missing);
}
