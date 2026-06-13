const provincePoints = {
  Luanda: [-8.839, 13.289], Huambo: [-12.776, 15.739], Cabinda: [-5.56, 12.19],
  Namibe: [-15.196, 12.152], Benguela: [-12.576, 13.405], Huila: [-14.917, 13.492],
  Bie: [-12.383, 16.933], Malanje: [-9.54, 16.34], Uige: [-7.616, 15.05], Zaire: [-6.267, 14.24],
  "Cuanza Sul": [-10.8, 14.43], "Cuanza Norte": [-9.3, 14.91], Moxico: [-11.85, 19.91],
  "Lunda Sul": [-10.70, 20.39], "Lunda Norte": [-8.83, 20.74], Cunene: [-16.28, 16.16],
  Cuando: [-15.95, 19.17], Cubango: [-14.66, 17.68],
};

function riskColor(score) {
  if (score >= 70) return "#d95d39";
  if (score >= 45) return "#f2c94c";
  return "#2a9d8f";
}

async function loadHeatmap() {
  const response = await apiFetch("/analytics/regions");
  if (!response) return;
  const payload = await response.json();
  const map = L.map("map").setView([-11.2, 17.8], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 8, attribution: "&copy; OpenStreetMap" }).addTo(map);
  payload.byProvince.forEach((row) => {
    const point = provincePoints[row.name] || [-11.2, 17.8];
    L.circle(point, {
      radius: 25000 + row.averageScore * 1200,
      color: riskColor(row.averageScore),
      fillColor: riskColor(row.averageScore),
      fillOpacity: 0.45,
    }).addTo(map).bindPopup(`<strong>${row.name}</strong><br>Índice: ${row.averageScore}<br>Respostas: ${row.count}`);
  });
  document.querySelector("#heatmapRanking").innerHTML = payload.byProvince.map((row) => `
    <div class="ranking-row"><span>${row.name}</span><span class="risk-dot" style="background:${riskColor(row.averageScore)}"></span><strong>${row.averageScore}</strong></div>
  `).join("");
}

document.addEventListener("DOMContentLoaded", loadHeatmap);
