import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

const query = new URLSearchParams(window.location.search);
const embedded = query.get("embed") === "1" || window.self !== window.top;
document.documentElement.classList.toggle("is-embedded", embedded);

const viewport = document.querySelector("#viewport");
const loading = document.querySelector("#loading");
const playButton = document.querySelector("#play");
const resetButton = document.querySelector("#reset");
const timelineInput = document.querySelector("#timeline");
const structureOpacityInput = document.querySelector("#structure-opacity");
const chamberOpacityInput = document.querySelector("#chamber-opacity");
const structureOpacityValue = document.querySelector("#structure-opacity-value");
const chamberOpacityValue = document.querySelector("#chamber-opacity-value");
const stageTitle = document.querySelector("#stage-title");
const stageNote = document.querySelector("#stage-note");
const displayControls = document.querySelector("#display-controls");

if (embedded) {
  displayControls?.removeAttribute("open");
}

window.__gizaDemoErrors = [];

function reportError(error) {
  const message = error?.message || String(error);
  window.__gizaDemoErrors.push(message);
  console.error(error);
  if (loading) {
    loading.hidden = false;
    loading.textContent = `Demo error: ${message}`;
  }
}

window.addEventListener("error", (event) => reportError(event.error || event.message));
window.addEventListener("unhandledrejection", (event) => reportError(event.reason));

const toggles = {
  core: document.querySelector("#toggle-core"),
  mound: document.querySelector("#toggle-mound"),
  ramps: document.querySelector("#toggle-ramps"),
  casing: document.querySelector("#toggle-casing"),
  chambers: document.querySelector("#toggle-chambers"),
};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf6f2e8);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
camera.up.set(0, 0, 1);
camera.position.set(175, -215, 140);

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
} catch (error) {
  reportError(error);
  throw error;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 48);
controls.enableDamping = true;
controls.minPolarAngle = Math.PI * 0.04;
controls.maxPolarAngle = Math.PI * 0.94;
controls.minDistance = 95;
controls.maxDistance = 560;

const defaultCameraOffset = camera.position.clone().sub(controls.target);
let cameraFitScale = 1;
let sceneFramed = false;

const sun = new THREE.DirectionalLight(0xffffff, 2.4);
sun.position.set(-90, -125, 210);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
scene.add(sun);
scene.add(new THREE.HemisphereLight(0xfff3d6, 0x6f7f91, 1.7));

const grid = new THREE.GridHelper(420, 42, 0xc9b99f, 0xe4dac9);
grid.rotation.x = Math.PI / 2;
grid.position.z = -0.02;
scene.add(grid);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(460, 460),
  new THREE.ShadowMaterial({ opacity: 0.14 }),
);
ground.receiveShadow = true;
ground.position.z = -0.04;
scene.add(ground);

const basePath = "../dist/";
const layerCount = 16;
const partDefs = [
  { key: "platform", path: "demo_parts/temporary_flat_capstone_platform.stl", color: 0xf1ddb6, opacity: 0.92, kind: "platform", renderOrder: 8 },
  { key: "capstone", path: "demo_parts/capstone.stl", color: 0xf5c75b, opacity: 1, kind: "capstone" },
  { key: "subchambers", path: "demo_parts/internal_chambers_subterranean_precut.stl", color: 0x244e56, opacity: 0.84, kind: "subchambers", depthWrite: false, renderOrder: 9 },
];

for (let i = 1; i <= layerCount; i += 1) {
  partDefs.push({
    key: `core-${String(i).padStart(2, "0")}`,
    path: `demo_layers/core/core_layer_${String(i).padStart(2, "0")}.stl`,
    color: 0xb7b0a3,
    opacity: 0.66,
    kind: "core",
    layer: i - 1,
  });
  partDefs.push({
    key: `fill-${String(i).padStart(2, "0")}`,
    path: `demo_layers/fill/fill_layer_${String(i).padStart(2, "0")}.stl`,
    color: 0xc58c45,
    opacity: 0.64,
    kind: "fill",
    layer: i - 1,
  });
  partDefs.push({
    key: `ramp-${String(i).padStart(2, "0")}`,
    path: `demo_layers/ramps/ramp_layer_${String(i).padStart(2, "0")}.stl`,
    color: 0xf3ead7,
    opacity: 0.96,
    kind: "ramp",
    layer: i - 1,
  });
  partDefs.push({
    key: `chamber-${String(i).padStart(2, "0")}`,
    path: `demo_layers/chambers/chamber_layer_${String(i).padStart(2, "0")}.stl`,
    color: 0x2e5962,
    opacity: 0.78,
    kind: "chambers",
    layer: i - 1,
    depthWrite: false,
    renderOrder: 9,
  });
  partDefs.push({
    key: `casing-${String(i).padStart(2, "0")}`,
    path: `demo_parts/casing_ring_top_${String(i).padStart(2, "0")}.stl`,
    color: 0xe8dfca,
    opacity: 0.98,
    kind: "casing",
    casingIndex: i - 1,
  });
}

