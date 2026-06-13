const predictForm = document.querySelector("#predictForm");
const predictionResult = document.querySelector("#predictionResult");

predictForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await apiFetch("/ml/predict", {
    method: "POST",
    body: JSON.stringify(formToJson(predictForm)),
  });
  renderJson(predictionResult, await response.json());
});
