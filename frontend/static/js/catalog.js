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
const vrMenuEl = document.getElementById("vr-menu");
const vrBtnResetEl = document.getElementById("vr-btn-reset");
const vrBtnSpinEl = document.getElementById("vr-btn-spin");
const vrBtnExitEl = document.getElementById("vr-btn-exit");

let cars = [];
let brandsById = new Map();
let activeCar = null;
let activeModelEl = null;
let spinning = false;
let yaw = 0;

const isQuestBrowser = /OculusBrowser|Quest/i.test(navigator.userAgent || "");
const query = new URLSearchParams(window.location.search);
const forceHeadsetMode = query.get("vrhmd") === "1";
const HEADSET_VR_MODE = isQuestBrowser || forceHeadsetMode;

let lightVrMode = false;
const vrTextureFallbacks = [
  { selector: "a-plane[width='20'][height='22'][rotation='-90 0 0']", color: "#1e293b" },
  { selector: "a-plane[width='20'][height='22'][rotation='90 0 0']", color: "#334155" },
  { selector: "a-plane[position='-6.875 4 -11']", color: "#3f4c5f" },
  { selector: "a-plane[position='6.875 4 -11']", color: "#3f4c5f" },
  { selector: "a-plane[position='0 6.6 -11']", color: "#475569" },
  { selector: "a-plane[position='-10 4 0']", color: "#1f2937" },
  { selector: "a-plane[position='10 4 0']", color: "#1f2937" }
];

function setLightVrMode(enabled) {
  lightVrMode = Boolean(enabled);
  const source = document.getElementById("garage-props-source");
  if (source) {
    if (lightVrMode) {
      source.removeAttribute("fbx-model");
      source.setAttribute("visible", "false");
    }
  }

  vrTextureFallbacks.forEach(({ selector, color }) => {
    const el = document.querySelector(selector);
    if (!el || !lightVrMode) return;
    el.removeAttribute("src");
    el.setAttribute("color", color);
    el.setAttribute("material", "roughness: 0.9; metalness: 0.05");
  });
}


function setStatus(message) {
  statusLineEl.textContent = message;
}

function resolveBrandName(car) {
  const fromMap = brandsById.get(car.brand_id);
  if (fromMap && String(fromMap).trim()) return String(fromMap).trim();
  return "Марка";
}

