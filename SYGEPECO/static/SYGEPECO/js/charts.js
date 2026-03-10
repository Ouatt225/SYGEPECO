/* ═══════════════════════════════════════════════════════════
   SYGEPECO — charts.js
   Initialisation des graphiques Chart.js 4.x :
   - initPresenceChart : barres groupees (present/absent) sur 7 jours
     -> Donnees depuis /api/chart-presences/
   - initContratsChart : donut repartition types de contrats
     -> Donnees passees directement depuis le template
   - initDeptChart    : barres horizontales par direction
     -> Donnees passees directement depuis le template
   ═══════════════════════════════════════════════════════════ */

// Constantes de style partagees entre tous les graphiques (theme sombre SYGEPECO)
const CHART_DEFAULTS = {
  color: '#A0A0B0',
  fontFamily: "'Inter', 'Segoe UI', sans-serif",
  gridColor: 'rgba(255,255,255,0.04)',
  goldColor: '#D4A853',
  blueColor: '#4A6CF7',
  greenColor: '#22C55E',
  redColor: '#EF4444',
};

Chart.defaults.color = CHART_DEFAULTS.color;
Chart.defaults.font.family = CHART_DEFAULTS.fontFamily;
Chart.defaults.font.size = 12;

// ─── Graphique Présences (barres) ────────────────────────
function initPresenceChart(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  fetch('/api/chart-presences/')
    .then(r => r.json())
    .then(data => {
      new Chart(canvas, {
        type: 'bar',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Présents',
              data: data.presents,
              backgroundColor: 'rgba(34, 197, 94, 0.7)',
              borderColor: '#22C55E',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
            },
            {
              label: 'Absents',
              data: data.absents,
              backgroundColor: 'rgba(239, 68, 68, 0.7)',
              borderColor: '#EF4444',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false }, // Tooltip groupee : affiche toutes les series a x
          plugins: {
            legend: {
              labels: { color: '#A0A0B0', boxWidth: 12, borderRadius: 3 },
            },
            tooltip: {
              backgroundColor: '#1E1E2A',
              borderColor: 'rgba(255,255,255,0.08)',
              borderWidth: 1,
              titleColor: '#F1F1F5',
              bodyColor: '#A0A0B0',
              padding: 12,
              cornerRadius: 8,
            },
          },
          scales: {
            x: {
              grid: { color: CHART_DEFAULTS.gridColor },
              ticks: { color: '#6B7280' },
            },
            y: {
              grid: { color: CHART_DEFAULTS.gridColor },
              ticks: { color: '#6B7280', stepSize: 1 },
              beginAtZero: true,
            },
          },
        },
      });
    })
    .catch(console.error); // Erreur reseau ou API : logge en console
}

// ─── Graphique Contrats (donut) ──────────────────────────
function initContratsChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data) return;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.values,
        backgroundColor: [
          'rgba(212, 168, 83, 0.8)',
          'rgba(74, 108, 247, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(168, 85, 247, 0.8)',
        ],
        borderColor: '#16161F',
        borderWidth: 3,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%', // Epaisseur de l'anneau du donut (70% = anneau fin)
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#A0A0B0',
            padding: 16,
            boxWidth: 12,
            borderRadius: 3,
            usePointStyle: true,
          },
        },
        tooltip: {
          backgroundColor: '#1E1E2A',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          titleColor: '#F1F1F5',
          bodyColor: '#A0A0B0',
          padding: 12,
          cornerRadius: 8,
        },
      },
    },
  });
}

// ─── Graphique Répartition département (horizontal bar) ──
function initDeptChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data) return;

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Contractuels',
        data: data.values,
        backgroundColor: 'rgba(212, 168, 83, 0.6)',
        borderColor: '#D4A853',
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y', // Barres horizontales (l'axe des categories est vertical)
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1E1E2A',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          titleColor: '#F1F1F5',
          bodyColor: '#A0A0B0',
          padding: 12,
          cornerRadius: 8,
        },
      },
      scales: {
        x: {
          grid: { color: CHART_DEFAULTS.gridColor },
          ticks: { color: '#6B7280', stepSize: 1 },
          beginAtZero: true,
        },
        y: {
          grid: { display: false },
          ticks: { color: '#A0A0B0' },
        },
      },
    },
  });
}

// Init automatique
document.addEventListener('DOMContentLoaded', () => {
  initPresenceChart('chartPresences');
});
