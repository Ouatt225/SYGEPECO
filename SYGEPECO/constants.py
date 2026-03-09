"""
SYGEPECO — Constantes métier centralisées.
Toutes les valeurs magiques du domaine RH sont ici.
"""

# ─── Règles métier RH ──────────────────────────────────────────────
QUOTA_CONGE_ANNUEL       = 30   # Nombre de jours de congé annuels
PREVIS_MINIMUM_JOURS     = 7    # Délai de préavis minimum (jours)
CONGE_MATERNITE_MAX      = 180  # Durée maximale congé maternité (jours)
CONGE_PATERNITE_MAX      = 30   # Durée maximale congé paternité (jours)
PERMISSION_MAX_HEURES    = 3    # Durée maximale d'une permission (heures)
AGE_RETRAITE             = 60   # Âge légal de départ à la retraite

# ─── Rôles utilisateurs ────────────────────────────────────────────
ROLE_ADMINISTRATEUR = 'ADMINISTRATEUR'
ROLE_ENTREPRISE     = 'ENTREPRISE'
ROLE_MANAGER        = 'MANAGER'
ROLE_EMPLOYE        = 'EMPLOYE'
ROLE_DRH            = 'DRH'
ROLE_RH             = 'RH'

ROLES_ACCES_RH          = (ROLE_ADMINISTRATEUR, ROLE_DRH, ROLE_RH, ROLE_MANAGER)
ROLES_ACCES_ENTREPRISE  = (ROLE_ADMINISTRATEUR, ROLE_ENTREPRISE, ROLE_DRH)
ROLES_ACCES_MANAGER     = (ROLE_ADMINISTRATEUR, ROLE_MANAGER, ROLE_DRH)
ROLES_ACCES_ADMIN       = (ROLE_ADMINISTRATEUR, ROLE_DRH)

# ─── Statuts communs (congés / permissions) ────────────────────────
STATUT_EN_ATTENTE     = 'EN_ATTENTE'
STATUT_APPROUVE       = 'APPROUVE'
STATUT_REJETE         = 'REJETE'
STATUT_ANNULE         = 'ANNULE'
STATUT_VALIDE_MANAGER = 'VALIDE_MANAGER'

# ─── Statuts Contractuel ───────────────────────────────────────────
CONTRACTUEL_ACTIF    = 'ACTIF'
CONTRACTUEL_INACTIF  = 'INACTIF'
CONTRACTUEL_SUSPENDU = 'SUSPENDU'

# ─── Statuts Contrat ───────────────────────────────────────────────
CONTRAT_EN_COURS  = 'EN_COURS'
CONTRAT_EXPIRE    = 'EXPIRE'
CONTRAT_RESILIE   = 'RESILIE'
CONTRAT_RENOUVELE = 'RENOUVELE'

# ─── Statuts Présence ──────────────────────────────────────────────
PRESENCE_PRESENT    = 'PRESENT'
PRESENCE_ABSENT     = 'ABSENT'
PRESENCE_RETARD     = 'RETARD'
PRESENCE_CONGE      = 'CONGE'
PRESENCE_PERMISSION = 'PERMISSION'

# ─── Labels lisibles pour les exports ──────────────────────────────
STATUT_LABELS = {
    STATUT_EN_ATTENTE:     'En attente',
    STATUT_APPROUVE:       'Approuvé',
    STATUT_REJETE:         'Rejeté',
    STATUT_ANNULE:         'Annulé',
    STATUT_VALIDE_MANAGER: 'Validé Manager',
}

# ─── Couleurs Excel ────────────────────────────────────────────────
EXCEL_HEADER_BG      = '1A1A2E'
EXCEL_HEADER_FONT    = 'D4A853'
EXCEL_BORDER_COLOR   = '333344'
EXCEL_ROW_APPROUVE   = 'F0FFF4'
EXCEL_ROW_REJETE     = 'FFF0F0'
EXCEL_ROW_ATTENTE    = 'FFFBF0'
EXCEL_ROW_ALT_EVEN   = 'F8F9FF'
EXCEL_ROW_ALT_ODD    = 'FFFFFF'
