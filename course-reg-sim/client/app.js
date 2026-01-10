function setActiveNav() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".navlinks a").forEach(a => {
    const href = a.getAttribute("href");
    if (href === here) a.classList.add("active");
  });
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("studentId");
  location.href = "/login.html";
}

function renderUserPill() {
  const role = localStorage.getItem("role");
  const pill = document.getElementById("userPill");
  if (!pill) return;

  if (!role) {
    pill.innerHTML = `<span class="small">Giriş yapılmadı</span>`;
    return;
  }

  const label = role === "admin"
    ? "Admin"
    : `Öğrenci: ${localStorage.getItem("studentId") || ""}`;

  pill.innerHTML = `
    <span>${label}</span>
    <button class="btn btn-secondary" style="padding:8px 10px; border-radius:999px;" id="logoutBtn">Çıkış</button>
  `;
  document.getElementById("logoutBtn").addEventListener("click", logout);
}

window.addEventListener("DOMContentLoaded", () => {
  setActiveNav();
  renderUserPill();

  const page = document.body.getAttribute("data-page");
  if (page === "login") initLogin();
  if (page === "dashboard") initDashboard();
  if (page === "catalog") initCatalog();
  if (page === "cart") initCart();
  if (page === "simulate") initSimulate();
  if (page === "admin") initAdmin();
});

async function initLogin() {
  const adminForm = document.getElementById("adminLoginForm");
  const studentForm = document.getElementById("studentLoginForm");

  adminForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const password = document.getElementById("adminPassword").value;
    try {
      const r = await API.loginAdmin(password);
      localStorage.setItem("token", r.token);
      localStorage.setItem("role", "admin");
      location.href = "/dashboard.html";
    } catch (err) {
      alert("Admin giriş hatası: " + err.message);
    }
  });

  studentForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("studentId").value;
    const password = document.getElementById("studentPassword").value;
    try {
      const r = await API.loginStudent(id, password);
      localStorage.setItem("token", r.token);
      localStorage.setItem("role", "student");
      localStorage.setItem("studentId", r.studentId || id);
      location.href = "/dashboard.html";
    } catch (err) {
      alert("Öğrenci giriş hatası: " + err.message);
    }
  });
}

async function initDashboard() {
  const metricsEl = document.getElementById("metrics");
  const coursesEl = document.getElementById("topCourses");

  const last = await API.lastSimulation();
  const result = last.result;

  if (!result) {
    metricsEl.innerHTML = `<div class="small">Henüz simülasyon çalıştırılmadı. Admin → Simülasyon ekranından başlat.</div>`;
    coursesEl.innerHTML = `<div class="small">Simülasyon sonrası doluluklar burada görünecek.</div>`;
    return;
  }

  const m = result.metrics;
  metricsEl.innerHTML = `
    <div class="grid">
      ${kpi("Kontenjanı dolan ders", m.fullCoursesCount)}
      ${kpi("Kontenjan yüzünden reddedilen", m.rejectedByCapacity)}
      ${kpi("Çakışma yüzünden reddedilen", m.rejectedByConflict)}
      ${kpi("Ön şart yüzünden reddedilen", m.rejectedByPrereq)}
      ${kpi("Ortalama alınan ders", m.avgApprovedPerStudent)}
    </div>
  `;

  const top = result.courses
    .slice()
    .sort((a, b) => b.fillRate - a.fillRate)
    .slice(0, 8);

  coursesEl.innerHTML = top.map(c => courseRow(c)).join("");
}

function kpi(label, value) {
  return `
  <div class="card" style="grid-column: span 4;">
    <div class="kpi">
      <div class="value">${value}</div>
      <div class="label">${label}</div>
    </div>
  </div>`;
}

function courseRow(c) {
  const pct = Math.round((c.fillRate || 0) * 100);
  return `
  <div class="card mt12">
    <div class="spread">
      <div>
        <div style="font-weight:900">${c.code} · ${c.name}</div>
        <div class="small">${c.dept} · Kontenjan ${c.capacity} · Kayıt ${c.enrolled} · Waitlist ${c.waitlist}</div>
      </div>
      <span class="badge">%${pct}</span>
    </div>
    <div class="progress mt12"><div style="width:${pct}%"></div></div>
  </div>`;
}

