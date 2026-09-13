// dashboard.js — fetches /api/dashboard-stats and renders charts + tables

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/api/dashboard-stats");
    const data = await res.json();
    renderStats(data);
  } catch (err) {
    console.error("Failed to load dashboard stats", err);
  }
});

function renderStats(data) {
  document.getElementById("statTotal").textContent = data.total_classifications;
  document.getElementById("statMostFrequent").textContent = data.most_frequent_class || "—";
  document.getElementById("statAvgConfidence").textContent = data.average_confidence + "%";

  const bio = data.biodegradable_vs_non;
  const bioTotal = bio.biodegradable + bio.non_biodegradable;
  const bioPct = bioTotal > 0 ? Math.round((bio.biodegradable / bioTotal) * 100) : 0;
  document.getElementById("statBiodegPct").textContent = bioPct + "%";

  // Category breakdown bar chart
  const catLabels = Object.keys(data.class_counts);
  const catValues = Object.values(data.class_counts);
  new Chart(document.getElementById("categoryChart"), {
    type: "bar",
    data: {
      labels: catLabels,
      datasets: [{
        label: "Classifications",
        data: catValues,
        backgroundColor: "#16a34a",
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });

  // Biodegradable donut
  new Chart(document.getElementById("biodegChart"), {
    type: "doughnut",
    data: {
      labels: ["Biodegradable", "Non-Biodegradable"],
      datasets: [{ data: [bio.biodegradable, bio.non_biodegradable], backgroundColor: ["#16a34a", "#94a3b8"] }],
    },
    options: { responsive: true, plugins: { legend: { position: "bottom" } } },
  });

  // Recyclable donut
  const rec = data.recyclable_vs_non;
  new Chart(document.getElementById("recycleChart"), {
    type: "doughnut",
    data: {
      labels: ["Recyclable", "Non-Recyclable"],
      datasets: [{ data: [rec.recyclable, rec.non_recyclable], backgroundColor: ["#0ea5e9", "#f59e0b"] }],
    },
    options: { responsive: true, plugins: { legend: { position: "bottom" } } },
  });

  // Recent table
  const tbody = document.getElementById("recentTableBody");
  const emptyNote = document.getElementById("recentEmptyNote");
  if (!data.recent || data.recent.length === 0) {
    emptyNote.style.display = "block";
    return;
  }
  data.recent.forEach(entry => {
    const tr = document.createElement("tr");
    const time = new Date(entry.timestamp).toLocaleString();
    tr.innerHTML = `
      <td>${entry.predicted_class}</td>
      <td>${entry.confidence}%</td>
      <td>${entry.biodegradable === true ? "Yes" : entry.biodegradable === false ? "No" : entry.biodegradable}</td>
      <td>${entry.recyclable}</td>
      <td>${time}</td>
    `;
    tbody.appendChild(tr);
  });
}
