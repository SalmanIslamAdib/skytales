let scene, camera, renderer, starPoints, raycaster, mouse;
let starData = [];

function initSkyMap() {
  const container = document.getElementById("sky-map");
  const width = container.clientWidth;
  const height = container.clientHeight;

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 5000);
  camera.position.z = 300;

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  container.appendChild(renderer.domElement);

  raycaster = new THREE.Raycaster();
  raycaster.params.Points.threshold = 2;
  mouse = new THREE.Vector2();

  let dragging = false, lastX = 0, lastY = 0, rotX = 0, rotY = 0;
  renderer.domElement.addEventListener("mousedown", (e) => { dragging = true; lastX = e.clientX; lastY = e.clientY; });
  window.addEventListener("mouseup", () => dragging = false);
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    rotY += (e.clientX - lastX) * 0.005;
    rotX += (e.clientY - lastY) * 0.005;
    lastX = e.clientX; lastY = e.clientY;
    if (starPoints) { starPoints.rotation.y = rotY; starPoints.rotation.x = rotX; }
  });
  renderer.domElement.addEventListener("wheel", (e) => {
    camera.position.z = Math.max(50, Math.min(1500, camera.position.z + e.deltaY * 0.2));
  });
  renderer.domElement.addEventListener("click", onStarClick);

  animate();
  loadStars();
}

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}

async function loadStars() {
  document.getElementById("star-count").textContent = "loading…";
  try {
    const data = await apiGet("/api/stars?n=3000");
    starData = data.stars;
    document.getElementById("star-count").textContent = data.count;
    renderStars(starData);
  } catch (e) {
    document.getElementById("star-count").textContent = "error";
    console.error(e);
  }
}

const CLASS_COLOR = {
  O: 0x9bb0ff, B: 0xaabfff, A: 0xcad7ff, F: 0xf8f7ff, G: 0xfff4ea, K: 0xffd2a1, M: 0xffcc6f,
};

function renderStars(stars) {
  if (starPoints) scene.remove(starPoints);

  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(stars.length * 3);
  const colors = new Float32Array(stars.length * 3);
  const scale = 0.6; // pc -> scene units

  stars.forEach((s, i) => {
    positions[i * 3] = s.x * scale;
    positions[i * 3 + 1] = s.y * scale;
    positions[i * 3 + 2] = s.z * scale;

    const hex = CLASS_COLOR[s.spectral_class] || 0xffffff;
    const c = new THREE.Color(hex);
    colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
  });

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 2.2,
    vertexColors: true,
    sizeAttenuation: true,
  });

  starPoints = new THREE.Points(geometry, material);
  scene.add(starPoints);
}

function onStarClick(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObject(starPoints);
  if (intersects.length === 0) return;

  const idx = intersects[0].index;
  const star = starData[idx];
  showStarInfo(star);
  classifyStar(star);
}

function showStarInfo(star) {
  const box = document.getElementById("star-info");
  box.classList.remove("hidden");
  box.innerHTML = `
    <strong>${star.name}</strong><br/>
    Spectral: ${star.spectral_class}<br/>
    Mag: ${star.magnitude}<br/>
    Distance: ${star.distance_pc} pc<br/>
    Color idx: ${star.color_index ?? "n/a"}
  `;
}

async function classifyStar(star) {
  const resultBox = document.getElementById("classify-result");
  resultBox.textContent = "classifying…";
  try {
    const result = await apiPost("/api/classify", {
      color_index: star.color_index,
      magnitude: star.magnitude,
    });
    resultBox.textContent = `Predicted: ${result.predicted_class} (${(result.confidence * 100).toFixed(1)}%)\n` +
      Object.entries(result.probabilities).map(([k, v]) => `  ${k}: ${(v * 100).toFixed(1)}%`).join("\n");
  } catch (e) {
    resultBox.textContent = "Classification failed: " + e.message;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initSkyMap();
  document.getElementById("reload-stars").addEventListener("click", loadStars);
});
