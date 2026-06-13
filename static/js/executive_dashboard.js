function rows(items) {
  return items.map((item, index) => `
    <div class="ranking-row">
      <span>${index + 1}. ${item.name || item.title || item}</span>
      <strong>${item.averageScore || item.demand || ""}</strong>
      <span>${item.count || ""}</span>
    </div>
  `).join("");
}

async function loadExecutive() {
  const [insightsResponse, regionsResponse, alertsResponse, reportResponse] = await Promise.all([
    apiFetch("/analytics/insights"),
    apiFetch("/analytics/regions"),
    apiFetch("/analytics/alerts"),
    apiFetch("/analytics/report-text"),
  ]);
  if (!insightsResponse || !regionsResponse || !alertsResponse || !reportResponse) return;
  const insights = await insightsResponse.json();
  const regions = await regionsResponse.json();
  const alerts = await alertsResponse.json();
  const report = await reportResponse.json();

  document.querySelector("#executiveCards").innerHTML = [
    ["Awareness Score", `${insights.awarenessScore}/100`, "bi-speedometer2"],
    ["Insights", insights.topInsights.length, "bi-bar-chart"],
    ["Alertas", alerts.length, "bi-exclamation-triangle"],
    ["Regiões", regions.byProvince.length, "bi-geo-alt"],
  ].map(([label, value, icon]) => `
    <div class="col-6 col-lg-3"><div class="panel metric animated-card"><i class="bi ${icon}"></i><div class="metric-value">${value}</div><div class="metric-label">${label}</div></div></div>
  `).join("");
  document.querySelector("#priorityRegions").innerHTML = rows(regions.byProvince.slice(0, 10));
  document.querySelector("#alertCenter").innerHTML = alerts.map((alert) => `<div class="alert alert-warning"><strong>${alert.type}</strong><br>${alert.message}</div>`).join("") || "<p class='text-secondary'>Sem alertas críticos.</p>";
  document.querySelector("#topProblems").innerHTML = insights.problems.map((item) => `<li>${item}</li>`).join("");
  document.querySelector("#topRecommendations").innerHTML = rows(insights.topRecommendations);
  document.querySelector("#reportText").textContent = report.report;
}

document.addEventListener("DOMContentLoaded", () => {
  loadExecutive();
  document.querySelector("#generateReport").addEventListener("click", loadExecutive);
});
