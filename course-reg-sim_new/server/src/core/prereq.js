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

/**
 * Returns a richer explanation for missing prerequisites.
 *
 * Output:
 *  {
 *    missing: string[],
 *    paths: Array<{ missingCode: string, path: string[] }>
 *  }
 *
 * Example path: ["CS401", "CS301", "CS201"] => "CS201" is missing.
 */
export function explainMissingPrereqsForCourse(store, courseCode, completedCourses, thisTermRequested) {
  const missingSet = new Set();
  const paths = [];
  const visiting = new Set();

  function dfs(code, stack) {
    if (visiting.has(code)) return; // cycle guard
    visiting.add(code);

    const course = store.coursesByCode.get(code);
    if (!course) {
      visiting.delete(code);
      return;
    }

    for (const pre of course.prereqs || []) {
      const satisfied = completedCourses.has(pre) || thisTermRequested.has(pre);
      const nextStack = [...stack, pre];
      if (!satisfied) {
        if (!missingSet.has(pre)) {
          missingSet.add(pre);
          paths.push({ missingCode: pre, path: nextStack });
        }
      }
      dfs(pre, nextStack);
    }

    visiting.delete(code);
  }

  dfs(courseCode, [courseCode]);

  return {
    missing: Array.from(missingSet),
    paths
  };
}
