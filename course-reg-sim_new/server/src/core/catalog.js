export function findCourse(store, code) {
  return store.coursesByCode.get(code) || null;
}

export function searchCourses(store, query) {
  const q = (query || "").trim().toLowerCase();
  const results = [];

  // Fast path: if user searched by an exact course code, return instantly (Map lookup)
  if (q) {
    const exact = store.coursesByCode.get(q.toUpperCase());
    if (exact) return [exact];
  }

  for (const c of store.coursesByCode.values()) {
    if (!q) {
      results.push(c);
      continue;
    }
    if (
      c.code.toLowerCase().includes(q) ||
      c.name.toLowerCase().includes(q) ||
      c.dept.toLowerCase().includes(q)
    ) {
      results.push(c);
    }
  }

  // Sort: code asc
  results.sort((a, b) => a.code.localeCompare(b.code));
  return results;
}
