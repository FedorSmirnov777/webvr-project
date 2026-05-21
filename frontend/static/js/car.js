const carId = new URLSearchParams(window.location.search).get("id");

const loadingEl  = document.getElementById("loading");
const errorEl    = document.getElementById("error");
const errorMsgEl = document.getElementById("error-msg");
const contentEl  = document.getElementById("car-content");

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function showError(msg) {
  loadingEl.hidden = true;
  errorMsgEl.textContent = msg;
  errorEl.hidden = false;
}

/* ── Spec label map ── */
const SPEC_LABELS = {
  engine:        "Двигатель",
  mileage:       "Пробег",
  power:         "Мощность",
  drivetrain:    "Привод",
  acceleration:  "Разгон 0–100",
  range:         "Запас хода",
  color:         "Цвет",
  transmission:  "КПП",
  fuel:          "Топливо",
  seats:         "Мест",
};

function formatMileage(val) {
  if (val === 0 || val === "new" || val === "новый") return "Новый";
  const num = Number(val);
  return Number.isFinite(num) ? `${num.toLocaleString("ru-RU")} км` : String(val);
}

/* ── Gallery ── */
let galleryImages = [];
let activeThumb = 0;

function buildGallery(images) {
  galleryImages = images;
  const mainImg = document.getElementById("gallery-img");
  const thumbsEl = document.getElementById("gallery-thumbs");

  if (!images.length) {
    mainImg.src = "/assets/uploads/images/car_1_demo.jpg";
    mainImg.alt = "Нет изображения";
    return;
  }

  mainImg.src = images[0];
  mainImg.alt = "";

  if (images.length > 1) {
    images.forEach((src, i) => {
      const thumb = document.createElement("button");
      thumb.className = "gallery-thumb" + (i === 0 ? " active" : "");
      thumb.type = "button";
      thumb.innerHTML = `<img src="${src}" alt="Фото ${i + 1}" loading="lazy" />`;
      thumb.addEventListener("click", () => switchImage(i));
      thumbsEl.appendChild(thumb);
    });
  }
}

function switchImage(index) {
  const mainImg = document.getElementById("gallery-img");
  const thumbsEl = document.getElementById("gallery-thumbs");

  mainImg.classList.add("loading");
  const tmp = new Image();
  tmp.onload = () => {
    mainImg.src = galleryImages[index];
    mainImg.classList.remove("loading");
  };
  tmp.src = galleryImages[index];

  thumbsEl.querySelectorAll(".gallery-thumb").forEach((t, i) => {
    t.classList.toggle("active", i === index);
  });

  activeThumb = index;
}

/* ── Render ── */
function renderCar(car, brandName) {
  /* Breadcrumb & title */
  const modelWithYear = `${car.model_name} ${car.year || ""}`.trim();
  const fullName = `${brandName} ${modelWithYear}`.trim();
  document.getElementById("bc-name").textContent = `${brandName} ${car.model_name}`.trim();
  document.title = `${fullName} | VR Garage`;

  /* Header */
  document.getElementById("car-brand-label").textContent = brandName.toUpperCase();
  document.getElementById("car-name").textContent = modelWithYear;

  /* Price */
  const priceEl = document.getElementById("car-price");
  if (car.base_price) {
    priceEl.textContent = `${Number(car.base_price).toLocaleString("ru-RU")} $`;
  } else {
    priceEl.textContent = "по запросу";
    priceEl.classList.add("muted");
  }

  /* Badge */
  const parts = [];
  if (car.year) parts.push(String(car.year));
  if (car.body_type) parts.push(car.body_type);
  document.getElementById("car-badge").textContent = parts.join(" · ");

  /* Gallery — hero from config, then extra_images */
  let images = [];
  const heroUrl = car.config?.hero_image_url || car.hero_image_url || "";
  if (heroUrl) images.push(heroUrl);
  (car.extra_images || []).forEach((url) => {
    if (url && url !== heroUrl) images.push(url);
  });
  buildGallery(images);

  /* Specs grid */
  const specsGrid = document.getElementById("specs-grid");
  const rows = [];

  /* Fixed rows always shown */
  if (car.year)      rows.push({ label: "Год выпуска",  value: car.year });
  if (car.body_type) rows.push({ label: "Тип кузова",   value: car.body_type });

  /* Dynamic specs from specs dict */
  Object.entries(car.specs || {}).forEach(([key, val]) => {
    const label = SPEC_LABELS[key] || key;
    let value = val;
    if (key === "mileage") value = formatMileage(val);
    rows.push({ label, value });
  });

  specsGrid.innerHTML = rows.map(({ label, value }) => `
    <div class="spec-item">
      <span class="spec-label">${label}</span>
      <span class="spec-value">${value ?? "—"}</span>
    </div>
  `).join("");

  /* Description */
  const descEl = document.getElementById("car-desc");
  if (car.description) {
    descEl.textContent = car.description;
  } else {
    descEl.hidden = true;
  }

  /* 3D viewer button */
  document.getElementById("btn-vr").addEventListener("click", () => {
    window.location.href = `/catalog?car_id=${car.id}`;
  });

  /* Trims */
  if (car.trims && car.trims.length > 0) {
    const trimsSection = document.getElementById("trims-section");
    const trimsGrid    = document.getElementById("trims-grid");

    trimsGrid.innerHTML = car.trims.map((trim) => {
      const featuresHtml = Object.entries(trim.features || {})
        .map(([k, v]) => `<p class="trim-feature">${SPEC_LABELS[k] || k}: ${v}</p>`)
        .join("");
      const priceStr = trim.trim_price
        ? `${Number(trim.trim_price).toLocaleString("ru-RU")} $`
        : "Цена по запросу";
      return `
        <div class="trim-card">
          <h3>${trim.trim_name}</h3>
          <p class="trim-price">${priceStr}</p>
          ${featuresHtml}
        </div>
      `;
    }).join("");

    trimsSection.hidden = false;
  }

  /* Show content */
  loadingEl.hidden = true;
  contentEl.hidden = false;
}

