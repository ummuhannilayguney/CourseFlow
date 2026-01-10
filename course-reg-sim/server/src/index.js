import express from "express";
import path from "path";
import { fileURLToPath } from "url";

import { initDataStore } from "./data/seedCourses.js";
import { seedStudents } from "./data/seedStudents.js";

import authRoutes from "./routes/auth.js";
import courseRoutes from "./routes/courses.js";
import studentRoutes from "./routes/students.js";
import adminRoutes from "./routes/admin.js";
import simulateRoutes from "./routes/simulate.js";

const app = express();
app.use(express.json());

// ===== In-memory DB =====
const store = initDataStore(); // courses + required list + waitlists + enrollments
store.students = seedStudents({
  count: 1000,
  courseCodes: Array.from(store.coursesByCode.keys()),
  requiredCourseCodes: store.requiredCourseCodes,
  testStudent: {
    id: process.env.TEST_STUDENT_ID || "S0001",
    password: process.env.TEST_STUDENT_PASSWORD || "student123"
  }
});

// Expose store to routes via app.locals
app.locals.store = store;

// ===== API Routes =====
app.use("/api/auth", authRoutes);
app.use("/api/courses", courseRoutes);
app.use("/api/students", studentRoutes);
app.use("/api/admin", adminRoutes);
app.use("/api/simulate", simulateRoutes);

// ===== Serve client static =====
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const clientDir = path.resolve(__dirname, "../../client");

app.use(express.static(clientDir));

// Default route
app.get("/", (req, res) => {
  res.sendFile(path.join(clientDir, "index.html"));
});

const port = Number(process.env.PORT || 3000);
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