const parts = new Map();
const skippedParts = [];
const reusePile = new THREE.Group();
let progress = 0;
let playing = true;
let lastTime = performance.now();

const opacityState = {
  structure: 1,
  chambers: 1,
};

window.__gizaDemo = { scene, camera, renderer, controls, parts, skippedParts, reusePile, progress, layerCount, opacityState };

function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

function rangePercent(input, fallback = 1) {
  if (!input) return fallback;
  return clamp(Number(input.value) / 100, 0, 1);
}

function syncOpacityControls() {
  opacityState.structure = rangePercent(structureOpacityInput, 1);
  opacityState.chambers = rangePercent(chamberOpacityInput, 1);
  if (structureOpacityValue) {
    structureOpacityValue.textContent = `${Math.round(opacityState.structure * 100)}%`;
  }
  if (chamberOpacityValue) {
    chamberOpacityValue.textContent = `${Math.round(opacityState.chambers * 100)}%`;
  }
}

function opacityForKind(kind, baseOpacity) {
  const setting = (kind === "chambers" || kind === "subchambers")
    ? opacityState.chambers
    : ["core", "fill", "ramp", "casing", "platform"].includes(kind)
      ? opacityState.structure
      : 1;
  if (setting <= 0.001) return 0;
  if (setting >= 0.999) return 1;
  return baseOpacity * setting;
}

function smoothstep(edge0, edge1, value) {
  const x = clamp((value - edge0) / (edge1 - edge0));
  return x * x * (3 - 2 * x);
}

function fadeInOut(value, start, inEnd, outStart, outEnd) {
  return smoothstep(start, inEnd, value) * (1 - smoothstep(outStart, outEnd, value));
}

function geometryVolume(geometry) {
  const position = geometry.getAttribute("position");
  if (!position) return 0;
  let volume = 0;
  for (let i = 0; i < position.count; i += 3) {
    const ax = position.getX(i);
    const ay = position.getY(i);
    const az = position.getZ(i);
    const bx = position.getX(i + 1);
    const by = position.getY(i + 1);
    const bz = position.getZ(i + 1);
    const cx = position.getX(i + 2);
    const cy = position.getY(i + 2);
    const cz = position.getZ(i + 2);
    volume += (
      ax * (by * cz - bz * cy)
      + ay * (bz * cx - bx * cz)
      + az * (bx * cy - by * cx)
    ) / 6;
  }
  return Math.abs(volume);
}

function setMaterial(mesh, color, opacity, options = {}) {
  const isXray = options.kind === "chambers" || options.kind === "subchambers";
  const materialOptions = {
    color,
    transparent: opacity < 1 || isXray,
    opacity,
    side: THREE.FrontSide,
    depthTest: options.depthTest !== false,
    depthWrite: isXray ? false : opacity >= 0.995,
  };
  const material = isXray
    ? new THREE.MeshBasicMaterial(materialOptions)
    : new THREE.MeshStandardMaterial({
      ...materialOptions,
      roughness: 0.72,
      metalness: 0.02,
    });
  if (isXray || options.kind === "platform" || options.kind === "casing") {
    material.polygonOffset = true;
    material.polygonOffsetFactor = isXray ? -1 : -2;
    material.polygonOffsetUnits = isXray ? -1 : -2;
  }
  mesh.material = material;
}

async function loadPart(def, loader) {
  const geometry = await loader.loadAsync(basePath + def.path);
  geometry.computeBoundingBox();
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry);
  setMaterial(mesh, def.color, def.opacity, def);
  const isXray = def.kind === "chambers" || def.kind === "subchambers";
  const softShadow = !isXray && def.kind !== "core" && def.kind !== "fill" && def.kind !== "platform";
  mesh.castShadow = softShadow;
  mesh.receiveShadow = softShadow;
  mesh.renderOrder = def.renderOrder || 0;
  mesh.userData.bounds = geometry.boundingBox.clone();
  mesh.userData.baseOpacity = def.opacity;
  mesh.userData.key = def.key;
  mesh.userData.kind = def.kind;
  mesh.userData.layer = def.layer;
  mesh.userData.casingIndex = def.casingIndex;
  mesh.userData.isXray = isXray;
  mesh.userData.volume = geometryVolume(geometry);
  scene.add(mesh);
  parts.set(def.key, mesh);
}

