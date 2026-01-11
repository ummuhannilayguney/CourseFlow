/**
 * Random student generator (deterministic)
 * - 1000 students
 * - Each has: classYear, remainingCourses, gpa, completedCourses(Set), cart(Array)
 * - Includes test student ID+password for login demo
 */

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick(rng, arr) {
  return arr[Math.floor(rng() * arr.length)];
}

function sampleUnique(rng, arr, k) {
  const copy = arr.slice();
  // Fisher-Yates partial shuffle
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, Math.min(k, copy.length));
}

export function seedStudents({ count, courseCodes, requiredCourseCodes, testStudent }) {
  const rng = mulberry32(123456); // deterministic seed
  const students = new Map();

  // Simple TR name pool (inspired by the OBS project seed)
  const firstNames = [
    "Ahmet", "Mehmet", "Ali", "Ayşe", "Fatma", "Zeynep", "Mustafa", "Elif", "Emre", "Selin",
    "Can", "Deniz", "Ece", "Mert", "Seda", "Berk", "Ceren", "Hakan", "Derya", "Oğuz"
  ];
  const lastNames = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Öztürk", "Yıldız", "Aydın", "Arslan", "Doğan",
    "Koç", "Aslan", "Kurt", "Polat", "Güneş", "Aksoy", "Eren", "Karaca", "Yalçın", "Taş"
  ];
  const specialStatusPool = [null, null, null, null, "disabled", "scholarship", "athlete", "honor", "doubleMajor"];

  const requiredArr = Array.from(requiredCourseCodes);

  for (let i = 1; i <= count; i++) {
    const id = `S${String(i).padStart(4, "0")}`;

    const firstName = pick(rng, firstNames);
    const lastName = pick(rng, lastNames);
    const email = `${id.toLowerCase()}@ogrenci.edu.tr`;

    const classYear = 1 + Math.floor(rng() * 4); // 1..4
    const remainingCourses = Math.max(0, Math.floor(rng() * 40) - (classYear - 1) * 5);
    const gpa = Math.round((2.0 + rng() * 2.0) * 100) / 100; // 2.00..4.00

    // completed courses: some subset
    const completedCount = Math.floor(rng() * 20);
    const completed = new Set(sampleUnique(rng, courseCodes, completedCount));

    // cart: 6..8 courses
    const cartSize = 6 + Math.floor(rng() * 3);
    const cartCodes = sampleUnique(rng, courseCodes, cartSize);

    // sprinkle required flags
    const cart = cartCodes.map((code, idx) => {
      const isReqFlag = (rng() < 0.15); // user "required" flag
      return { code, required: isReqFlag, rank: idx };
    });

    // Ensure some students request some required courses sometimes
    if (rng() < 0.35 && requiredArr.length > 0) {
      const rc = pick(rng, requiredArr);
      if (!cart.some(x => x.code === rc)) {
        cart.unshift({ code: rc, required: true, rank: -1 });
      }
    }

    students.set(id, {
      id,
      password: "pass" + id, // default password pattern (not used in UI)
      firstName,
      lastName,
      email,
      classYear,
      remainingCourses,
      gpa,
      special: {
        // keep old boolean flags for backwards-compat
        doubleMajor: rng() < 0.05,
        scholarship: rng() < 0.1,
        // add a single-string special status for reporting
        status: pick(rng, specialStatusPool)
      },
      completedCourses: completed,
      cart
    });
  }

  // Add/override test student
  if (testStudent?.id) {
    const sid = testStudent.id;
    const exists = students.get(sid);
    const base = exists || {
      id: sid,
      classYear: 4,
      remainingCourses: 3,
      gpa: 3.5,
      special: { doubleMajor: false, scholarship: false },
      completedCourses: new Set(),
      cart: []
    };

    students.set(sid, {
      ...base,
      id: sid,
      password: testStudent.password || "student123",
      firstName: base.firstName || "Test",
      lastName: base.lastName || "Student",
      email: base.email || `${sid.toLowerCase()}@ogrenci.edu.tr`
    });
  }

  return students;
}
