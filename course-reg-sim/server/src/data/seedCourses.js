import { parseScheduleString } from "../core/time.js";

/**
 * Builds an in-memory store:
 * - coursesByCode: Map(code -> course)
 * - requiredCourseCodes: Set(code)
 * - lastSimulation: null | result
 */
export function initDataStore() {
  const store = {
    coursesByCode: new Map(),
    requiredCourseCodes: new Set(),
    lastSimulation: null
  };

  // ===== Required (zorunlu) ders kod listesi (seed) =====
  const required = [
    "YZM0205",
    "MAT0291",
    "MAT0295",
    "EDY0201",
    "ATA0101",
    "TUR0101"
  ];
  required.forEach((c) => store.requiredCourseCodes.add(c));

  // ===== Seed course set (50-100 arası) =====
  const baseCourses = [
    course("YZM0205", "Veri Yapıları", "Yapay Zeka ve Makine Öğrenme", 60, ["Salı 10:00-12:00"], []),
    course("MAT0291", "Diferansiyel Denklemler", "Yapay Zeka ve Makine Öğrenme", 70, ["Pazartesi 13:00-15:00"], []),
    course("MAT0295", "Ayrık Matematik", "Yapay Zeka ve Makine Öğrenme", 80, ["Çarşamba 10:00-12:00"], []),
    course("EDY0201", "Eleştirel Düşünme", "Ortak Dersler", 120, ["Perşembe 14:00-16:00"], []),
    course("ATA0101", "Atatürk İlkeleri", "Ortak Dersler", 300, ["Cuma 09:00-10:00"], []),
    course("TUR0101", "Türk Dili", "Ortak Dersler", 300, ["Cuma 10:00-11:00"], [])
  ];

  // More courses (generate)
  const generated = generateCoursePool(60); // toplam ~66 eder (base + generated unique)
  const all = [...baseCourses, ...generated];

  // Load into Map
  for (const c of all) {
    store.coursesByCode.set(c.code, c);
  }

  // Ensure required courses exist
  for (const rc of store.requiredCourseCodes) {
    if (!store.coursesByCode.has(rc)) {
      store.coursesByCode.set(rc, course(rc, `Zorunlu Ders ${rc}`, "Ortak Dersler", 120, ["Salı 09:00-10:00"], []));
    }
  }

  return store;
}

function course(code, name, dept, capacity, scheduleStrings, prereqs) {
  const schedule = scheduleStrings.map(parseScheduleString);
  return {
    code,
    name,
    dept,
    capacity,
    scheduleStrings,
    schedule, // normalized
    prereqs: prereqs || [],
    enrolledStudentIds: new Set(),
    waitlistStudentIds: []
  };
}

function generateCoursePool(count) {
  const depts = ["Bilgisayar", "Elektrik-Elektronik", "Makine", "Ortak Dersler", "Yapay Zeka ve Makine Öğrenme"];
  const days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"];
  const slots = [
    ["09:00", "10:00"],
    ["10:00", "12:00"],
    ["13:00", "15:00"],
    ["15:00", "17:00"]
  ];

  const list = [];
  let idx = 1;

  while (list.length < count) {
    const code = `BLM${String(100 + idx).padStart(3, "0")}`;
    const dept = depts[idx % depts.length];
    const name = `Ders ${idx} (${dept})`;
    const capacity = 40 + (idx % 6) * 10;

    const day = days[idx % days.length];
    const slot = slots[idx % slots.length];
    const scheduleStrings = [`${day} ${slot[0]}-${slot[1]}`];

    // Light prereq chain for some courses
    const prereqs = [];
    if (idx > 5 && idx % 7 === 0) {
      prereqs.push(`BLM${String(100 + (idx - 1)).padStart(3, "0")}`);
    }
    if (idx > 10 && idx % 11 === 0) {
      prereqs.push(`BLM${String(100 + (idx - 3)).padStart(3, "0")}`);
    }

    list.push({
      code,
      name,
      dept,
      capacity,
      scheduleStrings,
      schedule: scheduleStrings.map(parseScheduleString),
      prereqs,
      enrolledStudentIds: new Set(),
      waitlistStudentIds: []
    });

    idx++;
  }

  return list;
}
