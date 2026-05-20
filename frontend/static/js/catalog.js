const searchInputEl = document.getElementById("search-input");
const listEl = document.getElementById("car-list");
const statusLineEl = document.getElementById("status-line");
const viewerSectionEl = document.getElementById("viewer-section");
const titleEl = document.getElementById("car-title");
const descEl = document.getElementById("car-description");
const toggleSpinBtn = document.getElementById("toggle-spin");
const resetViewBtn = document.getElementById("reset-view");
const enterVrBtn = document.getElementById("enter-vr");
const carAnchor = document.getElementById("car-anchor");
const turntable = document.getElementById("turntable");
const garageDoorEl = document.getElementById("garage-door");

let cars = [];
let brandsById = new Map();
let activeCar = null;
let activeModelEl = null;
let spinning = false;
let yaw = 0;
let filterBrandId = "";
let filterBodyType = "";

const isQuestBrowser = /OculusBrowser|Quest/i.test(navigator.userAgent || "");
const query = new URLSearchParams(window.location.search);
const forceHeadsetMode = query.get("vrhmd") === "1";
const HEADSET_VR_MODE = isQuestBrowser || forceHeadsetMode;

function setStatus(message) {
  statusLineEl.textContent = message;
}

function resolveBrandName(car) {
  const fromMap = brandsById.get(car.brand_id);
  if (fromMap && String(fromMap).trim()) return String(fromMap).trim();
  return "Марка";
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

function createFallbackModel(car) {
  const wrapper = document.createElement("a-entity");
  const color = car.config?.fallback_color || "#2563eb";
  const scale = car.config?.fallback_scale || "1.6 0.75 3.2";

  const body = document.createElement("a-box");
  body.setAttribute("scale", scale);
  body.setAttribute("position", "0 0.5 0");
  body.setAttribute("color", color);
  body.setAttribute("material", "metalness: 0.2; roughness: 0.35");

  const cabin = document.createElement("a-box");
  cabin.setAttribute("scale", "1.2 0.5 1.3");
  cabin.setAttribute("position", "0 1 0");
  cabin.setAttribute("color", "#e5e7eb");
  cabin.setAttribute("material", "opacity: 0.85; transparent: true");

  const wheels = [
    [-0.7, 0.2, 1.05],
    [0.7, 0.2, 1.05],
    [-0.7, 0.2, -1.05],
    [0.7, 0.2, -1.05]
  ].map(([x, y, z]) => {
    const wheel = document.createElement("a-cylinder");
    wheel.setAttribute("radius", "0.24");
    wheel.setAttribute("height", "0.2");
    wheel.setAttribute("rotation", "90 0 0");
    wheel.setAttribute("position", `${x} ${y} ${z}`);
    wheel.setAttribute("color", "#111111");
    return wheel;
  });

  [body, cabin, ...wheels].forEach((part) => wrapper.appendChild(part));
  return wrapper;
}

function fitModelToParkingSlot(model, localConfig = {}) {
  const mesh = model.getObject3D("mesh");
  if (!mesh || !window.AFRAME?.THREE) return false;

  mesh.traverse((obj) => {
    if (!obj.isMesh || !obj.material) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    mats.forEach((mat) => {
      if (!mat) return;
      if ("transmission" in mat) mat.transmission = 0;
      if ("opacity" in mat) mat.opacity = 1;
      mat.transparent = false;
      mat.depthWrite = true;
      mat.needsUpdate = true;
    });
  });

  const { Box3, Vector3, Matrix4 } = window.AFRAME.THREE;

  const getLocalBounds = () => {
    const localBounds = new Box3();
    const tempBox = new Box3();
    const rel = new Matrix4();
    const invMeshWorld = new Matrix4();
    let hasGeom = false;

    mesh.updateWorldMatrix(true, true);
    invMeshWorld.copy(mesh.matrixWorld).invert();

    mesh.traverse((obj) => {
      if (!obj.isMesh || !obj.geometry) return;
      if (!obj.geometry.boundingBox) obj.geometry.computeBoundingBox();
      if (!obj.geometry.boundingBox) return;

      rel.multiplyMatrices(invMeshWorld, obj.matrixWorld);
      tempBox.copy(obj.geometry.boundingBox).applyMatrix4(rel);
      if (!hasGeom) {
        localBounds.copy(tempBox);
        hasGeom = true;
      } else {
        localBounds.union(tempBox);
      }
    });

    return hasGeom ? localBounds : null;
  };

  let bounds = getLocalBounds();
  if (!bounds) return false;

  const size = new Vector3();
  bounds.getSize(size);

  const slotWidth = Number(localConfig?.slotWidth || 2.35);
  const slotLength = Number(localConfig?.slotLength || 4.95);
  const slotHeight = Number(localConfig?.slotHeight || 1.95);

  const fitByWidth = size.x > 0 ? slotWidth / size.x : 1;
  const fitByLength = size.z > 0 ? slotLength / size.z : 1;
  const fitByHeight = size.y > 0 ? slotHeight / size.y : 1;
  const fitScale = Math.min(fitByWidth, fitByLength, fitByHeight);

  if (Number.isFinite(fitScale) && fitScale > 0) {
    mesh.scale.multiplyScalar(fitScale);
    bounds = getLocalBounds() || bounds;
  }

  const center = new Vector3();
  bounds.getCenter(center);
  mesh.position.x -= center.x;
  mesh.position.z -= center.z;
  mesh.position.y -= bounds.min.y;

  const lift = Number(localConfig?.lift || 0.02);
  if (lift) mesh.position.y += lift;

  return true;
}

const MODEL_PATHS = {
  toyota:   "/assets/models/2023_toyota_avalon_hybrid_limited.glb",
  bmw_m3:   "/assets/models/2015_bmw_m3_f80.glb",
  mercedes: "/assets/models/mercedese190evo.glb",
  porsche:  "/assets/models/1989_porsche_911_964_carrera_4.glb",
};

function resolveModelPath(car) {
  const name = (car.model_name || "").toLowerCase();
  if (name.includes("avalon") || name.includes("camry")) return MODEL_PATHS.toyota;
  if (name.includes("m3"))                               return MODEL_PATHS.bmw_m3;
  if (name.includes("190"))                              return MODEL_PATHS.mercedes;
  if (name.includes("964") || name.includes("911"))     return MODEL_PATHS.porsche;
  return null;
}

function createModelEntity(car) {
  const glbPath = resolveModelPath(car);
  if (!glbPath) return createFallbackModel(car);

  const model = document.createElement("a-entity");
  model.setAttribute("gltf-model", glbPath);
  model.setAttribute("position", "0 0 0");
  model.setAttribute("rotation", "0 0 0");

  let loaded = false;
  model.addEventListener("model-loaded", () => {
    loaded = true;
    fitModelToParkingSlot(model, { lift: 0.04 });
  });
  model.addEventListener("model-error", () => {
    clearModel();
    activeModelEl = createFallbackModel(car);
    carAnchor.appendChild(activeModelEl);
  });
  setTimeout(() => {
    if (!loaded) {
      clearModel();
      activeModelEl = createFallbackModel(car);
      carAnchor.appendChild(activeModelEl);
    }
  }, 20000);

  return model;
}

function clearModel() {
  if (!activeModelEl) return;
  activeModelEl.remove();
  activeModelEl = null;
}

function cardLabel(car) {
  const price = car.base_price ? `${Number(car.base_price).toLocaleString("ru-RU")} $` : "Цена по запросу";
  return `${car.body_type} • ${price}`;
}

function cardSpecsHtml(car) {
  const parts = [];
  if (car.year) parts.push(`<span class="car-spec-tag">${car.year}</span>`);
  if (car.specs?.engine) parts.push(`<span class="car-spec-tag">${car.specs.engine}</span>`);
  if (car.specs?.mileage != null) {
    const mileageVal = car.specs.mileage === 0 || car.specs.mileage === "new"
      ? "Новый"
      : `${Number(car.specs.mileage).toLocaleString("ru-RU")} км`;
    parts.push(`<span class="car-spec-tag">${mileageVal}</span>`);
  }
  return parts.length ? `<div class="car-specs-row">${parts.join("")}</div>` : "";
}

function renderCatalog() {
  const search = searchInputEl.value.trim().toLowerCase();
  const filtered = cars.filter((car) => {
    if (search) {
      const brandName = resolveBrandName(car);
      const text = `${brandName} ${car.model_name || ""}`.toLowerCase();
      if (!text.includes(search)) return false;
    }
    if (filterBrandId && String(car.brand_id) !== String(filterBrandId)) return false;
    if (filterBodyType && car.body_type !== filterBodyType) return false;
    return true;
  });

  listEl.innerHTML = "";

  if (!filtered.length) {
    setStatus("По запросу ничего не найдено.");
    return;
  }

  filtered.forEach((car) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "car-item";
    card.dataset.id = String(car.id);

    const brandName = resolveBrandName(car);
    const isToyota = (car.model_name || "").toLowerCase().includes("camry") ||
                     (car.model_name || "").toLowerCase().includes("avalon");
    const displayModelName = isToyota ? "Avalon 2023" : car.model_name;
    const TOYOTA_HERO = "/assets/uploads/images/tayota_avalon/toyota_avalon_hero.jpg";
    const imageSrc =
      car.config?.hero_image_url ||
      car.hero_image_url ||
      (isToyota ? TOYOTA_HERO : "/assets/uploads/images/car_1_demo.jpg");
    const onerrorAttr = isToyota
      ? `onerror="this.onerror=null;this.src='${TOYOTA_HERO}'"` : "";
    card.innerHTML = `
      <div class="car-media">
        <img class="car-thumb" src="${imageSrc}" alt="${brandName} ${displayModelName}" ${onerrorAttr} />
        <span class="car-open-pill">Подробнее →</span>
      </div>
      <div class="car-meta">
        <strong>${brandName} ${displayModelName}</strong>
        ${cardSpecsHtml(car)}
        <span>${cardLabel(car)}</span>
        <span class="car-open-hint">Нажми, чтобы открыть карточку автомобиля</span>
      </div>
    `;

    card.addEventListener("click", () => { window.location.href = `/car?id=${car.id}`; });
    listEl.appendChild(card);
  });

  setStatus(`Найдено автомобилей: ${filtered.length}`);
  setupCardReveal();
}

