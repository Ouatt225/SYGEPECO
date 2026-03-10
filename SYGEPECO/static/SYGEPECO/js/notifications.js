/* SYGEPECO — Notifications congés approchants */
(function () {
  'use strict';

  var STORAGE_KEY = 'syg_notifs_v1'; // Cle sessionStorage — changer la version si le format change
  var _audioCtx   = null;   // contexte partagé (créé une seule fois)
  var _userReady  = false;  // true dès qu'une interaction a eu lieu

  /* ── Contexte audio partagé ───────────────────────────────────── */
  function getCtx() {
    if (!_audioCtx) {
      try {
        _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      } catch (e) { return null; }
    }
    return _audioCtx;
  }

  /* Déverrouiller le contexte dès la première interaction */
  function unlockAudio() {
    if (_userReady) return;
    _userReady = true;
    var ctx = getCtx();
    if (ctx && ctx.state === 'suspended') {
      ctx.resume().catch(function () {});
    }
  }
  ['click', 'keydown', 'touchstart', 'scroll'].forEach(function (ev) {
    document.addEventListener(ev, unlockAudio, { once: false, passive: true });
  });

  /* ── Sons ────────────────────────────────────────────────────── */
  function playSound(urgent) {
    var ctx = getCtx();
    if (!ctx) return;

    /* Resume si suspendu (premier chargement sans interaction) puis joue */
    var doPlay = function () {
      var notes = urgent ? [523, 659, 784, 1047] : [523, 659];
      var t = ctx.currentTime + 0.04;
      notes.forEach(function (freq) {
        try {
          var osc  = ctx.createOscillator();
          var gain = ctx.createGain();
          osc.type = 'sine';
          osc.frequency.value = freq;
          osc.connect(gain);
          gain.connect(ctx.destination);
          gain.gain.setValueAtTime(0.28, t);  // Volume initial : 0.28 (modere)
          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.32); // Fondu exponentiel vers 0 en 0.32s (anti-clic)
          osc.start(t);
          osc.stop(t + 0.32);
          t += 0.26; // Espacement entre les notes : 260ms
        } catch (e) {}
      });
    };

    if (ctx.state === 'suspended') {
      ctx.resume().then(doPlay).catch(function () {});
    } else {
      doPlay();
    }
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
    var label  = urgent ? 'Congé DEMAIN !' : 'Congé dans 7 jours';
    var icon   = urgent
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>';

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
      '<button style="background:none;border:none;cursor:pointer;color:#52566E;font-size:1rem;padding:0 0 0 6px;flex-shrink:0;line-height:1;" onclick="this.closest(\'[id]\').remove ? this.parentElement.parentElement.remove() : this.parentElement.remove()">✕</button>';

    getContainer().appendChild(toast);
    setTimeout(function () {
      toast.style.animation = 'sygToastOut .3s ease forwards';
      setTimeout(function () { if (toast.parentNode) toast.remove(); }, 300);
    }, 10000);
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
        var seen  = getSeenKeys();
        var fresh = data.notifications.filter(function (n) { return !seen.has(n.key); });
        if (!fresh.length) return;

        injectStyles();
        var hasUrgent = fresh.some(function (n) { return n.days_until <= 1; });

        /* Afficher les toasts d'abord (interaction visuelle), puis le son */
        fresh.forEach(function (n) {
          showToast(n);
          seen.add(n.key);
        });
        saveSeenKeys(seen);

        /* Jouer le son (résumé automatique si contexte suspendu) */
        playSound(hasUrgent);
      })
      .catch(function () {});
  }

  /* ── Démarrage ─────────────────────────────────────────────────── */
  function init() {
    /* Pré-créer le contexte pour qu'il soit prêt */
    getCtx();
    setTimeout(checkNotifications, 2000);   // Delai initial 2s (laisser la page charger)
    setInterval(checkNotifications, 5 * 60 * 1000); // Verif toutes les 5 min
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
