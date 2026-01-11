import express from "express";
import { requireAuth } from "../config/auth.js";
import { runSimulation } from "../core/simulate.js";

const router = express.Router();

// Admin triggers simulation (or allow student too if you want, for now admin)
router.post("/run", requireAuth("admin"), (req, res) => {
  const store = req.app.locals.store;
  const result = runSimulation(store);
  res.json({ ok: true, result });
});

router.get("/last", (req, res) => {
  const store = req.app.locals.store;
  res.json({ ok: true, result: store.lastSimulation });
});

export default router;
