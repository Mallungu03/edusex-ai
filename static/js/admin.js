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
