function rankingHtml(items) {
  if (!items.length) return "<p class='text-secondary'>Sem dados disponíveis.</p>";
  return items.map((item, index) => `
    <div class="ranking-row">
      <strong>${index + 1}. ${item.name}</strong>
      <span>${item.averageScore}</span>
      <span class="badge text-bg-secondary">${item.count}</span>
    </div>
  `).join("");
}

async function loadRegions() {
  const response = await apiFetch("/analytics/regions");
  if (!response) return;
  const payload = await response.json();
  document.querySelector("#provinceRanking").innerHTML = rankingHtml(payload.byProvince);
  document.querySelector("#municipalityRanking").innerHTML = rankingHtml(payload.byMunicipality);
}

document.addEventListener("DOMContentLoaded", loadRegions);
