const API_BASE = "https://skytales-3r27.onrender.com";

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

async function checkHealth() {
  const pill = document.getElementById("api-status");
  try {
    const data = await apiGet("/api/health");
    pill.textContent = `API: ${data.status}`;
    pill.classList.add("ok");
  } catch (e) {
    pill.textContent = "API: offline (start backend/app.py)";
    pill.classList.add("err");
  }
}

document.addEventListener("DOMContentLoaded", checkHealth);
