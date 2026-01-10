import crypto from "crypto";

const TOKEN_SECRET = process.env.TOKEN_SECRET || "dev-secret-change-me";
const TOKEN_TTL_MS = 1000 * 60 * 60 * 6; // 6 hours

function base64url(input) {
  return Buffer.from(input).toString("base64").replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}
function unbase64url(input) {
  input = input.replace(/-/g, "+").replace(/_/g, "/");
  while (input.length % 4) input += "=";
  return Buffer.from(input, "base64").toString("utf8");
}

export function signToken(payload) {
  const now = Date.now();
  const body = {
    ...payload,
    iat: now,
    exp: now + TOKEN_TTL_MS
  };
  const bodyStr = JSON.stringify(body);
  const bodyB64 = base64url(bodyStr);

  const sig = crypto.createHmac("sha256", TOKEN_SECRET).update(bodyB64).digest("base64");
  const sigB64 = sig.replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `${bodyB64}.${sigB64}`;
}

export function verifyToken(token) {
  if (!token || typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length !== 2) return null;

  const [bodyB64, sigB64] = parts;
  const expected = crypto.createHmac("sha256", TOKEN_SECRET).update(bodyB64).digest("base64")
    .replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");

  if (expected !== sigB64) return null;

  let payload;
  try {
    payload = JSON.parse(unbase64url(bodyB64));
  } catch {
    return null;
  }

  if (!payload.exp || Date.now() > payload.exp) return null;
  return payload;
}

export function requireAuth(role /* "admin" | "student" */) {
  return (req, res, next) => {
    const header = req.headers.authorization || "";
    const token = header.startsWith("Bearer ") ? header.slice(7) : "";
    const payload = verifyToken(token);
    if (!payload) return res.status(401).json({ ok: false, error: "UNAUTHORIZED" });

    if (role && payload.role !== role) {
      return res.status(403).json({ ok: false, error: "FORBIDDEN" });
    }

    req.user = payload;
    next();
  };
}
