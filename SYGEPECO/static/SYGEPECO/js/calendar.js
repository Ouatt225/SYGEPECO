/* ═══════════════════════════════════════════════════════════
   SYGEPECO — calendar.js
   Initialise FullCalendar 6.x sur l'element #calendar.
   Les evenements sont charges dynamiquement depuis l'API Django
   /api/calendrier-events/ (conges + permissions APPROUVES).
   Vues disponibles : mois, semaine, liste.
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
  const calEl = document.getElementById('calendar');
  // Sortie preventive si l'element ou la librairie FullCalendar est absent
  if (!calEl || typeof FullCalendar === 'undefined') return;

  const calendar = new FullCalendar.Calendar(calEl, {
    initialView: 'dayGridMonth', // Vue par defaut : calendrier mensuel en grille
    locale: 'fr',
    height: 'auto',
    headerToolbar: {
      left:   'prev,next today',
      center: 'title',
      right:  'dayGridMonth,timeGridWeek,listWeek',
    },
    buttonText: {
      today:    "Aujourd'hui",
      month:    'Mois',
      week:     'Semaine',
      list:     'Liste',
    },
    events: '/api/calendrier-events/', // URL Django retournant les evenements JSON
    eventDisplay: 'block', // Affichage plein (fond colore) plutot que point
    eventClick: function (info) {
      const ev = info.event;
      alert(`${ev.title}\nDu ${ev.startStr} au ${ev.endStr || ev.startStr}`);
    },
    dayMaxEvents: 3, // Max 3 evenements par case, le reste affiche "+N autres"
    moreLinkText: (n) => `+${n} autres`,
    noEventsText: 'Aucun événement ce mois.',
  });

  calendar.render();
});
