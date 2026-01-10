import { missingPrereqsForCourse } from "./prereq.js";
import { findConflicts } from "./conflict.js";
import { sortStudentsByPriority } from "./priority.js";
import { createMetrics, finalizeMetrics } from "./metrics.js";
import { addToWaitlist } from "./waitlist.js";

function isCourseMandatory(store, courseCode) {
  return store.requiredCourseCodes.has(courseCode);
}

function isRequestedRequired(cartItem) {
  return !!cartItem.required;
}

export function runSimulation(store) {
  // Reset enrollments + waitlists each run (RAM-based simulation)
  for (const c of store.coursesByCode.values()) {
    c.enrolledStudentIds = new Set();
    c.waitlistStudentIds = [];
  }

  const studentsArr = Array.from(store.students.values());
  sortStudentsByPriority(studentsArr);

  const metrics = createMetrics();
  const results = [];

  for (const student of studentsArr) {
    const approved = [];
    const rejected = [];
    const scheduleAccum = []; // list of schedule blocks of approved
    const thisTermRequested = new Set(); // co-requisite: approved + in-progress
    // Pre-fill with cart codes? (same term counts) -> allow prereq if it exists anywhere in cart
    // We'll add all cart codes here so prereqs count if they are in cart, even if later approved.
    for (const item of student.cart || []) thisTermRequested.add(item.code);

    for (const item of (student.cart || [])) {
      const code = item.code;
      const course = store.coursesByCode.get(code);
      if (!course) {
        rejected.push({ code, reason: "COURSE_NOT_FOUND" });
        continue;
      }

      // 1) prereq chain
      const missing = missingPrereqsForCourse(
        store,
        code,
        student.completedCourses || new Set(),
        thisTermRequested
      );
      if (missing.length) {
        metrics.rejectedByPrereq++;
        rejected.push({ code, reason: "PREREQ_MISSING", detail: missing });
        continue;
      }

      // 2) conflict check
      const conflicts = findConflicts(scheduleAccum, course.schedule);
      if (conflicts.length) {
        // conflict resolution rule:
        // - mandatory (code list) always stays
        // - else user-required stays
        // - if both mandatory -> cart order wins (existing approved stays, new rejected)
        // Here we treat "existing approved" as already chosen; new one tries to enter.

        const newIsMandatory = isCourseMandatory(store, code);
        const newIsReq = newIsMandatory || isRequestedRequired(item);

        // find a conflicting approved course code (first one)
        const conflictingApproved = findFirstConflictingApproved(store, approved, course);
        if (conflictingApproved) {
          const oldCode = conflictingApproved;
          const oldMandatory = isCourseMandatory(store, oldCode);
          const oldReq = oldMandatory || isStudentMarkedRequired(student, oldCode);

          // Decide keep which:
          // If old mandatory and new mandatory -> keep old (because it came earlier in cart)
          if (oldMandatory && newIsMandatory) {
            metrics.rejectedByConflict++;
            rejected.push({ code, reason: "CONFLICT_REQUIRED_REQUIRED", detail: { with: oldCode, conflicts } });
            continue;
          }

          // If new is mandatory/required and old is not, drop old
          if (newIsReq && !oldReq) {
            // drop old
            dropApprovedCourse(store, student, approved, scheduleAccum, oldCode);
            metrics.rejectedByConflict++; // counted as a conflict happened (optional)
            // continue to capacity check & enroll new
          } else {
            // keep old, reject new
            metrics.rejectedByConflict++;
            rejected.push({ code, reason: "CONFLICT", detail: { with: oldCode, conflicts } });
            continue;
          }
        } else {
          // no mapping found -> reject safely
          metrics.rejectedByConflict++;
          rejected.push({ code, reason: "CONFLICT", detail: { conflicts } });
          continue;
        }
      }

      // 3) capacity
      if (course.enrolledStudentIds.size >= course.capacity) {
        metrics.rejectedByCapacity++;
        rejected.push({ code, reason: "CAPACITY_FULL" });
        continue;
      }

      // 4) enroll
      course.enrolledStudentIds.add(student.id);
      approved.push(code);
      // add course schedule blocks
      for (const s of course.schedule) scheduleAccum.push(s);
    }

    results.push({
      id: student.id,
      classYear: student.classYear,
      remainingCourses: student.remainingCourses,
      gpa: student.gpa,
      approved,
      rejected,
      totalDemanded: approved.length + rejected.length,
      successCount: approved.length
    });
  }

  finalizeMetrics(metrics, store, results);

  const summary = {
    metrics,
    students: results,
    courses: Array.from(store.coursesByCode.values()).map(c => ({
      code: c.code,
      name: c.name,
      dept: c.dept,
      capacity: c.capacity,
      enrolled: c.enrolledStudentIds.size,
      waitlist: c.waitlistStudentIds.length,
      fillRate: c.capacity ? Math.round((c.enrolledStudentIds.size / c.capacity) * 100) / 100 : 0
    }))
  };

  store.lastSimulation = summary;
  return summary;
}

function findFirstConflictingApproved(store, approvedCodes, newCourse) {
  for (const code of approvedCodes) {
    const old = store.coursesByCode.get(code);
    if (!old) continue;
    const conflicts = findConflicts(old.schedule, newCourse.schedule);
    if (conflicts.length) return code;
  }
  return null;
}

function isStudentMarkedRequired(student, courseCode) {
  const item = (student.cart || []).find(x => x.code === courseCode);
  return !!(item && item.required);
}

function dropApprovedCourse(store, student, approved, scheduleAccum, oldCode) {
  // remove from approved list
  const idx = approved.indexOf(oldCode);
  if (idx >= 0) approved.splice(idx, 1);

  // remove schedule blocks of old course from scheduleAccum (rebuild for safety)
  const rebuilt = [];
  for (const code of approved) {
    const c = store.coursesByCode.get(code);
    if (!c) continue;
    for (const s of c.schedule) rebuilt.push(s);
  }
  scheduleAccum.length = 0;
  for (const s of rebuilt) scheduleAccum.push(s);

  // remove enrollment
  const oldCourse = store.coursesByCode.get(oldCode);
  if (oldCourse) oldCourse.enrolledStudentIds.delete(student.id);
}
