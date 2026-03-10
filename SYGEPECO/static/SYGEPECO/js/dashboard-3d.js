/* ═══════════════════════════════════════════════════════════
   SYGEPECO — dashboard-3d.js
   Effets visuels du tableau de bord :
   1. Tilt 3D au survol des cartes stats (mousemove → transform)
   2. Compteurs animes de 0 → valeur cible (IntersectionObserver)
   3. Particules flottantes en canvas (arriere-plan subtil)
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ─── 3D Tilt Effect ──────────────────────────────────────
  const tiltCards = document.querySelectorAll('.stat-card');

  tiltCards.forEach(card => {
    card.addEventListener('mousemove', handleTilt);
    card.addEventListener('mouseleave', resetTilt);
  });

  function handleTilt(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    // Centre de la carte en coordonnees ecran
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    // Deplacement normalise : -1 (bord gauche/haut) → +1 (bord droit/bas)
    const dx = (e.clientX - cx) / (rect.width / 2);
    const dy = (e.clientY - cy) / (rect.height / 2);

    const maxAngle = 8; // Angle max de rotation en degres (8 = subtil, non distordant)
    const rotX = -dy * maxAngle; // Inclinaison verticale (haut/bas) inversee
    const rotY = dx * maxAngle;  // Inclinaison horizontale (gauche/droite)

    card.style.transform = `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateZ(8px)`;
  }

  function resetTilt(e) {
    const card = e.currentTarget;
    card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
  }

  // ─── Animated Counters ───────────────────────────────────
  function animateCounter(el, target, duration = 1500) {
    const start = performance.now();
    const startVal = 0;

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Easing ease-out cubique : ralentit progressivement (1 - (1-t)^3)
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startVal + (target - startVal) * eased);
      el.textContent = current.toLocaleString('fr-FR');
      if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  // Observer pour déclencher quand visible
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target || el.textContent, 10);
        if (!isNaN(target)) {
          animateCounter(el, target);
        }
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.3 }); // Declenche quand 30% de l'element est visible

  document.querySelectorAll('.counter-value').forEach(el => {
    const val = parseInt(el.textContent, 10);
    if (!isNaN(val)) {
      el.dataset.target = val;
      el.textContent = '0';
      observer.observe(el);
    }
  });

  // ─── Floating particles background ───────────────────────
  const canvas = document.getElementById('bgCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;

  // 35 particules dorees semi-transparentes en mouvement brownien
  const particles = Array.from({ length: 35 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 1.5 + 0.5,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    alpha: Math.random() * 0.3 + 0.05,
  }));

  function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(212, 168, 83, ${p.alpha})`; // Couleur or SYGEPECO
      ctx.fill();

      p.x += p.vx;
      p.y += p.vy;

      // Rebond sur les bords du canvas (inversion de velocity)
      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    });
    requestAnimationFrame(drawParticles);
  }

  drawParticles();

  window.addEventListener('resize', () => {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  });

});