async function initCatalog() {
  const q = document.getElementById("q");
  const list = document.getElementById("courseList");

  async function load() {
    const data = await API.listCourses(q.value);
    list.innerHTML = data.courses.map(c => {
      const pct = c.capacity ? Math.round((c.enrolled / c.capacity) * 100) : 0;
      const isFull = c.enrolled >= c.capacity;
      const prereqStr = c.prereqs?.length ? c.prereqs.join(", ") : "Yok";
      const role = localStorage.getItem("role");
      const studentId = localStorage.getItem("studentId");
      
      return `
      <div class="card mt12">
        <div class="spread">
          <div>
            <div style="font-weight:900">${c.code} · ${c.name}</div>
            <div class="small">${c.dept}</div>
            <div class="small">Saat: ${c.scheduleStrings.join(" + ")}</div>
            <div class="small">Ön şart: ${prereqStr}</div>
          </div>
          <div style="text-align:right;">
            <span class="badge">${isFull ? "DOLU" : c.enrolled + "/" + c.capacity}</span>
            ${c.waitlist > 0 ? `<div class="small">Waitlist: ${c.waitlist}</div>` : ""}
          </div>
        </div>
        <div class="progress mt12"><div style="width:${pct}%;"></div></div>
        ${isFull && role === "student" ? `
          <div class="mt12">
            <button class="btn btn-secondary waitBtn" data-code="${c.code}" style="font-size:12px;">Waitlist'e Ekle</button>
          </div>
        ` : ""}
      </div>`;
    }).join("");

    list.querySelectorAll(".waitBtn").forEach(b => {
      b.addEventListener("click", async () => {
        const code = b.dataset.code;
        try {
          await API.addWaitlist(code);
          alert(`${code} waitlist'ine eklendi.`);
        } catch (err) {
          alert("Waitlist hatası: " + err.message);
        }
      });
    });
  }

  document.getElementById("searchBtn").addEventListener("click", load);
  q.addEventListener("keydown", (e) => { if (e.key === "Enter") load(); });
  await load();
}

