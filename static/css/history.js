// history.js — fetches /api/history and renders cards; handles clear button

document.addEventListener("DOMContentLoaded", loadHistory);

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const history = await res.json();
    renderHistory(history);
  } catch (err) {
    console.error("Failed to load history", err);
  }
}

function renderHistory(history) {
  const grid = document.getElementById("historyGrid");
  const emptyNote = document.getElementById("historyEmptyNote");
  grid.innerHTML = "";

  if (!history || history.length === 0) {
    emptyNote.style.display = "block";
    return;
  }
  emptyNote.style.display = "none";

  history.forEach(entry => {
    const card = document.createElement("div");
    card.className = "history-card";
    const time = new Date(entry.timestamp).toLocaleString();
    const bioLabel = entry.biodegradable === true ? "Biodegradable" : entry.biodegradable === false ? "Non-Biodegradable" : entry.biodegradable;
    card.innerHTML = `
      <img src="/uploads/${entry.image_filename}" alt="${entry.predicted_class}" onerror="this.style.display='none'">
      <div class="history-card-body">
        <h4>${entry.predicted_class}</h4>
        <div class="hc-meta"><span>${entry.confidence}%</span><span>${bioLabel}</span></div>
        <div class="hc-meta"><span>${entry.recyclable}</span><span>${time}</span></div>
      </div>
    `;
    grid.appendChild(card);
  });
}

document.getElementById("clearHistoryBtn").addEventListener("click", async () => {
  if (!confirm("Clear all prediction history? This cannot be undone.")) return;
  try {
    await fetch("/api/history/clear", { method: "POST" });
    loadHistory();
    showToast("History cleared.");
  } catch (err) {
    showToast("Failed to clear history.");
  }
});
