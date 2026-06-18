const predictForm = document.querySelector("#predictForm");
const predictionResult = document.querySelector("#predictionResult");

function escapeHtml(value) {
  const span = document.createElement("span");
  span.textContent = value ?? "";
  return span.innerHTML;
}

function renderPrediction(element, payload) {
  if (!payload || typeof payload !== "object") {
    element.innerHTML = `<div class="alert-box">Erro ao processar o resultado.</div>`;
    return;
  }

  if (payload.error || payload.message) {
    element.innerHTML = `<div class="alert-box">${escapeHtml(payload.error || payload.message)}</div>`;
    return;
  }

  const risk = payload.risk || payload.score?.category || "Desconhecido";
  const label = payload.score?.label || risk;
  const score = typeof payload.score?.score === "number" ? payload.score.score : null;
  const reasons = Array.isArray(payload.score?.reasons) ? payload.score.score ? payload.score.reasons : payload.score.reasons : [];
  const recommendations = Array.isArray(payload.recommendations) ? payload.recommendations : [];
  const safeRisk = escapeHtml(risk);
  const safeLabel = escapeHtml(label);
  const safeScore = score === null ? "—" : `${score} / 100`;
  const scorePercent = score === null ? 0 : Math.max(0, Math.min(100, score));

  const colorClass = risk === "Alto" ? "danger" : risk === "Médio" ? "warning" : "success";
  const reasonsHtml = reasons.length
    ? `<ul class="clean-list">${reasons.map((item) => `<li><span>•</span>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "<p class=\"muted-text\">Nenhum fator de risco específico foi identificado.</p>";
  const recommendationsHtml = recommendations.length
    ? `<ul class="clean-list">${recommendations.map((item) => `<li><span>✓</span>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "<p class=\"muted-text\">Sem recomendações adicionais no momento.</p>";

  element.innerHTML = `
    <div class="prediction-card animated-card">
      <div class="prediction-header">
        <div>
          <p class="prediction-label">Risco previsto</p>
          <h2>${safeRisk}</h2>
          <p class="muted-text mb-0">${safeLabel}</p>
        </div>
        <span class="score-pill ${colorClass}">${safeLabel}</span>
      </div>

      <div class="prediction-metrics">
        <div class="metric">
          <p class="metric-label">Pontuação de desinformação</p>
          <p class="metric-value">${safeScore}</p>
        </div>
        <div class="progress">
          <div class="progress-bar ${colorClass}" style="width: ${scorePercent}%;"></div>
        </div>
      </div>

      <div class="prediction-section">
        <h3>Fatores de risco</h3>
        ${reasonsHtml}
      </div>

      <div class="prediction-section">
        <h3>Recomendações</h3>
        ${recommendationsHtml}
      </div>
    </div>
  `;
}

predictForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  predictionResult.innerHTML = `<div class="empty-state">Carregando resultado...</div>`;
  const response = await apiFetch("/ml/predict", {
    method: "POST",
    body: JSON.stringify(formToJson(predictForm)),
  });

  const payload = await response.json();
  renderPrediction(predictionResult, payload);
});