/* ── Init ── */
async function init() {
  if (!carId || !/^\d+$/.test(carId)) {
    showError("Автомобиль не указан или ID некорректен.");
    return;
  }

  try {
    const [car, brands] = await Promise.all([
      fetchJson(`/api/v1/cars/${carId}`),
      fetchJson("/api/v1/brands"),
    ]);

    const brand = (brands || []).find((b) => b.id === car.brand_id);
    const brandName = brand ? brand.name : "";

    renderCar(car, brandName);
    initRating(car.id);
  } catch (err) {
    const msg = err.message.includes("404")
      ? "Автомобиль не найден или снят с публикации."
      : `Не удалось загрузить данные: ${err.message}`;
    showError(msg);
  }
}

/* ── Star rating ── */
function pluralizeRatings(n) {
  if (n % 10 === 1 && n % 100 !== 11) return "оценка";
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return "оценки";
  return "оценок";
}

function fillStars(count) {
  document.querySelectorAll(".star-btn").forEach((s, i) => {
    s.classList.toggle("filled", i < count);
  });
}

async function initRating(id) {
  const starsRow  = document.getElementById("stars-row");
  const avgEl     = document.getElementById("rating-avg");
  const thanksEl  = document.getElementById("rating-thanks");
  if (!starsRow) return;

  const storageKey  = `vr_rating_${id}`;
  const alreadyVoted = localStorage.getItem(storageKey);

  // Load current average
  try {
    const res = await fetch(`/api/v1/commerce/ratings/${id}`);
    if (res.ok) {
      const data = await res.json();
      if (data.count > 0) {
        avgEl.textContent = `★ ${data.average} (${data.count} ${pluralizeRatings(data.count)})`;
      } else {
        avgEl.textContent = "Оценок пока нет";
      }
    }
  } catch { /* silent */ }

  if (alreadyVoted) {
    fillStars(parseInt(alreadyVoted));
    starsRow.classList.add("voted");
    thanksEl.hidden = false;
    return;
  }

  // Hover effect
  const stars = starsRow.querySelectorAll(".star-btn");
  stars.forEach((star, idx) => {
    star.addEventListener("mouseenter", () => {
      stars.forEach((s, j) => s.classList.toggle("hovered", j <= idx));
    });
    star.addEventListener("click", () => submitRating(id, idx + 1));
  });

  starsRow.addEventListener("mouseleave", () => {
    stars.forEach(s => s.classList.remove("hovered"));
  });
}

async function submitRating(id, score) {
  const starsRow = document.getElementById("stars-row");
  const avgEl    = document.getElementById("rating-avg");
  const thanksEl = document.getElementById("rating-thanks");

  starsRow.classList.add("voted");
  fillStars(score);
  localStorage.setItem(`vr_rating_${id}`, score);

  try {
    const res = await fetch(`/api/v1/commerce/ratings/${id}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ score }),
    });
    if (res.ok) {
      const data = await res.json();
      avgEl.textContent = `★ ${data.average} (${data.count} ${pluralizeRatings(data.count)})`;
    }
  } catch { /* silent — localStorage already saved */ }

  thanksEl.hidden = false;
}

init();