async function selectCar(carId) {
  const selected = cars.find((item) => String(item.id) === String(carId));
  if (!selected) return;

  let fullCar = selected;
  const isNumericId = /^\d+$/.test(String(carId));
  if (isNumericId) {
    try {
      fullCar = await fetchJson(`/api/v1/cars/${carId}`);
    } catch {
      // Use summary payload if detail endpoint fails.
    }
  }

  activeCar = { ...selected, ...fullCar };

  document.querySelectorAll(".car-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.id === String(carId));
  });

  const brandName = resolveBrandName(activeCar);
  const isActiveToyota = (activeCar.model_name || "").toLowerCase().includes("camry") ||
                         (activeCar.model_name || "").toLowerCase().includes("avalon");
  const displayActiveName = isActiveToyota ? "Avalon 2023" : activeCar.model_name;
  const name = `${brandName} ${displayActiveName}`;
  titleEl.textContent = name;
  const activeDesc = isActiveToyota
    ? "Toyota Avalon Hybrid 2023 — флагманский полноразмерный седан с гибридной установкой. Сочетает премиальный комфорт, тихий салон и экономичность гибрида."
    : (activeCar.description || "Описание появится позже.");
  descEl.textContent = activeDesc;

  clearModel();
  activeModelEl = createModelEntity(activeCar);
  carAnchor.appendChild(activeModelEl);
  playEntryAnimation();

  viewerSectionEl.hidden = false;
  viewerSectionEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

