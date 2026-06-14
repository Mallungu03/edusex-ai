const uploadForm = document.querySelector("#uploadForm");
const uploadResult = document.querySelector("#uploadResult");
const apiKeyBtn = document.querySelector("#apiKeyBtn");
const apiKeyResult = document.querySelector("#apiKeyResult");
const trainBtn = document.querySelector("#trainBtn");
const trainResult = document.querySelector("#trainResult");

if (uploadForm) {
  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await apiFetch("/surveys/upload", {
      method: "POST",
      body: new FormData(uploadForm),
      headers: {},
    });
    renderJson(uploadResult, await response.json());
  });
}

apiKeyBtn.addEventListener("click", async () => {
  const response = await apiFetch("/auth/api-keys", { method: "POST", body: "{}" });
  renderJson(apiKeyResult, await response.json());
});

if (trainBtn) {
  trainBtn.addEventListener("click", async () => {
    const response = await apiFetch("/ml/train", { method: "POST", body: "{}" });
    renderJson(trainResult, await response.json());
  });
}

// Load AI metrics for admin monitoring
async function loadAiMetrics() {
  const res = await apiFetch('/api/v2/ai/metrics');
  if (!res) return;
  const data = await res.json();
  document.querySelector('#aiTotal').textContent = data.total_calls || 0;
  document.querySelector('#aiErrors').textContent = data.errors || 0;
  document.querySelector('#aiLatency').textContent = data.avg_latency || 0;
  document.querySelector('#aiModels').textContent = JSON.stringify(data.models || {}, null, 2);
}

document.addEventListener('DOMContentLoaded', () => {
  loadAiMetrics();
});