async function initCart() {
  const role = localStorage.getItem("role");
  if (role !== "student") {
    document.getElementById("cartRoot").innerHTML = `<div class="card">Bu sayfa sadece öğrenci içindir. <a href="/login.html">Giriş yap</a></div>`;
    return;
  }

  const me = await API.getMe();
  let cart = me.student.cart || [];

  const root = document.getElementById("cartRoot");
  const saveBtn = document.getElementById("saveCartBtn");

  function render() {
    root.innerHTML = `
      <table class="table">
        <thead><tr><th>Sıra</th><th>Ders</th><th>Required</th><th>İşlem</th></tr></thead>
        <tbody>
          ${cart.map((it, idx) => `
            <tr>
              <td>${idx + 1}</td>
              <td style="font-weight:800">${it.code}</td>
              <td>
                <input type="checkbox" ${it.required ? "checked" : ""} data-idx="${idx}" class="reqChk"/>
              </td>
              <td class="row">
                <button class="btn btn-secondary upBtn" data-idx="${idx}">↑</button>
                <button class="btn btn-secondary downBtn" data-idx="${idx}">↓</button>
                <button class="btn btn-secondary delBtn" data-idx="${idx}">Sil</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      <div class="small mt12">Not: Zorunlu ders kod listesi ayrıca sistemde sabittir; burada required işareti de çakışma çözümünde etkili olur.</div>
    `;

    root.querySelectorAll(".reqChk").forEach(el => {
      el.addEventListener("change", () => {
        const idx = Number(el.dataset.idx);
        cart[idx].required = el.checked;
      });
    });

    root.querySelectorAll(".upBtn").forEach(b => b.addEventListener("click", () => {
      const i = Number(b.dataset.idx);
      if (i <= 0) return;
      [cart[i-1], cart[i]] = [cart[i], cart[i-1]];
      render();
    }));

    root.querySelectorAll(".downBtn").forEach(b => b.addEventListener("click", () => {
      const i = Number(b.dataset.idx);
      if (i >= cart.length - 1) return;
      [cart[i+1], cart[i]] = [cart[i], cart[i+1]];
      render();
    }));

    root.querySelectorAll(".delBtn").forEach(b => b.addEventListener("click", () => {
      const i = Number(b.dataset.idx);
      cart.splice(i, 1);
      render();
    }));
  }

  saveBtn.addEventListener("click", async () => {
    // normalize ranks
    cart = cart.map((x, idx) => ({ ...x, rank: idx }));
    try {
      await API.saveCart(cart);
      alert("Sepet kaydedildi.");
    } catch (e) {
      alert("Kaydetme hatası: " + e.message);
    }
  });

  render();
}

async function initSimulate() {
  const role = localStorage.getItem("role");
  const runBtn = document.getElementById("runBtn");
  const out = document.getElementById("simOut");

  if (role !== "admin") {
    out.innerHTML = `<div class="card">Bu sayfa sadece admin içindir. <a href="/login.html">Giriş yap</a></div>`;
    runBtn.disabled = true;
    return;
  }

  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    runBtn.textContent = "Çalışıyor...";
    try {
      const r = await API.runSimulation();
      const m = r.result.metrics;
      out.innerHTML = `
        <div class="card">
          <div style="font-weight:900; font-size:18px;">Simülasyon tamamlandı</div>
          <div class="small mt12"><strong>Genel Metrikler:</strong></div>
          <ul class="small">
            <li>Toplam talep edilen ders: ${m.totalDemanded}</li>
            <li>Toplam onaylanan ders: ${m.totalApproved}</li>
            <li>Genel başarı oranı: %${m.overallSuccessRate}</li>
            <li>Zorunlu ders başarı oranı: %${m.mandatoryCourseSuccessRate}</li>
            <li>Öğrenci başına ortalama alınan ders: ${m.avgApprovedPerStudent}</li>
          </ul>
          <div class="small mt12"><strong>Reddi Sebepleri:</strong></div>
          <ul class="small">
            <li>Kontenjanı dolan ders: ${m.fullCoursesCount}</li>
            <li>Kontenjan nedeniyle reddedilen: ${m.rejectedByCapacity}</li>
            <li>Çakışma nedeniyle reddedilen: ${m.rejectedByConflict}</li>
            <li>Ön şart nedeniyle reddedilen: ${m.rejectedByPrereq}</li>
          </ul>
          <div class="small mt12" style="color: var(--muted);">Not: Sonuçlar dashboard'a yansıdı.</div>
        </div>
      `;
    } catch (e) {
      out.innerHTML = `<div class="card">Hata: ${e.message}</div>`;
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = "Simülasyonu Başlat";
    }
  });
}

async function initAdmin() {
  const role = localStorage.getItem("role");
  const root = document.getElementById("adminRoot");

  if (role !== "admin") {
    root.innerHTML = `<div class="card">Bu sayfa sadece admin içindir. <a href="/login.html">Giriş yap</a></div>`;
    return;
  }

  const form = document.getElementById("addCourseForm");
  const list = document.getElementById("adminCourseList");

  async function load() {
    const r = await API.adminCourses();
    list.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Kod</th><th>Ad</th><th>Bölüm</th><th>Kontenjan</th><th>Doluluk</th><th>Zorunlu</th><th></th></tr>
        </thead>
        <tbody>
          ${r.courses.map(c => `
            <tr>
              <td style="font-weight:900">${c.code}</td>
              <td>${c.name}</td>
              <td>${c.dept}</td>
              <td>${c.capacity}</td>
              <td>${c.enrolled}/${c.capacity} · WL:${c.waitlist}</td>
              <td>${c.mandatory ? "Evet" : "Hayır"}</td>
              <td><button class="btn btn-secondary delAdminBtn" data-code="${c.code}">Sil</button></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;

    list.querySelectorAll(".delAdminBtn").forEach(b => b.addEventListener("click", async () => {
      const code = b.dataset.code;
      if (!confirm(code + " silinsin mi?")) return;
      try {
        await API.adminDeleteCourse(code);
        await load();
      } catch (e) {
        alert("Silme hatası: " + e.message);
      }
    }));
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const course = {
      code: document.getElementById("c_code").value.trim(),
      name: document.getElementById("c_name").value.trim(),
      dept: document.getElementById("c_dept").value.trim(),
      capacity: Number(document.getElementById("c_capacity").value),
      scheduleStrings: [document.getElementById("c_sched").value.trim()],
      prereqs: document.getElementById("c_prereq").value.trim()
        ? document.getElementById("c_prereq").value.trim().split(",").map(s => s.trim())
        : []
    };

    try {
      await API.adminAddCourse(course);
      form.reset();
      await load();
    } catch (e2) {
      alert("Ekleme hatası: " + e2.message);
    }
  });

  await load();
}
