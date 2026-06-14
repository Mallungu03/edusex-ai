async function loadAiDashboard() {
  const [comparisonResponse, trendsResponse, profilesResponse, alertsResponse, insightsResponse, aiStatusResponse, sentimentStatsResponse] = await Promise.all([
    apiFetch("/analytics/model-comparison"),
    apiFetch("/analytics/trends"),
    apiFetch("/analytics/risk-profiles"),
    apiFetch("/analytics/alerts"),
    apiFetch("/analytics/insights"),
    apiFetch("/api/v2/ai/status"),
    apiFetch("/api/v2/sentiment/stats"),
  ]);
  if (!comparisonResponse || !trendsResponse || !profilesResponse || !alertsResponse || !insightsResponse) return;
  const comparison = await comparisonResponse.json();
  const trends = await trendsResponse.json();
  const profiles = await profilesResponse.json();
  const alerts = await alertsResponse.json();
  const insights = await insightsResponse.json();

  document.querySelector("#aiCards").innerHTML = [
    ["Melhor modelo", comparison.bestModel, "bi-award"],
    ["Accuracy", comparison.metrics.find((item) => item.model === comparison.bestModel)?.accuracy || 0, "bi-bullseye"],
    ["Awareness", `${insights.awarenessScore}/100`, "bi-activity"],
    ["Alertas", alerts.length, "bi-bell"],
  ].map(([label, value, icon]) => `<div class="col-6 col-lg-3"><div class="panel metric animated-card"><i class="bi ${icon}"></i><div class="metric-value">${value}</div><div class="metric-label">${label}</div></div></div>`).join("");

  new Chart(document.querySelector("#trendChart"), {
    type: "line",
    data: {
      labels: trends.future.map((item) => item.period),
      datasets: [
        { label: "Desinformação", data: trends.future.map((item) => item.misinformationIndex), borderColor: "#d95d39" },
        { label: "Necessidade info", data: trends.future.map((item) => item.needMoreInformation), borderColor: "#1f6f78" },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
  new Chart(document.querySelector("#profileChart"), {
    type: "doughnut",
    data: {
      labels: profiles.profiles.map((item) => item.name),
      datasets: [{ data: profiles.profiles.map((item) => item.count), backgroundColor: ["#2a9d8f", "#f2a65a", "#f2c94c", "#d95d39"] }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
  });
  document.querySelector("#aiAlerts").innerHTML = alerts.map((alert) => `<div class="alert alert-warning py-2"><strong>${alert.severity}</strong> ${alert.message}</div>`).join("") || "<p class='text-secondary'>Sem alertas críticos.</p>";

  // Exibe modelo usado
  if (aiStatusResponse) {
    const aiStatus = await aiStatusResponse.json();
    document.querySelector("#modelName").textContent = aiStatus.preferred_model || "desconhecido";
  }

  // Mostra estatísticas de sentimento
  if (sentimentStatsResponse) {
    const stat = await sentimentStatsResponse.json();
    const counts = stat.counts || { positive: 0, neutral: 0, negative: 0 };
    document.querySelector("#sentimentTotal").textContent = stat.total || 0;
    const ctx = document.querySelector("#sentimentChart");
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{ data: [counts.positive || 0, counts.neutral || 0, counts.negative || 0], backgroundColor: ["#2a9d8f", "#f2c94c", "#d95d39"] }],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadAiDashboard();
  document.querySelector("#mythForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const statement = new FormData(event.currentTarget).get("statement");
    const response = await apiFetch("/analytics/myth-detector", { method: "POST", body: JSON.stringify({ statement }) });
    if (!response) return;
    const result = await response.json();
    document.querySelector("#mythResult").innerHTML = `<div class="alert alert-info"><strong>${result.label}</strong> (${result.confidence}%)<br>${result.explanation}<br><small>Mais semelhante: ${result.match}</small></div>`;
  });
});
