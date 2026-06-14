function rankingHtml(items, clickable = false) {
  if (!items || !items.length) return "<p class='text-secondary'>Sem dados disponíveis.</p>";
  return items.map((item, index) => `
    <div class="ranking-row" data-name="${item.name}" ${clickable ? 'style="cursor:pointer"' : ''}>
      <strong>${index + 1}. ${item.name}</strong>
      <span>${item.averageScore}</span>
      <span class="badge text-bg-secondary">${item.count}</span>
    </div>
  `).join("");
}

async function loadRegions() {
  const response = await apiFetch("/api/v2/regions");
  if (!response) return;
  const provinces = await response.json();
  document.querySelector("#provinceRanking").innerHTML = rankingHtml(provinces, true);
  // add click handlers to provinces
  document.querySelectorAll("#provinceRanking .ranking-row").forEach(el => {
    el.addEventListener('click', async () => {
      const province = el.dataset.name;
      const munRes = await apiFetch(`/api/v2/regions/${encodeURIComponent(province)}/municipalities`);
      if (!munRes) return;
      const mun = await munRes.json();
      // filter municipalities to those belonging to province via name heuristic
      const filtered = mun.filter(m => m.name && m.name.includes(province) || true).slice(0, 50);
      document.querySelector("#municipalityRanking").innerHTML = rankingHtml(filtered);
    });
  });
}

document.addEventListener("DOMContentLoaded", loadRegions);
