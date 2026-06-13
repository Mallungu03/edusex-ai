function chartData(map) {
  return { labels: Object.keys(map), values: Object.values(map) };
}

function createChart(id, type, title, map) {
  const data = chartData(map);
  return new Chart(document.getElementById(id), {
    type,
    data: {
      labels: data.labels,
      datasets: [{
        label: title,
        data: data.values,
        backgroundColor: ["#1f6f78", "#f2a65a", "#7fb069", "#d95d39", "#6c757d", "#2a9d8f", "#8d6e63"],
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { title: { display: true, text: title }, legend: { position: "bottom" } },
    },
  });
}

async function loadDashboard() {
  const [response, insightsResponse, trendsResponse] = await Promise.all([
    apiFetch("/analytics/dashboard"),
    apiFetch("/analytics/insights"),
    apiFetch("/analytics/trends"),
  ]);
  if (!response || !insightsResponse || !trendsResponse) return;
  const payload = await response.json();
  const insights = await insightsResponse.json();
  const trends = await trendsResponse.json();
  const indicators = payload.indicators;
  const cards = [
    ["Sex Education Awareness Score", `${insights.awarenessScore}/100`],
    ["Participantes", indicators.totalParticipants],
    ["Média de idade", indicators.averageAge],
    ["Recebeu educação sexual", `${indicators.receivedSexEducation}%`],
    ["Deseja mais informação", `${indicators.needMoreInformation}%`],
    ["Sente vergonha", `${indicators.feelsEmbarrassed}%`],
    ["Sofreu pressão social", `${indicators.pressuredToHaveSex}%`],
    ["Usa contraceptivos", `${indicators.contraceptiveUse}%`],
  ];
  document.querySelector("#indicatorCards").innerHTML = cards.map(([label, value]) => `
    <div class="col-6 col-md-4 col-xl-2">
      <div class="panel metric">
        <div class="metric-value">${value}</div>
        <div class="metric-label">${label}</div>
      </div>
    </div>
  `).join("");

  createChart("genderChart", "pie", "Distribuição por sexo", payload.charts.gender);
  createChart("riskChart", "doughnut", "Risco de desinformação", payload.charts.risk);
  createChart("monthlyChart", "line", "Respostas por mês", payload.charts.monthly);
  createChart("provinceChart", "bar", "Top províncias", payload.charts.province);
  createChart("sourceChart", "bar", "Fontes de informação", payload.charts.source);
  document.querySelector("#dashboardInsights").innerHTML = insights.topInsights.map((item) => `<div class="ranking-row"><span>${item}</span></div>`).join("");
  new Chart(document.querySelector("#futureChart"), {
    type: "line",
    data: {
      labels: trends.future.map((item) => item.period),
      datasets: [
        { label: "Índice de desinformação", data: trends.future.map((item) => item.misinformationIndex), borderColor: "#d95d39" },
        { label: "Necessidade de informação", data: trends.future.map((item) => item.needMoreInformation), borderColor: "#1f6f78" },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
  });
}

document.addEventListener("DOMContentLoaded", loadDashboard);
