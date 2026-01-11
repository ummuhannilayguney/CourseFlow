const API = {
  async request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    const token = localStorage.getItem("token");
    if (auth && token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data?.error || "REQUEST_FAILED");
    }
    return data;
  },

  loginAdmin(password) {
    return this.request("/api/auth/login", { method: "POST", body: { role: "admin", password }, auth: false });
  },

  loginStudent(id, password) {
    return this.request("/api/auth/login", { method: "POST", body: { role: "student", id, password }, auth: false });
  },

  listCourses(query = "") {
    return this.request("/api/courses?query=" + encodeURIComponent(query), { auth: false });
  },

  getMe() {
    return this.request("/api/students/me", { method: "GET" });
  },

  saveCart(cart) {
    return this.request("/api/students/me/cart", { method: "POST", body: { cart } });
  },

  addWaitlist(courseCode) {
    return this.request("/api/students/me/waitlist", { method: "POST", body: { courseCode } });
  },

  adminCourses() {
    return this.request("/api/admin/courses", { method: "GET" });
  },

  adminAddCourse(course) {
    return this.request("/api/admin/courses", { method: "POST", body: course });
  },

  adminDeleteCourse(code) {
    return this.request("/api/admin/courses/" + encodeURIComponent(code), { method: "DELETE" });
  },

  runSimulation() {
    return this.request("/api/simulate/run", { method: "POST" });
  },

  lastSimulation() {
    return this.request("/api/simulate/last", { method: "GET", auth: false });
  }
};

window.API = API;