function playEntryAnimation() {
  const idleY  = 0.04;
  const startZ = -10.8;  // behind the garage door
  const stopZ  = 0;
  const driveDur = 2600;
  const doorDelay = 420;

  // Position car at starting point facing the door (front = -Z = front-first entry)
  carAnchor.removeAttribute("animation__drivein");
  carAnchor.setAttribute("position", `0 ${idleY} ${startZ}`);

  // Reset any previous rotation on the model itself
  if (activeModelEl) {
    activeModelEl.removeAttribute("animation__face");
    activeModelEl.setAttribute("rotation", "0 0 0");
  }

  const startDrive = () => {
    carAnchor.removeAttribute("animation__drivein");
    carAnchor.setAttribute(
      "animation__drivein",
      `property: position; to: 0 ${idleY} ${stopZ}; dur: ${driveDur}; easing: easeInOutQuad`
    );

    // After the car stops, pivot it to face the viewer (180° turn)
    const pivotDelay = driveDur + 200;
    setTimeout(() => {
      if (!activeModelEl) return;
      activeModelEl.setAttribute(
        "animation__face",
        "property: rotation; to: 0 180 0; dur: 700; easing: easeInOutCubic"
      );
    }, pivotDelay);
  };

  if (!garageDoorEl) {
    startDrive();
    return;
  }

  // Open door
  garageDoorEl.removeAttribute("animation__open");
  garageDoorEl.removeAttribute("animation__close");
  garageDoorEl.setAttribute("position", "0 3.6 -10.95");
  garageDoorEl.setAttribute(
    "animation__open",
    "property: position; to: 0 6.7 -10.95; dur: 800; easing: easeOutQuad"
  );

  setTimeout(startDrive, doorDelay);

  // Close door after car is fully inside
  setTimeout(() => {
    garageDoorEl.removeAttribute("animation__close");
    garageDoorEl.setAttribute(
      "animation__close",
      "property: position; to: 0 3.6 -10.95; dur: 800; easing: easeInQuad"
    );
  }, doorDelay + driveDur + 900);
}

