/* ── State ── */
let currentStep = 1;
let selectedCar  = null; // { id, name }
let selectedDate = null;
let selectedTime = null;

const TIME_SLOTS = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"];

/* ── DOM refs ── */
const statusEl = document.getElementById("lead-status");
const btnBack  = document.getElementById("wiz-back");
const btnNext  = document.getElementById("wiz-next");
const wizNav   = document.getElementById("wiz-nav");
const wizProg  = document.getElementById("wiz-progress");

function setStatus(text, type = "") {
  if (!statusEl) return;
  statusEl.textContent = text;
  statusEl.className  = `cs-form-status ${type}`.trim();
}

/* ── Step manager ── */
function showStep(step) {
  currentStep = step;

  for (let i = 1; i <= 3; i++) {
    const p = document.getElementById(`wiz-panel-${i}`);
    if (p) p.hidden = true;
  }
  const donePanel = document.getElementById("wiz-panel-done");
  if (donePanel) donePanel.hidden = true;

  if (step === 0) {
    /* Success state — show done panel, hide all chrome */
    if (donePanel) donePanel.hidden = false;
    if (wizNav)  wizNav.hidden  = true;
    if (wizProg) wizProg.hidden = true;
    if (statusEl) statusEl.textContent = "";
    /* Reset button so it doesn't stay as "Отправляем…" */
    btnNext.disabled    = false;
    btnNext.textContent = "Далее";
    return;
  }

  const panel = document.getElementById(`wiz-panel-${step}`);
  if (panel) panel.hidden = false;

  document.querySelectorAll(".wiz-step").forEach(s => {
    const n = parseInt(s.dataset.step);
    s.classList.toggle("active", n === step);
    s.classList.toggle("done",   n < step);
  });

  if (wizNav)  wizNav.hidden  = false;
  if (wizProg) wizProg.hidden = false;
  btnBack.hidden      = (step === 1);
  btnNext.textContent = step === 3 ? "Записаться" : "Далее";
  btnNext.disabled    = false;
  setStatus("");
}

/* ── Step 1: Car dropdown ── */
async function loadCars() {
  const sel = document.getElementById("car-select");

  try {
    const [cars, brands] = await Promise.all([
      fetch("/api/v1/cars").then(r => r.json()),
      fetch("/api/v1/brands").then(r => r.json()),
    ]);

    const brandMap = Object.fromEntries((brands || []).map(b => [b.id, b.name]));
    sel.innerHTML = '<option value="">— Выберите автомобиль —</option>';

    if (!cars || !cars.length) {
      sel.innerHTML = '<option value="">Нет доступных автомобилей</option>';
      return;
    }

    cars.forEach(car => {
      const brandName = brandMap[car.brand_id] || "";
      const name      = `${brandName} ${car.model_name}`.trim();
      const price     = car.base_price
        ? `${Number(car.base_price).toLocaleString("ru-RU")} $`
        : "по запросу";

      const opt = document.createElement("option");
      opt.value        = car.id;
      opt.textContent  = `${name} — ${price}`;
      opt.dataset.name = name;
      sel.appendChild(opt);
    });

    sel.addEventListener("change", () => {
      const opt = sel.options[sel.selectedIndex];
      if (opt && opt.value) {
        selectedCar = { id: parseInt(opt.value), name: opt.dataset.name };
      } else {
        selectedCar = null;
      }
      setStatus("");
    });

    /* Pre-select if car_id passed via URL */
    const urlCarId = new URLSearchParams(window.location.search).get("car_id");
    if (urlCarId) {
      const match = [...sel.options].find(o => o.value === urlCarId);
      if (match) {
        sel.value = urlCarId;
        sel.dispatchEvent(new Event("change"));
      }
    }

  } catch {
    sel.innerHTML = '<option value="">Не удалось загрузить автомобили</option>';
  }
}

/* ── Step 2: Time slots ── */
function buildSlots() {
  const grid    = document.getElementById("slots-grid");
  const dateInp = document.getElementById("pick-date");

  const today   = new Date().toISOString().split("T")[0];
  dateInp.min   = today;
  if (!dateInp.value) dateInp.value = today;

  grid.innerHTML = "";
  TIME_SLOTS.forEach(time => {
    const btn = document.createElement("button");
    btn.type        = "button";
    btn.className   = "slot-btn" + (time === selectedTime ? " selected" : "");
    btn.textContent = time;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".slot-btn").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedTime = time;
      setStatus("");
    });
    grid.appendChild(btn);
  });
}

/* ── Validation ── */
function validateStep(step) {
  if (step === 1 && !selectedCar) {
    setStatus("Выберите автомобиль из списка", "error");
    return false;
  }
  if (step === 2) {
    const date = document.getElementById("pick-date").value;
    if (!date)        { setStatus("Укажите желаемую дату", "error"); return false; }
    if (!selectedTime){ setStatus("Выберите время", "error"); return false; }
    selectedDate = date;
  }
  if (step === 3) {
    const name  = document.getElementById("w-name").value.trim();
    const phone = document.getElementById("w-phone").value.trim();
    const email = document.getElementById("w-email").value.trim();
    if (!name || !phone || !email) {
      setStatus("Заполните все поля", "error");
      return false;
    }
  }
  return true;
}

/* ── Submit ── */
async function submitBooking() {
  const name  = document.getElementById("w-name").value.trim();
  const phone = document.getElementById("w-phone").value.trim();
  const email = document.getElementById("w-email").value.trim();

  btnNext.disabled    = true;
  btnNext.textContent = "Отправляем…";

  try {
    const res = await fetch("/api/v1/commerce/leads", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        car_id:    selectedCar?.id || null,
        full_name: name,
        email,
        phone,
        lead_type: "test_drive",
        note:      null,
        payload: {
          preferred_date: selectedDate,
          preferred_time: selectedTime,
          car_name:       selectedCar?.name || "",
          source:         "contacts_booking_wizard",
          page:           window.location.pathname,
          submitted_at:   new Date().toISOString(),
        },
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const dateFormatted = selectedDate
      ? new Date(selectedDate + "T12:00:00").toLocaleDateString("ru-RU", {
          day: "numeric", month: "long", year: "numeric",
        })
      : "—";

    document.getElementById("done-summary").textContent =
      `${selectedCar?.name} · ${dateFormatted} · ${selectedTime}`;
    document.getElementById("done-ref").textContent = `Заявка №${data.id}`;

    showStep(0);

  } catch {
    setStatus("Ошибка отправки. Попробуйте ещё раз.", "error");
    btnNext.disabled    = false;
    btnNext.textContent = "Записаться";
  }
}

/* ── Navigation ── */
btnNext.addEventListener("click", async () => {
  if (!validateStep(currentStep)) return;
  if (currentStep === 3) { await submitBooking(); return; }
  const nextStep = currentStep + 1;
  showStep(nextStep);
  if (nextStep === 2) buildSlots();
});

btnBack.addEventListener("click", () => {
  const prevStep = currentStep - 1;
  if (prevStep >= 1) {
    showStep(prevStep);
    if (prevStep === 2) buildSlots();
  }
});

/* ── Init ── */
loadCars();
showStep(1);