async function loadAll() {
  const loader = new STLLoader();
  const manifest = await fetch(basePath + "manifest.json")
    .then((response) => response.ok ? response.json() : null)
    .catch(() => null);
  const triangleCounts = new Map((manifest?.files || []).map((item) => [item.file, item.triangles]));
  const loadableDefs = partDefs.filter((def) => {
    const triangles = triangleCounts.get(def.path);
    if (triangles === 0) {
      skippedParts.push(def.key);
      return false;
    }
    return true;
  });
  await Promise.all(loadableDefs.map((def) => loadPart(def, loader)));
  createReusePile();
  frameScene();
  loading.hidden = true;
  updateAnimation(0);
}

function frameScene() {
  const bounds = new THREE.Box3();
  parts.forEach((part) => bounds.expandByObject(part));
  const center = bounds.getCenter(new THREE.Vector3());
  controls.target.copy(center);
  controls.target.z = 46;
  camera.position.copy(controls.target).add(defaultCameraOffset);
  cameraFitScale = 1;
  sceneFramed = true;
  fitCameraToAspect();
  controls.update();
}

function fitCameraToAspect() {
  if (!sceneFramed) return;
  const aspect = Math.max(0.45, camera.aspect);
  const nextScale = aspect < 1.05 ? Math.min(1.9, 1.05 / aspect) : 1;
  const offset = camera.position.clone().sub(controls.target);
  if (offset.lengthSq() < 0.0001) {
    offset.copy(defaultCameraOffset);
  }
  offset.multiplyScalar(nextScale / cameraFitScale);
  camera.position.copy(controls.target).add(offset);
  cameraFitScale = nextScale;
  controls.update();
}

function setVisible(mesh, visible, opacity = 1) {
  const finalOpacity = clamp(opacity);
  mesh.visible = visible && finalOpacity > 0.015;
  mesh.material.opacity = finalOpacity;
  mesh.material.transparent = finalOpacity < 0.995 || mesh.userData.isXray;
  mesh.material.depthWrite = mesh.userData.isXray ? false : finalOpacity >= 0.995;
  mesh.material.needsUpdate = true;
}

function setLayerVisibility() {
  parts.forEach((mesh, key) => {
    if (mesh.userData.kind === "core") mesh.visible = mesh.visible && toggles.core.checked;
    if (mesh.userData.kind === "fill") mesh.visible = mesh.visible && toggles.mound.checked;
    if (mesh.userData.kind === "ramp") mesh.visible = mesh.visible && toggles.ramps.checked;
    if (mesh.userData.kind === "chambers") mesh.visible = mesh.visible && toggles.chambers.checked;
    if (mesh.userData.kind === "subchambers") mesh.visible = mesh.visible && toggles.chambers.checked;
    if (key.startsWith("casing-")) mesh.visible = mesh.visible && toggles.casing.checked;
  });
}

function updateCopy(value) {
  if (value < 0.58) {
    stageTitle.textContent = "Fill and ramps build course by course";
    stageNote.textContent = "The lower chamber is already cut below grade; each inner mound, chamber, fill, and ramp layer then builds upward.";
  } else if (value < 0.68) {
    stageTitle.textContent = "Capstone set before deramping";
    stageNote.textContent = "The level platform and capstone settle while all temporary layers are still present.";
  } else if (value < 0.94) {
    stageTitle.textContent = "Top-down deramping, layer by layer";
    stageNote.textContent = "The upper ramp comes off first, its support fill follows, and the smooth casing ring appears in that cleared course.";
  } else {
    stageTitle.textContent = "Finished pyramid and reused material";
    stageNote.textContent = "The casing remains, while the animation pile shows removed temporary material accumulated by layer volume.";
  }
}

function layerPhaseAmount(value, layer, start, end, phaseStart, phaseEnd) {
  const span = (end - start) / layerCount;
  return smoothstep(start + (layer + phaseStart) * span, start + (layer + phaseEnd) * span, value);
}

function topDownRemovalAmount(value, layer, start, end, phaseStart, phaseEnd) {
  const topOrder = layerCount - 1 - layer;
  const span = (end - start) / layerCount;
  return smoothstep(start + (topOrder + phaseStart) * span, start + (topOrder + phaseEnd) * span, value);
}

