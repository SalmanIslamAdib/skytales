let currentLightCurve = null;

async function fetchLightCurve() {
  const target = document.getElementById("target-input").value.trim() || "TOI-700";
  const mission = document.getElementById("mission-select").value;
  const synthetic = document.getElementById("synthetic-toggle").checked;

  try {
    const data = await apiGet(
      `/api/lightcurve/${encodeURIComponent(target)}?mission=${mission}&synthetic=${synthetic}`
    );
    currentLightCurve = data;
    plotLightCurve(data);
  } catch (e) {
    console.error(e);
    alert("Failed to fetch light curve: " + e.message);
  }
}

function plotLightCurve(data) {
  const trace = {
    x: data.time,
    y: data.flux,
    mode: "markers",
    type: "scattergl",
    marker: { size: 3, color: "#7fdbff" },
    name: data.target,
  };
  const layout = {
    margin: { t: 20, r: 10, l: 40, b: 30 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#e8ecf7", size: 10 },
    xaxis: { title: "Time (days)", gridcolor: "#1e2440" },
    yaxis: { title: "Flux", gridcolor: "#1e2440" },
  };
  Plotly.newPlot("lightcurve-plot", [trace], layout, { responsive: true, displayModeBar: false });

  if (data.fallback_reason) {
    console.warn("Using fallback synthetic curve:", data.fallback_reason);
  }
}

async function runTransitDetection() {
  const box = document.getElementById("transit-result");
  if (!currentLightCurve) { box.textContent = "Fetch a light curve first."; return; }
  box.textContent = "running LSTM + autoencoder…";
  try {
    const result = await apiPost("/api/transit", { flux: currentLightCurve.flux });
    box.textContent =
      `Transit probability (LSTM): ${(result.transit_probability * 100).toFixed(1)}%\n` +
      `Reconstruction error (AE): ${result.reconstruction_error.toFixed(4)}\n` +
      `Anomaly flagged: ${result.is_anomaly_autoencoder}\n` +
      `Combined detection: ${result.combined_detection}`;
  } catch (e) {
    box.textContent = "Failed: " + e.message;
  }
}

async function runTransientFilter() {
  const box = document.getElementById("transient-result");
  if (!currentLightCurve) { box.textContent = "Fetch a light curve first."; return; }
  box.textContent = "running rules + LLM filter…";
  try {
    const result = await apiPost("/api/transient", {
      flux: currentLightCurve.flux,
      target_name: currentLightCurve.target,
    });
    let text = `Passed rules: ${result.passed_rules}\n`;
    if (result.rule_reasons.length) text += `Reasons: ${result.rule_reasons.join(", ")}\n`;
    text += `LLM used: ${result.llm_triage.llm_used}\n`;
    text += `Note: ${result.llm_triage.note}`;
    box.textContent = text;
  } catch (e) {
    box.textContent = "Failed: " + e.message;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("fetch-lc-btn").addEventListener("click", fetchLightCurve);
  document.getElementById("run-transit-btn").addEventListener("click", runTransitDetection);
  document.getElementById("run-transient-btn").addEventListener("click", runTransientFilter);
});
