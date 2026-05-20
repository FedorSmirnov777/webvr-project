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
  const fullName = `${brandName} ${car.model_name}`.trim();
  document.getElementById("bc-name").textContent = fullName;
  document.title = `${fullName} ${car.year} | VR Garage`;

  /* Header */
  document.getElementById("car-brand-label").textContent = brandName.toUpperCase();
  document.getElementById("car-name").textContent = `${car.model_name} ${car.year || ""}`.trim();

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

  /* Gallery images — hero image first, then extra_images from API */
  const isCamry = (car.model_name || "").toLowerCase().includes("camry");
  const CAMRY_HERO = "/assets/uploads/images/toyota_camry_hero.jpg";
  const CAMRY_PHOTO2 = "/assets/uploads/images/toyota_camry_2.webp";

  let images = [];
  if (isCamry) {
    // For Camry: always use our two photos, ignore whatever DB says
    images = [CAMRY_HERO, CAMRY_PHOTO2];
  } else {
    const heroUrl = car.config?.hero_image_url || car.hero_image_url || "";
    if (heroUrl) images.push(heroUrl);
    (car.extra_images || []).forEach((url) => {
      if (url && url !== heroUrl) images.push(url);
    });
  }
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
  } catch (err) {
    const msg = err.message.includes("404")
      ? "Автомобиль не найден или снят с публикации."
      : `Не удалось загрузить данные: ${err.message}`;
    showError(msg);
  }
}

init();
