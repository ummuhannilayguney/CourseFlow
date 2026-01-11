export function addToWaitlist(store, courseCode, studentId) {
  const course = store.coursesByCode.get(courseCode);
  if (!course) return { ok: false, error: "COURSE_NOT_FOUND" };

  // already enrolled?
  if (course.enrolledStudentIds.has(studentId)) {
    return { ok: false, error: "ALREADY_ENROLLED" };
  }

  // already waitlisted?
  if (course.waitlistStudentIds.includes(studentId)) {
    return { ok: false, error: "ALREADY_WAITLISTED" };
  }

  course.waitlistStudentIds.push(studentId);
  return { ok: true };
}
