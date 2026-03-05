/* ═══════════════════════════════════════════════════════════
   SYGEPECO — Main JS
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ─── Sidebar Toggle ──────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const navbar  = document.getElementById('navbar');
  const mainContent = document.getElementById('mainContent');
  const btnToggle = document.getElementById('btnSidebarToggle');

  const SIDEBAR_KEY = 'sygepeco_sidebar_collapsed';
  let collapsed = localStorage.getItem(SIDEBAR_KEY) === 'true';

  function applySidebarState() {
    if (collapsed) {
      sidebar?.classList.add('collapsed');
      navbar?.classList.add('sidebar-collapsed');
      mainContent?.classList.add('sidebar-collapsed');
    } else {
      sidebar?.classList.remove('collapsed');
      navbar?.classList.remove('sidebar-collapsed');
      mainContent?.classList.remove('sidebar-collapsed');
    }
  }

  applySidebarState();

  btnToggle?.addEventListener('click', () => {
    collapsed = !collapsed;
    localStorage.setItem(SIDEBAR_KEY, collapsed);
    applySidebarState();
  });

  // ─── Auto-dismiss alerts ─────────────────────────────────
  const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(20px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(() => alert.remove(), 300);
    }, 4000);
  });

  // ─── Close alert on click ────────────────────────────────
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 200);
    });
  });

  // ─── Date dynamique navbar ───────────────────────────────
  const dateEl = document.getElementById('navbarDate');
  if (dateEl) {
    const now = new Date();
    const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateEl.textContent = now.toLocaleDateString('fr-FR', opts);
  }

  // ─── Active nav item ─────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && currentPath === '/') {
      link.classList.add('active');
    }
  });

  // ─── Confirmation suppression ────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm || 'Confirmer cette action ?')) {
        e.preventDefault();
      }
    });
  });

  // ─── Preview photo upload ────────────────────────────────
  const photoInput = document.getElementById('photoInput');
  const photoPreview = document.getElementById('photoPreview');
  if (photoInput && photoPreview) {
    photoInput.addEventListener('change', () => {
      const file = photoInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => { photoPreview.src = e.target.result; };
        reader.readAsDataURL(file);
      }
    });
  }

});
