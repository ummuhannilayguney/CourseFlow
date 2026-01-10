const DAY_MAP = {
  "pazartesi": "Pazartesi",
  "salı": "Salı",
  "sali": "Salı",
  "çarşamba": "Çarşamba",
  "carsamba": "Çarşamba",
  "perşembe": "Perşembe",
  "persembe": "Perşembe",
  "cuma": "Cuma"
};

export function timeToMinutes(hhmm) {
  const [hStr, mStr] = hhmm.split(":");
  const h = Number(hStr);
  const m = Number(mStr);
  return h * 60 + m;
}

/**
 * Input: "Salı 10:00-12:00"
 * Output: { day, startMin, endMin, raw }
 */
export function parseScheduleString(str) {
  const raw = String(str || "").trim();
  // format: Day HH:MM-HH:MM
  const parts = raw.split(" ");
  if (parts.length < 2) {
    throw new Error(`Invalid schedule string: "${raw}"`);
  }
  const dayRaw = parts[0].toLowerCase();
  const day = DAY_MAP[dayRaw] || parts[0];

  const timePart = parts[1];
  const [start, end] = timePart.split("-");
  if (!start || !end) throw new Error(`Invalid time range in: "${raw}"`);

  const startMin = timeToMinutes(start);
  const endMin = timeToMinutes(end);
  if (!(startMin < endMin)) throw new Error(`Start must be < end in: "${raw}"`);

  return { day, startMin, endMin, raw };
}
