import express from "express";
import { requireAuth } from "../config/auth.js";
import { addToWaitlist } from "../core/waitlist.js";

const router = express.Router();

// Student profile (test student)
router.get("/me", requireAuth("student"), (req, res) => {
  const store = req.app.locals.store;
  const student = store.students.get(req.user.id);
  if (!student) return res.status(404).json({ ok: false, error: "STUDENT_NOT_FOUND" });

  res.json({
    ok: true,
    student: {
      id: student.id,
      classYear: student.classYear,
      remainingCourses: student.remainingCourses,
      gpa: student.gpa,
      cart: student.cart
    }
  });
});

// Update cart: replace whole cart (simple)
router.post("/me/cart", requireAuth("student"), (req, res) => {
  const store = req.app.locals.store;
  const student = store.students.get(req.user.id);
  if (!student) return res.status(404).json({ ok: false, error: "STUDENT_NOT_FOUND" });

  const { cart } = req.body || {};
  if (!Array.isArray(cart)) return res.status(400).json({ ok: false, error: "BAD_CART" });

  // validate
  for (const item of cart) {
    if (!item || typeof item.code !== "string") {
      return res.status(400).json({ ok: false, error: "BAD_CART_ITEM" });
    }
  }

  student.cart = cart.map((x, idx) => ({
    code: x.code,
    required: !!x.required,
    rank: Number.isFinite(x.rank) ? x.rank : idx
  }));

  res.json({ ok: true, cart: student.cart });
});

// Add to waitlist (user clicks button after capacity full)
router.post("/me/waitlist", requireAuth("student"), (req, res) => {
  const store = req.app.locals.store;
  const { courseCode } = req.body || {};
  if (!courseCode) return res.status(400).json({ ok: false, error: "BAD_REQUEST" });

  const r = addToWaitlist(store, courseCode, req.user.id);
  if (!r.ok) return res.status(400).json(r);

  res.json({ ok: true });
});

export default router;
