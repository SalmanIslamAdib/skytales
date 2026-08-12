async function loadSkyView(lat, lon) {
  const plotDiv = document.getElementById("sky-view-plot");
  const detailPanel = document.getElementById("sky-detail-panel");
  detailPanel.classList.add("hidden");
  plotDiv.innerHTML = "<p class='hint'>Loading sky view…</p>";
  try {
    const data = await apiGet(`/api/sky_view?lat=${lat}&lon=${lon}`);

    if (data.count === 0) {
      plotDiv.innerHTML = "<p class='hint'>No cataloged stars are above the horizon right now at this location/time.</p>";
      return;
    }

    const lineTraces = data.constellation_lines.map((line) => ({
      type: "scatterpolar",
      mode: "lines",
      r: [90 - line.star1.alt, 90 - line.star2.alt],
      theta: [line.star1.az, line.star2.az],
      line: { color: "#3d4a7a", width: 1 },
      hoverinfo: "skip",
      showlegend: false,
      meta: { kind: "constellation_line", constellation: line.constellation, fact: line.constellation_fact },
    }));

    // A soft, larger, low-opacity halo behind each star for a glow effect —
    // real telescope views show bright stars with a visible glow, not a flat dot.
    const glowTrace = {
      type: "scatterpolar",
      mode: "markers",
      r: data.stars.map((s) => 90 - s.alt),
      theta: data.stars.map((s) => s.az),
      marker: {
        size: data.stars.map((s) => Math.max(14, 26 - s.magnitude * 2)),
        color: data.stars.map((s) => s.color),
        opacity: 0.25,
      },
      hoverinfo: "skip",
      showlegend: false,
    };

    // The crisp star point on top, colored by its real spectral type/temperature.
    const starTrace = {
      type: "scatterpolar",
      mode: "markers+text",
      r: data.stars.map((s) => 90 - s.alt),
      theta: data.stars.map((s) => s.az),
      text: data.stars.map((s) => s.name),
      textposition: "top center",
      textfont: { size: 9, color: "#c9cfe6" },
      marker: {
        size: data.stars.map((s) => Math.max(5, 12 - s.magnitude * 1.3)),
        color: data.stars.map((s) => s.color),
        line: { color: "#ffffff33", width: 1 },
      },
      hovertemplate: "%{text}<extra></extra>",
      customdata: data.stars,
      name: "Stars",
      showlegend: false,
    };

    const layout = {
      polar: {
        bgcolor: "radial-gradient(circle, #0a0e1e, #000)",
        radialaxis: { visible: true, range: [0, 90], showticklabels: false, gridcolor: "#1a2040" },
        angularaxis: {
          direction: "clockwise", rotation: 90, gridcolor: "#1a2040", color: "#8a92b2",
          tickmode: "array",
          tickvals: [0, 90, 180, 270],
          ticktext: ["N", "E", "S", "W"],
          tickfont: { size: 13, color: "#7fdbff" },
        },
      },
      paper_bgcolor: "transparent",
      plot_bgcolor: "#05070f",
      font: { color: "#e8ecf7", size: 10 },
      margin: { t: 30, r: 30, l: 30, b: 30 },
      title: { text: `${data.count} stars visible above the horizon`, font: { size: 12, color: "#8a92b2" } },
    };

    plotDiv.innerHTML = "";
    Plotly.newPlot("sky-view-plot", [...lineTraces, glowTrace, starTrace], layout, {
      responsive: true,
      displayModeBar: false,
    });

    const starTraceIndex = lineTraces.length + 1;

    plotDiv.on("plotly_click", (evt) => {
      const point = evt.points[0];
      const trace = point.data;

      if (trace.meta && trace.meta.kind === "constellation_line") {
        showConstellationDetail(trace.meta.constellation, trace.meta.fact, data.constellation_lines, data.stars);
        highlightConstellation(trace.meta.constellation, starTraceIndex);
      } else if (trace.customdata) {
        showStarDetail(point.customdata);
      }
    });
  } catch (e) {
    plotDiv.innerHTML = `<p class="hint">Failed to load sky view: ${e.message}</p>`;
  }
}