// ── Garage boundary clamp ────────────────────────────────────────────────────
// Keep the camera inside the garage volume so users can't escape into void
const GARAGE_BOUNDS = { xMin: -8.8, xMax: 8.8, yMin: 0.7, yMax: 6.8, zMin: -10.2, zMax: 9.5 };

function clampCamera() {
  const rig = document.getElementById("camera-rig");
  if (!rig) return;
  const p = rig.getAttribute("position");
  const x = Math.max(GARAGE_BOUNDS.xMin, Math.min(GARAGE_BOUNDS.xMax, Number(p.x)));
  const y = Math.max(GARAGE_BOUNDS.yMin, Math.min(GARAGE_BOUNDS.yMax, Number(p.y)));
  const z = Math.max(GARAGE_BOUNDS.zMin, Math.min(GARAGE_BOUNDS.zMax, Number(p.z)));
  if (x !== p.x || y !== p.y || z !== p.z) {
    rig.setAttribute("position", `${x} ${y} ${z}`);
  }
}

function startRenderLoop() {
  const sceneEl = document.getElementById("scene");
  if (!sceneEl) return;
  sceneEl.addEventListener("renderstart", () => {
    const loop = () => {
      if (spinning) {
        yaw += 0.22;
        turntable.setAttribute("rotation", `0 ${yaw} 0`);
      }
      clampCamera();
      requestAnimationFrame(loop);
    };
    loop();
  });
}

async function enterVrOrFullscreen(sceneEl) {
  if (window.AFRAME && typeof sceneEl.enterVR === "function") {
    try {
      await sceneEl.enterVR();
      return true;
    } catch {
      // Fall through to fullscreen fallback.
    }
  }

  const target = sceneEl.canvas || sceneEl;
  const requestFs = target.requestFullscreen || target.webkitRequestFullscreen;
  if (typeof requestFs === "function") {
    await requestFs.call(target);
    return true;
  }

  return false;
}

function setupVrControl() {
  const sceneEl = document.getElementById("scene");
  if (!enterVrBtn || !sceneEl) return;

  enterVrBtn.addEventListener("click", async () => {
    if (HEADSET_VR_MODE) {
      setStatus("Включен режим VR-шлема.");
      // Brighten sky for mobile WebXR
      sceneEl.setAttribute("fog", "type: linear; near: 999; far: 1000; color: #6aa9ff");
      const sky = sceneEl.querySelector("a-sky");
      if (sky) sky.setAttribute("color", "#60a5fa");

      const cameraRig = document.getElementById("camera-rig");
      if (cameraRig) {
        cameraRig.setAttribute("position", "0 1.65 3.4");
        cameraRig.setAttribute("rotation", "0 0 0");
      }
    }

    const ok = await enterVrOrFullscreen(sceneEl);
    if (!ok) {
      enterVrBtn.textContent = "VR недоступен";
      enterVrBtn.disabled = true;
      setStatus("VR режим недоступен в этом браузере/устройстве.");
    }
  });
}

