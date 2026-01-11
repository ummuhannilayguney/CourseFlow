import express from "express";
import { requireAuth } from "../config/auth.js";
import { parseScheduleString } from "../core/time.js";

const router = express.Router();

router.get("/courses", requireAuth("admin"), (req, res) => {
  const store = req.app.locals.store;
  const courses = Array.from(store.coursesByCode.values()).map(c => ({
    code: c.code,
    name: c.name,
    dept: c.dept,
    capacity: c.capacity,
    enrolled: c.enrolledStudentIds.size,
    waitlist: c.waitlistStudentIds.length,
    scheduleStrings: c.scheduleStrings,
    prereqs: c.prereqs,
    mandatory: store.requiredCourseCodes.has(c.code)
  }));
  res.json({ ok: true, courses });
});

router.post("/courses", requireAuth("admin"), (req, res) => {
  const store = req.app.locals.store;
  const { code, name, dept, capacity, scheduleStrings, prereqs } = req.body || {};
  if (!code || !name || !dept || !capacity || !Array.isArray(scheduleStrings)) {
    return res.status(400).json({ ok: false, error: "BAD_REQUEST" });
  }

  // validate schedules
  let schedule;
  try {
    schedule = scheduleStrings.map(parseScheduleString);
  } catch (e) {
    return res.status(400).json({ ok: false, error: "BAD_SCHEDULE", detail: String(e.message || e) });
  }

  store.coursesByCode.set(code, {
    code,
    name,
    dept,
    capacity: Number(capacity),
    scheduleStrings,
    schedule,
    prereqs: Array.isArray(prereqs) ? prereqs : [],
    enrolledStudentIds: new Set(),
    waitlistStudentIds: []
  });

  res.json({ ok: true });
});

router.delete("/courses/:code", requireAuth("admin"), (req, res) => {
  const store = req.app.locals.store;
  const code = req.params.code;

  if (!store.coursesByCode.has(code)) {
    return res.status(404).json({ ok: false, error: "NOT_FOUND" });
  }

  store.coursesByCode.delete(code);
  store.requiredCourseCodes.delete(code); // if it was mandatory
  res.json({ ok: true });
});

export default router;
