(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char]));

  function renderStats(data) {
    const overview = data.overview;
    $("metrics").innerHTML = [
      ["Students tracked", overview.students, "observations"],
      ["Average score", `${overview.average_score} / 10`, "dataset mean"],
      ["Daily social use", `${overview.average_usage} h`, "average per day"],
      ["Very high stress", `${overview.high_stress_share}%`, "of students"],
    ].map(([label, value, note]) => `<div class="metric"><span>${label}</span><b>${value}</b><small>${note}</small></div>`).join("");

    const maxScore = Math.max(...data.score_distribution.map((item) => item.value));
    $("distribution").innerHTML = data.score_distribution.map((item, index) => `
      <div class="bar-wrap"><div class="bar ${index === 3 ? "accent" : ""}" style="height:${Math.max(5, item.value / maxScore * 180)}px"><em>${item.value}</em></div><div class="bar-label">${esc(item.label)}</div></div>
    `).join("");

    const renderRows = (items, target) => {
      const maxValue = Math.max(...items.map((item) => item.value));
      $(target).innerHTML = items.map((item) => `
        <div class="row"><span>${esc(item.label)}</span><div class="track"><div class="fill" style="width:${item.value / maxValue * 100}%"></div></div><b>${item.value}</b></div>
      `).join("");
    };
    renderRows(data.platforms, "platforms");
    renderRows(data.stress_levels, "stress");
  }

  function setTheme(theme) {
    document.body.dataset.theme = theme;
    localStorage.setItem("mindline-theme", theme);
    $("theme").textContent = theme === "night" ? "Day mode" : "Night mode";
  }

  fetch("/api/stats").then((response) => response.json()).then(renderStats).catch(() => {
    $("metrics").innerHTML = '<div class="metric"><span>Dataset</span><b>Offline</b><small>Could not load statistics</small></div>';
  });

  setTheme(localStorage.getItem("mindline-theme") || "day");
  $("theme").addEventListener("click", () => setTheme(document.body.dataset.theme === "night" ? "day" : "night"));

  $("predict-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const data = Object.fromEntries(formData.entries());
    ["age", "avg_daily_usage_hours", "daily_unlocks", "study_hours", "physical_activity_hours", "sleep_hours_per_night"].forEach((key) => { data[key] = Number(data[key]); });
    const result = $("result");
    result.classList.add("show");
    $("result-value").textContent = "Calculating...";
    try {
      const response = await fetch("/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Prediction failed");
      const score = Number(body.predicted_mental_health_score);
      $("result-value").textContent = `${score.toFixed(2)} / 10`;
      $("result-note").textContent = score >= 7.5 ? "Strong projected wellbeing profile." : score >= 5.5 ? "Balanced profile with room for small improvements." : "A signal to pause and consider additional support.";
    } catch (error) {
      $("result-value").textContent = "Unavailable";
      $("result-note").textContent = error.message;
    }
  });
})();
