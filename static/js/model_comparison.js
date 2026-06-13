async function loadModelComparison() {
  const [comparisonResponse, clusterResponse] = await Promise.all([
    apiFetch("/analytics/model-comparison"),
    apiFetch("/analytics/hierarchical-clusters"),
  ]);
  if (!comparisonResponse || !clusterResponse) return;
  const comparison = await comparisonResponse.json();
  const clusters = await clusterResponse.json();
  const labels = comparison.metrics.map((item) => item.model);
  new Chart(document.querySelector("#modelChart"), {
    type: "bar",
    data: {
      labels,
      datasets: ["accuracy", "precision", "recall", "f1"].map((metric, index) => ({
        label: metric,
        data: comparison.metrics.map((item) => item[metric]),
        backgroundColor: ["#1f6f78", "#f2a65a", "#7fb069", "#d95d39"][index],
      })),
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } }, scales: { y: { max: 1 } } },
  });
  document.querySelector("#bestModel").innerHTML = `<div class="metric-value">${comparison.bestModel}</div><p class="text-secondary">Selecionado automaticamente pelo maior F1 Score ponderado.</p>`;
  document.querySelector("#hierarchicalClusters").innerHTML = clusters.groups.map((group) => `
    <div class="ranking-row"><span>${group.name}</span><strong>${group.count}</strong><span>participantes</span></div>
  `).join("");
}

document.addEventListener("DOMContentLoaded", loadModelComparison);
