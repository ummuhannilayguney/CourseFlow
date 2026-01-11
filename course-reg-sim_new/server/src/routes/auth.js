import express from "express";
import { signToken } from "../config/auth.js";

const router = express.Router();

router.post("/login", (req, res) => {
  const { role, id, password } = req.body || {};

  if (role === "admin") {
    const adminPass = process.env.ADMIN_PASSWORD || "admin123";
    if (password !== adminPass) {
      return res.status(401).json({ ok: false, error: "INVALID_CREDENTIALS" });
    }
    const token = signToken({ role: "admin", id: "admin" });
    return res.json({ ok: true, token, role: "admin" });
  }

  if (role === "student") {
    const testId = process.env.TEST_STUDENT_ID || "S0001";
    const testPass = process.env.TEST_STUDENT_PASSWORD || "student123";

    if (id !== testId || password !== testPass) {
      return res.status(401).json({ ok: false, error: "INVALID_CREDENTIALS" });
    }
    const token = signToken({ role: "student", id });
    return res.json({ ok: true, token, role: "student", studentId: id });
  }

  return res.status(400).json({ ok: false, error: "BAD_REQUEST" });
});

export default router;