function setupNavigationControls() {
  const cameraEl = document.getElementById("main-camera");
  const cameraRig = document.getElementById("camera-rig");
  if (!cameraEl || !cameraRig) return;

  const normalAcceleration = 42;
  const sprintAcceleration = 130;
  const verticalStep = 0.28;
  const applyAcceleration = (value) => {
    cameraEl.setAttribute("wasd-controls", `enabled: true; acceleration: ${value}; fly: true`);
  };

  const moveVertical = (direction) => {
    const pos = cameraRig.getAttribute("position");
    const nextY = Math.min(8, Math.max(0.7, Number(pos.y || 1.65) + direction * verticalStep));
    cameraRig.setAttribute("position", `${pos.x} ${nextY} ${pos.z}`);
  };

  cameraEl.setAttribute("look-controls", "enabled: true; pointerLockEnabled: false; touchEnabled: true; mouseEnabled: true");
  applyAcceleration(normalAcceleration);

  window.addEventListener("keydown", (event) => {
    if (event.key === "Shift") {
      applyAcceleration(sprintAcceleration);
      return;
    }

    if (event.code === "Space" || event.key.toLowerCase() === "e") {
      moveVertical(1);
      event.preventDefault();
      return;
    }

    if (event.code === "ControlLeft" || event.code === "ControlRight" || event.key.toLowerCase() === "q") {
      moveVertical(-1);
      event.preventDefault();
    }
  });

  window.addEventListener("keyup", (event) => {
    if (event.key === "Shift") {
      applyAcceleration(normalAcceleration);
    }
  });
}



// setupVrMovementControls and setupGarageImportedProps removed — no VR controllers
// or FBX props are used in this build.

function setupFilters() {
  const brandSelect = document.getElementById("filter-brand");
  const bodyContainer = document.getElementById("filter-body");
  if (!brandSelect || !bodyContainer) return;

  // Populate brand dropdown
  const sortedBrands = [...brandsById.entries()].sort((a, b) => a[1].localeCompare(b[1]));
  sortedBrands.forEach(([id, name]) => {
    const opt = document.createElement("option");
    opt.value = String(id);
    opt.textContent = name;
    brandSelect.appendChild(opt);
  });

  // Populate body type chips
  const bodyTypes = [...new Set(cars.map((c) => c.body_type).filter(Boolean))].sort();
  bodyTypes.forEach((type) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "filter-chip";
    btn.dataset.body = type;
    btn.textContent = type;
    bodyContainer.appendChild(btn);
  });

  brandSelect.addEventListener("change", () => {
    filterBrandId = brandSelect.value;
    renderCatalog();
  });

  bodyContainer.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-chip");
    if (!btn) return;
    bodyContainer.querySelectorAll(".filter-chip").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    filterBodyType = btn.dataset.body;
    renderCatalog();
  });
}

function setupCardReveal() {
  const cards = listEl.querySelectorAll(".car-item");
  if (!cards.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08 }
  );

  cards.forEach((card, i) => {
    card.style.transitionDelay = `${Math.min(i * 55, 330)}ms`;
    observer.observe(card);
  });
}

function setupSearch() {
  searchInputEl.addEventListener("input", () => {
    renderCatalog();
  });
}


async function init() {
  try {
    const [brands, payload] = await Promise.all([
      fetchJson("/api/v1/brands"),
      fetchJson("/api/v1/cars?published_only=true")
    ]);
    brandsById = new Map((brands || []).map((brand) => [brand.id, brand.name]));
    cars = Array.isArray(payload) ? payload : [];

    if (!cars.length) {
      listEl.innerHTML = "";
      setStatus("Каталог пока пуст. Добавь автомобили в админке.");
      return;
    }

    renderCatalog();
    setupSearch();
    setupFilters();
    startRenderLoop();
    setupNavigationControls();
    setupVrControl();

    // Auto-open VR viewer if car_id is in URL (redirect from car detail page)
    const urlCarId = new URLSearchParams(window.location.search).get("car_id");
    if (urlCarId) {
      selectCar(Number(urlCarId));
    }
  } catch (error) {
    listEl.innerHTML = "";
    setStatus(`Не удалось загрузить каталог: ${error.message}`);
  }
}

init();
