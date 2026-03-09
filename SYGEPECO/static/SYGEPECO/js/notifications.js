/* SYGEPECO — Notifications congés approchants */
(function () {
  'use strict';

  var STORAGE_KEY = 'syg_notifs_v1';

  /* ── Sons ────────────────────────────────────────────────────── */
  function playSound(urgent) {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var notes = urgent ? [523, 784, 1047] : [523, 659];
      var t = ctx.currentTime + 0.05;
      notes.forEach(function (freq) {
        var osc  = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.value = freq;
        osc.connect(gain);
        gain.connect(ctx.destination);
        gain.gain.setValueAtTime(0.22, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.28);
        osc.start(t);
        osc.stop(t + 0.28);
        t += 0.22;
      });
    } catch (e) { /* Web Audio non supporté */ }
  }

  /* ── Conteneur de toasts ──────────────────────────────────────── */
  function getContainer() {
    var el = document.getElementById('syg-notif-container');
    if (!el) {
      el = document.createElement('div');
      el.id = 'syg-notif-container';
      el.style.cssText = [
        'position:fixed', 'top:20px', 'right:20px', 'z-index:99999',
        'display:flex', 'flex-direction:column', 'gap:10px',
        'max-width:380px', 'pointer-events:none',
      ].join(';');
      document.body.appendChild(el);
    }
    return el;
  }

  /* ── Un toast ─────────────────────────────────────────────────── */
  function showToast(notif) {
    var urgent = notif.days_until <= 1;
    var color  = urgent ? '#F43F5E' : '#F59E0B';
    var label  = urgent ? 'Congé DEMAIN' : 'Congé dans 7 jours';
    var icon   = urgent
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>';

    var toast = document.createElement('div');
    toast.style.cssText = [
      'display:flex', 'align-items:flex-start', 'gap:12px',
      'background:#1A1F2E', 'border:1px solid rgba(255,255,255,.08)',
      'border-left:4px solid ' + color,
      'border-radius:12px', 'padding:14px 16px',
      'color:#EEF0F8', 'font-family:inherit',
      'box-shadow:0 12px 40px rgba(0,0,0,.6)',
      'pointer-events:all',
      'animation:sygToastIn .35s cubic-bezier(.21,1.02,.73,1) both',
    ].join(';');

    toast.innerHTML =
      '<div style="color:' + color + ';flex-shrink:0;margin-top:1px;">' + icon + '</div>' +
      '<div style="flex:1;min-width:0;">' +
        '<div style="font-weight:700;font-size:.82rem;letter-spacing:.03em;color:' + color + ';margin-bottom:4px;">' + label + '</div>' +
        '<div style="font-size:.80rem;font-weight:600;color:#EEF0F8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + notif.agent + '</div>' +
        '<div style="font-size:.73rem;color:#8B8FA8;margin-top:2px;">' + notif.type_conge + ' — début le ' + notif.date_debut + '</div>' +
      '</div>' +
      '<button style="background:none;border:none;cursor:pointer;color:#52566E;font-size:1rem;padding:0 0 0 6px;flex-shrink:0;line-height:1;" onclick="this.closest(\'div\').remove()">✕</button>';

    getContainer().appendChild(toast);
    setTimeout(function () {
      toast.style.animation = 'sygToastOut .3s ease forwards';
      setTimeout(function () { toast.remove(); }, 300);
    }, 9000);
  }

  /* ── Keyframes (injectés une seule fois) ───────────────────────── */
  function injectStyles() {
    if (document.getElementById('syg-notif-styles')) return;
    var style = document.createElement('style');
    style.id = 'syg-notif-styles';
    style.textContent =
      '@keyframes sygToastIn{from{transform:translateX(110%);opacity:0}to{transform:translateX(0);opacity:1}}' +
      '@keyframes sygToastOut{from{opacity:1;transform:translateX(0)}to{opacity:0;transform:translateX(110%)}}';
    document.head.appendChild(style);
  }

  /* ── Mémoire session ───────────────────────────────────────────── */
  function getSeenKeys() {
    try { return new Set(JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]')); }
    catch (e) { return new Set(); }
  }
  function saveSeenKeys(set) {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(set))); } catch (e) {}
  }

  /* ── Fetch & affichage ─────────────────────────────────────────── */
  function checkNotifications() {
    fetch('/api/conges/notifs/', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.notifications) return;
        var seen = getSeenKeys();
        var fresh = data.notifications.filter(function (n) { return !seen.has(n.key); });
        if (!fresh.length) return;

        injectStyles();
        var hasUrgent = fresh.some(function (n) { return n.days_until <= 1; });
        playSound(hasUrgent);

        fresh.forEach(function (n) {
          showToast(n);
          seen.add(n.key);
        });
        saveSeenKeys(seen);
      })
      .catch(function () {});
  }

  /* ── Démarrage ─────────────────────────────────────────────────── */
  function init() {
    setTimeout(checkNotifications, 1800);         // 1er check après chargement
    setInterval(checkNotifications, 5 * 60 * 1000); // re-check toutes les 5 min
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
