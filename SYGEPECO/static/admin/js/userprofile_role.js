/* ═══════════════════════════════════════════════════════════
   SYGEPECO — userprofile_role.js (Admin Django)
   Script charge dans l'interface d'administration Django
   pour le formulaire UserProfile.
   Comportement :
   - role = MANAGER   → affiche le champ "Direction" (departement)
   - role = ENTREPRISE → affiche le champ "Entreprise"
   - Autres roles      → masque les deux champs
   Evite les saisies incorrectes (ex: un DRH ne devrait pas
   avoir de direction liee).
   ═══════════════════════════════════════════════════════════ */
(function() {
  'use strict';

  function toggleFields() {
    var roleSelect = document.getElementById('id_role');
    if (!roleSelect) return;

    var role = roleSelect.value;

    // Ligne departement
    var deptRow = document.querySelector('.field-departement');
    // Ligne entreprise
    var entRow = document.querySelector('.field-entreprise');

    if (deptRow) {
      deptRow.style.display = (role === 'MANAGER') ? '' : 'none';
    }
    if (entRow) {
      entRow.style.display = (role === 'ENTREPRISE') ? '' : 'none';
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    toggleFields();
    var roleSelect = document.getElementById('id_role');
    if (roleSelect) {
      roleSelect.addEventListener('change', toggleFields);
    }
  });
})();