function removedMaterialFraction(value) {
  let total = 0;
  let removed = 0;
  parts.forEach((mesh) => {
    const { kind, layer = 0, volume = 0 } = mesh.userData;
    if (kind !== "fill" && kind !== "ramp") return;
    const removal = kind === "ramp"
      ? topDownRemovalAmount(value, layer, 0.68, 0.94, 0.0, 0.48)
      : topDownRemovalAmount(value, layer, 0.68, 0.94, 0.36, 0.92);
    total += volume;
    removed += volume * removal;
  });
  return total > 0 ? clamp(removed / total) : 0;
}

function createReusePile() {
  reusePile.clear();
  reusePile.position.set(146, -118, 0);
  reusePile.rotation.z = -0.12;
  reusePile.visible = false;
  scene.add(reusePile);

  const slabMaterial = new THREE.MeshStandardMaterial({
    color: 0xb87a35,
    roughness: 0.86,
    metalness: 0.01,
    transparent: true,
    opacity: 0.82,
  });
  const blockMaterial = new THREE.MeshStandardMaterial({
    color: 0xca9551,
    roughness: 0.78,
    metalness: 0.01,
    transparent: true,
    opacity: 0.9,
  });

  const tiers = [
    { maxX: 96, maxY: 66, maxZ: 8, threshold: 0.0 },
    { maxX: 78, maxY: 52, maxZ: 7, threshold: 0.18 },
    { maxX: 58, maxY: 38, maxZ: 6, threshold: 0.42 },
    { maxX: 38, maxY: 25, maxZ: 5, threshold: 0.68 },
  ];
  tiers.forEach((tier, index) => {
    const slab = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), slabMaterial.clone());
    slab.castShadow = true;
    slab.receiveShadow = true;
    slab.userData.kind = "reuse-slab";
    slab.userData.tier = tier;
    slab.userData.baseZ = tiers.slice(0, index).reduce((sum, item) => sum + item.maxZ, 0);
    reusePile.add(slab);
  });

  const blocks = [];
  for (let level = 0; level < 5; level += 1) {
    const cols = 11 - level * 2;
    const rows = 7 - level;
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const block = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), blockMaterial.clone());
        const jitterX = Math.sin((row + 1) * (col + 3)) * 1.2;
        const jitterY = Math.cos((row + 4) * (col + 1)) * 1.0;
        const w = 6.5 + ((row + col + level) % 3) * 1.3;
        const d = 5.2 + ((row * 2 + col + level) % 3) * 1.0;
        const h = 3.3 + ((row + col) % 2) * 0.9;
        block.scale.set(w, d, h);
        block.position.set((col - (cols - 1) / 2) * 7.4 + jitterX, (row - (rows - 1) / 2) * 6.4 + jitterY, level * 4.0 + h / 2);
        block.castShadow = true;
        block.receiveShadow = true;
        blocks.push(block);
        reusePile.add(block);
      }
    }
  }
  blocks.forEach((block, index) => {
    block.userData.kind = "reuse-block";
    block.userData.threshold = index / Math.max(1, blocks.length - 1);
    block.userData.baseScale = block.scale.clone();
    block.userData.baseZ = block.position.z;
  });
}

function updateReusePile(value) {
  const fraction = removedMaterialFraction(value);
  const visualFraction = Math.pow(fraction, 1.28);
  window.__gizaDemo.removedMaterialFraction = fraction;
  window.__gizaDemo.reusePileVisualFraction = visualFraction;
  reusePile.visible = fraction > 0.004;
  reusePile.children.forEach((child) => {
    if (child.userData.kind === "reuse-slab") {
      const { maxX, maxY, maxZ, threshold } = child.userData.tier;
      const amount = smoothstep(threshold, threshold + 0.28, visualFraction);
      child.visible = amount > 0.01;
      child.scale.set(maxX * (0.18 + 0.82 * amount), maxY * (0.18 + 0.82 * amount), maxZ * amount);
      child.position.set(0, 0, child.userData.baseZ + (maxZ * amount) / 2);
      child.material.opacity = 0.18 + 0.68 * amount;
      child.material.needsUpdate = true;
      return;
    }
    const amount = smoothstep(child.userData.threshold, child.userData.threshold + 0.045, visualFraction);
    child.visible = amount > 0.02;
    child.scale.set(
      child.userData.baseScale.x,
      child.userData.baseScale.y,
      child.userData.baseScale.z * amount,
    );
    child.position.z = child.userData.baseZ - (child.userData.baseScale.z * (1 - amount)) / 2;
    child.material.opacity = 0.35 + 0.55 * amount;
    child.material.needsUpdate = true;
  });
}