function carDisplayName(car) {
  return `${resolveBrandName(car)} ${car.model_name || ""}`.trim();
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

function createModelEntity(car) {
  if (HEADSET_VR_MODE) {
    const headsetCar = {
      ...car,
      config: {
        ...(car.config || {}),
        model_url: "/assets/models/toyota_camry/scene.gltf"
      }
    };
    const model = document.createElement("a-entity");
    model.setAttribute("gltf-model", headsetCar.config.model_url);
    model.setAttribute("position", "0 0 0");
    model.setAttribute("rotation", "0 180 0");
    model.setAttribute("scale", "0.9 0.9 0.9");

    let loaded = false;
    model.addEventListener("model-loaded", () => {
      loaded = true;
      fitModelToParkingSlot(model, { lift: 0.06 });
    });

    model.addEventListener("model-error", () => {
      clearModel();
      activeModelEl = createFallbackModel(car);
      carAnchor.appendChild(activeModelEl);
      setStatus("Легкая 3D-модель не загрузилась. Показан запасной вариант.");
    });

    setTimeout(() => {
      if (loaded) return;
      clearModel();
      activeModelEl = createFallbackModel(car);
      carAnchor.appendChild(activeModelEl);
      setStatus("3D-модель не загрузилась вовремя. Показан запасной вариант.");
    }, 15000);

    return model;
  }

  const localConfig = car.config || {};
  const modelType = localConfig?.model_type || "gltf";
  const modelUrl = (localConfig?.model_url || "").trim();
  const objUrl = (localConfig?.obj_url || "").trim();
  const mtlUrl = (localConfig?.mtl_url || "").trim();

  if (modelType === "obj") {
    if (!objUrl) {
      return createFallbackModel(car);
    }

    const model = document.createElement("a-entity");
    model.setAttribute("obj-model", `obj: url(${objUrl}); mtl: url(${mtlUrl})`);
    model.setAttribute("position", localConfig?.position || "0 0 0");
    model.setAttribute("rotation", localConfig?.rotation || "0 180 0");
    model.setAttribute("scale", localConfig?.scale || "1 1 1");

    model.addEventListener("model-loaded", () => {
      fitModelToParkingSlot(model, localConfig);
    });

    model.addEventListener("model-error", () => {
      clearModel();
      activeModelEl = createFallbackModel(car);
      carAnchor.appendChild(activeModelEl);
      setStatus("Не удалось загрузить OBJ-модель. Показан запасной вариант.");
    });

    return model;
  }

  if (!modelUrl) {
    return createFallbackModel(car);
  }

  const model = document.createElement("a-entity");
  model.setAttribute("gltf-model", modelUrl);
  model.setAttribute("position", localConfig?.position || "0 0 0");
  model.setAttribute("rotation", localConfig?.rotation || "0 180 0");
  model.setAttribute("scale", localConfig?.scale || "1 1 1");

  let loaded = false;
  model.addEventListener("model-loaded", () => {
    loaded = true;
    fitModelToParkingSlot(model, localConfig);
  });

  model.addEventListener("model-error", () => {
    clearModel();
    activeModelEl = createFallbackModel(car);
    carAnchor.appendChild(activeModelEl);
    setStatus("Не удалось загрузить 3D-модель. Показан запасной вариант.");
  });

  setTimeout(() => {
    if (loaded) return;
    clearModel();
    activeModelEl = createFallbackModel(car);
    carAnchor.appendChild(activeModelEl);
    setStatus("3D-модель не загрузилась вовремя. Показан запасной вариант.");
  }, HEADSET_VR_MODE ? 22000 : 15000);

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

function renderCatalog() {
  const search = searchInputEl.value.trim().toLowerCase();
  const filtered = cars.filter((car) => {
    if (!search) return true;
    const brandName = resolveBrandName(car);
    const text = `${brandName} ${car.model_name || ""}`.toLowerCase();
    return text.includes(search);
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
    const imageSrc =
      car.config?.hero_image_url ||
      car.hero_image_url ||
      "/assets/uploads/images/car_1_demo.jpg";
    card.innerHTML = `
      <div class="car-media">
        <img class="car-thumb" src="${imageSrc}" alt="${brandName} ${car.model_name}" />
        <span class="car-open-pill">3D-осмотр</span>
      </div>
      <div class="car-meta">
        <strong>${brandName} ${car.model_name}</strong>
        <span>${cardLabel(car)}</span>
        <span class="car-open-hint">Нажми, чтобы открыть режим обзора</span>
      </div>
    `;

    card.addEventListener("click", () => selectCar(car.id));
    listEl.appendChild(card);
  });

  setStatus(`Найдено автомобилей: ${filtered.length}`);
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
  const name = `${brandName} ${activeCar.model_name}`;
  titleEl.textContent = name;
  descEl.textContent = activeCar.description || "Описание появится позже.";

  clearModel();
  activeModelEl = createModelEntity(activeCar);
  carAnchor.appendChild(activeModelEl);
  playEntryAnimation();

  viewerSectionEl.hidden = false;
  viewerSectionEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

function playEntryAnimation() {
  const idleY = 0.04;
  const startZ = -10.8; // start near the gate so drive-in is clearly visible
  const stopZ = 0;

  carAnchor.removeAttribute("animation__drivein");
  carAnchor.setAttribute("position", `0 ${idleY} ${startZ}`);

  const startDrive = () => {
    carAnchor.removeAttribute("animation__drivein");
    carAnchor.setAttribute(
      "animation__drivein",
      `property: position; to: 0 ${idleY} ${stopZ}; dur: 2600; easing: easeInOutQuad`
    );
  };

  if (!garageDoorEl) {
    startDrive();
    return;
  }

  garageDoorEl.removeAttribute("animation__open");
  garageDoorEl.removeAttribute("animation__close");
  garageDoorEl.setAttribute("position", "0 3.6 -10.95");
  garageDoorEl.setAttribute(
    "animation__open",
    "property: position; to: 0 6.7 -10.95; dur: 800; easing: easeOutQuad"
  );

  setTimeout(startDrive, 420);

  setTimeout(() => {
    garageDoorEl.removeAttribute("animation__close");
    garageDoorEl.setAttribute(
      "animation__close",
      "property: position; to: 0 3.6 -10.95; dur: 800; easing: easeInQuad"
    );
  }, 4200);
}

function setupSpinControl() {
  toggleSpinBtn.addEventListener("click", () => {
    spinning = !spinning;
    toggleSpinBtn.textContent = spinning ? "Остановить вращение" : "Включить вращение";
  });

  const sceneEl = document.getElementById("scene");
  sceneEl.addEventListener("renderstart", () => {
    const loop = () => {
      if (spinning) {
        yaw += 0.22;
        turntable.setAttribute("rotation", `0 ${yaw} 0`);
      }
      requestAnimationFrame(loop);
    };
    loop();
  });
}

function setupResetView() {
  resetViewBtn.addEventListener("click", () => {
    spinning = false;
    toggleSpinBtn.textContent = "Включить вращение";
    yaw = 0;
    turntable.setAttribute("rotation", "0 0 0");
    const cameraRig = document.getElementById("camera-rig");
    cameraRig.setAttribute("position", "0 1.65 3.4");
    cameraRig.setAttribute("rotation", "0 0 0");
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
      setStatus("Включен режим VR-шлема: легкая модель + яркая сцена.");
      setLightVrMode(true);

      // Hard fail-safe against black scene in mobile WebXR.
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



function setupVrMovementControls() {
  const cameraRig = document.getElementById("camera-rig");
  const leftHand = document.getElementById("left-hand");
  const rightHand = document.getElementById("right-hand");
  if (!cameraRig) return;

  let lastSnapAt = 0;
  const snapCooldownMs = 220;
  const snapThreshold = 0.65;
  const snapStep = 35;

  const applySnapTurn = (xAxis) => {
    const now = Date.now();
    if (now - lastSnapAt < snapCooldownMs) return;

    const direction = xAxis > 0 ? -1 : 1;
    const rotation = cameraRig.getAttribute("rotation") || { x: 0, y: 0, z: 0 };
    const nextYaw = Number(rotation.y || 0) + direction * snapStep;
    cameraRig.setAttribute("rotation", `${Number(rotation.x || 0)} ${nextYaw} ${Number(rotation.z || 0)}`);
    lastSnapAt = now;
  };

  const onThumbstick = (event) => {
    const detail = event.detail || {};
    const x = Number(detail.x || 0);
    if (Math.abs(x) < snapThreshold) return;
    applySnapTurn(x);
  };

  [leftHand, rightHand].forEach((hand) => {
    if (!hand) return;
    hand.addEventListener("thumbstickmoved", onThumbstick);
    hand.addEventListener("axismove", onThumbstick);
  });
}

function setupGarageImportedProps() {
  const source = document.getElementById("garage-props-source");
  if (!source || !window.AFRAME?.THREE) return;

  const keepPattern = /(Rack|rack|Shelf|shelf|Tire_24|Tire|tire|ToolchestExported|ToolChest|Box_38)/;
  const { Box3, Matrix4, Vector3 } = window.AFRAME.THREE;

  source.addEventListener("model-error", () => {
    source.removeAttribute("fbx-model");
    source.setAttribute("visible", "false");
    setStatus("Часть декора гаража не загрузилась, VR запущен в легком режиме.");
  });

  setTimeout(() => {
    if (source.getObject3D("mesh")) return;
    source.removeAttribute("fbx-model");
    source.setAttribute("visible", "false");
  }, 4500);

  source.addEventListener("model-loaded", () => {
    const root = source.getObject3D("mesh");
    if (!root) return;

    root.traverse((obj) => {
      if (!obj.isMesh) return;
      const name = String(obj.name || "");
      obj.visible = keepPattern.test(name);
    });

    const localBounds = new Box3();
    const tempBox = new Box3();
    const rel = new Matrix4();
    const invRootWorld = new Matrix4();
    let hasGeom = false;

    root.updateWorldMatrix(true, true);
    invRootWorld.copy(root.matrixWorld).invert();

    root.traverse((obj) => {
      if (!obj.isMesh || !obj.visible || !obj.geometry) return;
      if (!obj.geometry.boundingBox) obj.geometry.computeBoundingBox();
      if (!obj.geometry.boundingBox) return;

      rel.multiplyMatrices(invRootWorld, obj.matrixWorld);
      tempBox.copy(obj.geometry.boundingBox).applyMatrix4(rel);
      if (!hasGeom) {
        localBounds.copy(tempBox);
        hasGeom = true;
      } else {
        localBounds.union(tempBox);
      }
    });

    if (!hasGeom) return;

    const size = new Vector3();
    const center = new Vector3();
    localBounds.getSize(size);
    localBounds.getCenter(center);

    const targetWidth = 7.8;
    const targetDepth = 1.35;
    const targetHeight = 2.4;

    const fitX = size.x > 0 ? targetWidth / size.x : 1;
    const fitZ = size.z > 0 ? targetDepth / size.z : 1;
    const fitY = size.y > 0 ? targetHeight / size.y : 1;
    const fitScale = Math.min(fitX, fitY, fitZ) * 0.92;

    root.scale.setScalar(fitScale);
    root.position.x -= center.x;
    root.position.z -= center.z;
    root.position.y -= localBounds.min.y;

    source.setAttribute("position", "0 0.02 -8.55");
    source.setAttribute("rotation", "0 180 0");
  });
}


function setupVrMenu() {
  const sceneEl = document.getElementById("scene");
  const cameraRig = document.getElementById("camera-rig");
  if (!sceneEl || !cameraRig || !vrMenuEl) return;

  const resetView = () => {
    spinning = false;
    if (toggleSpinBtn) toggleSpinBtn.textContent = "Включить вращение";
    yaw = 0;
    turntable.setAttribute("rotation", "0 0 0");
    cameraRig.setAttribute("position", "0 1.65 3.4");
    cameraRig.setAttribute("rotation", "0 0 0");
  };

  if (vrBtnResetEl) {
    vrBtnResetEl.addEventListener("click", () => {
      resetView();
      setStatus("Вид сброшен.");
    });
  }

  if (vrBtnSpinEl) {
    vrBtnSpinEl.addEventListener("click", () => {
      spinning = !spinning;
      if (toggleSpinBtn) toggleSpinBtn.textContent = spinning ? "Остановить вращение" : "Включить вращение";
      setStatus(spinning ? "Вращение включено." : "Вращение выключено.");
    });
  }

  if (vrBtnExitEl) {
    vrBtnExitEl.addEventListener("click", () => {
      if (typeof sceneEl.exitVR === "function") {
        sceneEl.exitVR();
      }
    });
  }

  sceneEl.addEventListener("enter-vr", () => {
    vrMenuEl.setAttribute("visible", "true");
  });

  sceneEl.addEventListener("exit-vr", () => {
    vrMenuEl.setAttribute("visible", "false");
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
    setupSpinControl();
    setupResetView();
    setupNavigationControls();
    setupGarageImportedProps();
    setupVrControl();
  } catch (error) {
    listEl.innerHTML = "";
    setStatus(`Не удалось загрузить каталог: ${error.message}`);
  }
}

init();
