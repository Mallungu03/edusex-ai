function boolValue(data, key) {
  return data[key] === true || data[key] === "on";
}

async function explainPayload(payload) {
  const response = await apiFetch("/analytics/explain", { method: "POST", body: JSON.stringify(payload) });
  if (!response) return;
  const result = await response.json();
  document.querySelector("#explainResult").innerHTML = `
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <div class="metric-label">Resultado</div>
        <div class="metric-value">${result.result}</div>
      </div>
      <span class="score-pill">${result.score}/100</span>
    </div>
    <h2>Motivos</h2>
    <ul class="clean-list">${result.reasons.map((reason) => `<li><i class="bi bi-check-circle text-success"></i> ${reason}</li>`).join("") || "<li>Sem fatores fortes de risco.</li>"}</ul>
    <h2>Importância das variáveis</h2>
    ${result.featureImportance.map((item) => `
      <div class="mb-2">
        <div class="d-flex justify-content-between"><span>${item.feature}</span><span>${Math.round(item.importance * 100)}%</span></div>
        <div class="progress"><div class="progress-bar" style="width:${Math.round(item.importance * 100)}%"></div></div>
        <small class="text-secondary">${item.explanation}</small>
      </div>
    `).join("")}
    <h2>Regras da Decision Tree</h2>
    <ul class="clean-list">${result.decisionTreeRules.map((rule) => `<li><i class="bi bi-diagram-3"></i> ${rule}</li>`).join("")}</ul>
    <div class="alert alert-info mb-0">${result.shap.message}</div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#explainForm");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    ["receivedSexEducation", "schoolEducation", "needMoreInformation", "feelsEmbarrassed", "contraceptiveUse"].forEach((key) => {
      data[key] = boolValue(data, key);
    });
    data.age = Number(data.age);
    explainPayload(data);
  });
  form.requestSubmit();
});
