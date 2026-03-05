/* ═══════════════════════════════════════════════════════════
   SYGEPECO — FullCalendar Init
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
  const calEl = document.getElementById('calendar');
  if (!calEl || typeof FullCalendar === 'undefined') return;

  const calendar = new FullCalendar.Calendar(calEl, {
    initialView: 'dayGridMonth',
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
    events: '/api/calendrier-events/',
    eventDisplay: 'block',
    eventClick: function (info) {
      const ev = info.event;
      alert(`${ev.title}\nDu ${ev.startStr} au ${ev.endStr || ev.startStr}`);
    },
    dayMaxEvents: 3,
    moreLinkText: (n) => `+${n} autres`,
    noEventsText: 'Aucun événement ce mois.',
  });

  calendar.render();
});
