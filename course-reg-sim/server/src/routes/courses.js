import express from "express";
import { searchCourses } from "../core/catalog.js";

const router = express.Router();

router.get("/", (req, res) => {
  const store = req.app.locals.store;
  const query = req.query.query || "";
  const results = searchCourses(store, query).map(c => ({
    code: c.code,
    name: c.name,
    dept: c.dept,
    capacity: c.capacity,
    enrolled: c.enrolledStudentIds.size,
    waitlist: c.waitlistStudentIds.length,
    scheduleStrings: c.scheduleStrings,
    prereqs: c.prereqs
  }));

  res.json({ ok: true, courses: results });
});

router.get("/:code", (req, res) => {
  const store = req.app.locals.store;
  const code = req.params.code;
  const c = store.coursesByCode.get(code);
  if (!c) return res.status(404).json({ ok: false, error: "NOT_FOUND" });

  res.json({
    ok: true,
    course: {
      code: c.code,
      name: c.name,
      dept: c.dept,
      capacity: c.capacity,
      enrolled: c.enrolledStudentIds.size,
      waitlist: c.waitlistStudentIds.length,
      scheduleStrings: c.scheduleStrings,
      prereqs: c.prereqs
    }
  });
});

export default router;
