// Ganti ini kalau backend dijalankan di alamat/port berbeda saat deploy
const API_BASE_URL = "http://localhost:8000";

const form = document.getElementById("process-form");
const urlInput = document.getElementById("youtube-url");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const resultsTitle = document.getElementById("results-title");
const clipsGrid = document.getElementById("clips-grid");

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.remove("hidden", "error");
  if (isError) statusEl.classList.add("error");
}

function hideStatus() {
  statusEl.classList.add("hidden");
}

function renderClips(data) {
  resultsTitle.textContent = `Klip dari: ${data.video_title}`;
  clipsGrid.innerHTML = "";

  data.clips.forEach((clip) => {
    const card = document.createElement("div");
    card.className = "clip-card";
    card.innerHTML = `
      <h3>${clip.title}</h3>
      <p>${clip.reason}</p>
      <a href="${API_BASE_URL}${clip.download_url}" download target="_blank" rel="noopener">
        Unduh klip &rarr;
      </a>
    `;
    clipsGrid.appendChild(card);
  });

  resultsEl.classList.remove("hidden");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const youtubeUrl = urlInput.value.trim();
  if (!youtubeUrl) return;

  submitBtn.disabled = true;
  resultsEl.classList.add("hidden");
  showStatus("Memproses video... ini bisa memakan waktu beberapa menit tergantung panjang video.");

  try {
    const res = await fetch(`${API_BASE_URL}/api/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_url: youtubeUrl }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Terjadi kesalahan saat memproses video.");
    }

    hideStatus();
    renderClips(data);
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    submitBtn.disabled = false;
  }
});