function updateAnimation(value) {
  syncOpacityControls();
  progress = clamp(value);
  window.__gizaDemo.progress = progress;
  timelineInput.value = Math.round(progress * 1000);
  updateCopy(progress);

  parts.forEach((mesh) => {
    const { kind, layer = 0 } = mesh.userData;
    if (!["core", "fill", "ramp", "chambers"].includes(kind)) return;
    const build = kind === "ramp"
      ? layerPhaseAmount(progress, layer, 0.02, 0.58, 0.34, 0.92)
      : layerPhaseAmount(progress, layer, 0.02, 0.58, 0.0, 0.48);
    const removal = kind === "ramp"
      ? topDownRemovalAmount(progress, layer, 0.68, 0.94, 0.0, 0.48)
      : kind === "fill"
        ? topDownRemovalAmount(progress, layer, 0.68, 0.94, 0.36, 0.92)
        : 0;
    const coreCover = kind === "core" && toggles.casing.checked
      ? topDownRemovalAmount(progress, layer, 0.68, 0.94, 0.48, 1.0)
      : 0;
    const opacity = opacityForKind(kind, mesh.userData.baseOpacity) * build * (1 - removal) * (1 - coreCover);
    const lift = kind === "chambers" ? 0 : 10 * (1 - build);
    mesh.position.set(16 * removal, -10 * removal, -18 * removal - lift);
    const toggle = kind === "core" ? toggles.core : kind === "fill" ? toggles.mound : kind === "ramp" ? toggles.ramps : toggles.chambers;
    setVisible(mesh, toggle.checked, opacity);
  });

  const platform = parts.get("platform");
  if (platform) {
    const amount = fadeInOut(progress, 0.52, 0.6, 0.66, 0.7);
    platform.position.set(0, 0, 0.06);
    setVisible(platform, true, opacityForKind("platform", platform.userData.baseOpacity) * amount);
  }

  const subchambers = parts.get("subchambers");
  if (subchambers) {
    subchambers.position.set(0, 0, 0);
    setVisible(subchambers, toggles.chambers.checked, opacityForKind("subchambers", subchambers.userData.baseOpacity));
  }

  const capstone = parts.get("capstone");
  if (capstone) {
    const amount = smoothstep(0.58, 0.68, progress);
    capstone.position.set(0, 0, 0);
    setVisible(capstone, true, capstone.userData.baseOpacity * amount);
  }

  parts.forEach((mesh, key) => {
    if (!key.startsWith("casing-")) return;
    const index = mesh.userData.casingIndex;
    const correspondingLayer = layerCount - 1 - index;
    const amount = topDownRemovalAmount(progress, correspondingLayer, 0.68, 0.94, 0.48, 1.0);
    mesh.position.set(0, 0, 12 * (1 - amount));
    setVisible(mesh, toggles.casing.checked, opacityForKind("casing", mesh.userData.baseOpacity) * amount);
  });

  updateReusePile(progress);

  setLayerVisibility();
}

function resize() {
  const rect = viewport.getBoundingClientRect();
  renderer.setSize(rect.width, rect.height, false);
  camera.aspect = rect.width / rect.height;
  camera.updateProjectionMatrix();
  fitCameraToAspect();
}

function tick(now) {
  const delta = Math.min(0.05, (now - lastTime) / 1000);
  lastTime = now;
  if (playing) {
    const next = (progress + delta * 0.055) % 1;
    updateAnimation(next);
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

playButton.addEventListener("click", () => {
  playing = !playing;
  playButton.textContent = playing ? "Pause" : "Play";
});

resetButton.addEventListener("click", () => {
  playing = false;
  playButton.textContent = "Play";
  updateAnimation(0);
});

timelineInput.addEventListener("input", () => {
  playing = false;
  playButton.textContent = "Play";
  updateAnimation(Number(timelineInput.value) / 1000);
});

Object.values(toggles).forEach((toggle) => {
  toggle.addEventListener("change", () => updateAnimation(progress));
});

[structureOpacityInput, chamberOpacityInput].forEach((input) => {
  input?.addEventListener("input", () => updateAnimation(progress));
});

window.addEventListener("resize", resize);
resize();
syncOpacityControls();
loadAll().catch((error) => {
  reportError(error);
  loading.textContent = "Could not load STL parts. Run python3 generate_giza_kit.py, then serve this folder over HTTP.";
});
requestAnimationFrame(tick);