function magnitudeToPercent(mag) {
  // Visual magnitude scale is inverted (lower = brighter). Map roughly
  // -1.5 (brightest, Sirius) .. 3.5 (faintest cataloged) onto a 0-100% bar.
  const clamped = Math.max(-1.5, Math.min(3.5, mag));
  return Math.round(((3.5 - clamped) / 5) * 100);
}

function showStarDetail(star) {
  const panel = document.getElementById("sky-detail-panel");
  panel.classList.remove("hidden");
  const brightnessPct = magnitudeToPercent(star.magnitude);
  const dist = star.distance_ly ? star.distance_ly.toLocaleString() : "unknown";

  panel.innerHTML = `
    <div class="sky-detail-header">
      <div class="star-swatch" style="background:${star.color}; color:${star.color};"></div>
      <div>
        <div class="sky-detail-title">${star.name}</div>
        <div class="sky-detail-subtitle">${star.constellation} · ${star.spectral_type}-type star</div>
      </div>
    </div>
    <div class="meter-row">
      Brightness
      <div class="meter-track"><div class="meter-fill" style="width:${brightnessPct}%"></div></div>
    </div>
    <div class="meter-row">
      Height above horizon
      <div class="meter-track"><div class="meter-fill" style="width:${Math.round((star.alt / 90) * 100)}%"></div></div>
    </div>
    <div class="sky-detail-subtitle">${dist} light-years away · facing ${Math.round(star.az)}° on the compass</div>
    ${star.constellation_fact ? `<div class="sky-detail-fact">${star.constellation_fact}</div>` : ""}
  `;
}

function showConstellationDetail(name, fact, allLines, allStars) {
  const panel = document.getElementById("sky-detail-panel");
  panel.classList.remove("hidden");
  const starsInConstellation = allStars.filter((s) => s.constellation === name);
  const chips = starsInConstellation.map((s) => `<span class="constellation-star-chip">${s.name}</span>`).join("");

  panel.innerHTML = `
    <div class="sky-detail-header">
      <div class="star-swatch" style="background:#ff6ad5; color:#ff6ad5;"></div>
      <div>
        <div class="sky-detail-title">${name}</div>
        <div class="sky-detail-subtitle">${starsInConstellation.length} stars visible now</div>
      </div>
    </div>
    <div class="sky-detail-fact">${fact}</div>
    <div style="margin-top:10px;">${chips}</div>
  `;
}

function highlightConstellation(constellationName, starTraceIndex) {
  const plotDiv = document.getElementById("sky-view-plot");
  const colors = [];
  const widths = [];
  const indices = [];
  plotDiv.data.forEach((trace, i) => {
    if (i >= starTraceIndex) return; // skip glow + star marker traces
    const isMatch = trace.meta && trace.meta.constellation === constellationName;
    colors.push(isMatch ? "#ff6ad5" : "#3d4a7a");
    widths.push(isMatch ? 3 : 1);
    indices.push(i);
  });
  Plotly.restyle(plotDiv, { "line.color": colors, "line.width": widths }, indices);
}

function useMyLocation() {
  if (!navigator.geolocation) {
    alert("Geolocation isn't supported by this browser — enter coordinates manually instead.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      document.getElementById("lat-input").value = pos.coords.latitude.toFixed(4);
      document.getElementById("lon-input").value = pos.coords.longitude.toFixed(4);
      loadSkyView(pos.coords.latitude, pos.coords.longitude);
    },
    (err) => {
      alert("Couldn't get your location: " + err.message + " — enter coordinates manually instead.");
    }
  );
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("use-location-btn").addEventListener("click", useMyLocation);
  document.getElementById("show-sky-btn").addEventListener("click", () => {
    const lat = parseFloat(document.getElementById("lat-input").value);
    const lon = parseFloat(document.getElementById("lon-input").value);
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      alert("Enter a valid latitude and longitude, or click 'Use My Location'.");
      return;
    }
    loadSkyView(lat, lon);
  });
});
