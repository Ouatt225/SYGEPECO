"""
Tests unitaires — EspaceCongeForm (règles métier)
==================================================
Couverture des 7 règles de EspaceCongeForm.clean() :
  R1  — Cohérence des dates (fin >= début)
  R2  — Justificatif médical obligatoire pour congé maladie
  R3  — Préavis minimum de 7 jours
  R4  — Congé maternité ≤ 180 jours
  R5  — Congé paternité ≤ 30 jours
  R6  — Quota annuel congé (QUOTA_CONGE_ANNUEL = 30 j)
  R7  — Chevauchement de dates avec un congé existant
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .constants import (
    CONGE_MATERNITE_MAX,
    CONGE_PATERNITE_MAX,
    PREVIS_MINIMUM_JOURS,
    QUOTA_CONGE_ANNUEL,
)
from .forms import EspaceCongeForm
from .models import Conge, Contractuel, Direction, Poste


# ─── Helpers ────────────────────────────────────────────────────────────────

def _d(offset: int) -> date:
    """Retourne la date d'aujourd'hui + offset jours."""
    return date.today() + timedelta(days=offset)


def _fake_pdf() -> SimpleUploadedFile:
    return SimpleUploadedFile("arret.pdf", b"%PDF-stub", content_type="application/pdf")


class EspaceCongeFormTestCase(TestCase):
    """Jeu de données partagé entre tous les tests (jamais modifié)."""

    @classmethod
    def setUpTestData(cls):
        cls.direction = Direction.objects.create(nom="DRH Test")
        cls.poste = Poste.objects.create(titre="Développeur", direction=cls.direction)
        cls.user = User.objects.create_user(
            username="test_agent", password="pass1234"
        )
        cls.contractuel = Contractuel.objects.create(
            user=cls.user,
            matricule="TST-001",
            nom="Doe",
            prenom="John",
            genre="M",
            date_naissance=date(1990, 1, 15),
            email="john.doe@test.ci",
            telephone="0102030405",
            date_embauche=date(2020, 1, 1),
            poste=cls.poste,
            direction=cls.direction,
        )

    # ── Fabrique de formulaire ────────────────────────────────────────────

    def _form(self, data: dict, files: dict | None = None) -> EspaceCongeForm:
        return EspaceCongeForm(
            data=data,
            files=files or {},
            contractuel=self.contractuel,
        )

    def _data(self, **overrides) -> dict:
        """Données valides par défaut (ANNUEL, 10 jours, préavis OK)."""
        defaults = {
            "type_conge": "ANNUEL",
            "date_debut": _d(PREVIS_MINIMUM_JOURS + 1),
            "date_fin":   _d(PREVIS_MINIMUM_JOURS + 10),
            "motif":      "Vacances",
        }
        defaults.update(overrides)
        # Sérialiser les dates en string ISO pour le formulaire
        for k in ("date_debut", "date_fin"):
            if isinstance(defaults.get(k), date):
                defaults[k] = defaults[k].isoformat()
        return defaults

    # ════════════════════════════════════════════════════════════════════════
    # R1 — Cohérence des dates
    # ════════════════════════════════════════════════════════════════════════

    def test_r1_dates_coherentes_valide(self):
        """date_fin == date_debut est accepté (congé d'1 jour)."""
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        form = self._form(self._data(date_debut=debut, date_fin=debut))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r1_date_fin_avant_debut_invalide(self):
        debut = _d(PREVIS_MINIMUM_JOURS + 5)
        fin   = _d(PREVIS_MINIMUM_JOURS + 2)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("postérieure", str(form.errors))

    # ════════════════════════════════════════════════════════════════════════
    # R2 — Justificatif médical obligatoire (congé maladie)
    # ════════════════════════════════════════════════════════════════════════

    def test_r2_maladie_sans_justificatif_invalide(self):
        form = self._form(self._data(type_conge="MALADIE"))
        self.assertFalse(form.is_valid())
        self.assertIn("justificatif", str(form.errors).lower())

    def test_r2_maladie_avec_justificatif_valide(self):
        form = self._form(
            self._data(type_conge="MALADIE"),
            files={"document_medical": _fake_pdf()},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_r2_annuel_sans_justificatif_valide(self):
        """Le justificatif est uniquement requis pour MALADIE."""
        form = self._form(self._data(type_conge="ANNUEL"))
        self.assertTrue(form.is_valid(), form.errors)

    # ════════════════════════════════════════════════════════════════════════
    # R3 — Préavis minimum (PREVIS_MINIMUM_JOURS)
    # ════════════════════════════════════════════════════════════════════════

    def test_r3_preavis_exact_valide(self):
        """date_debut = aujourd'hui + PREVIS_MINIMUM_JOURS (7 j) est acceptée car la condition est delai < 7 (strict)."""
        debut = _d(PREVIS_MINIMUM_JOURS)
        form = self._form(self._data(date_debut=debut, date_fin=_d(PREVIS_MINIMUM_JOURS + 5)))
        self.assertTrue(form.is_valid(), form.errors)  # delai == 7 → 7 < 7 est faux → valide

    def test_r3_preavis_suffisant_valide(self):
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        form = self._form(self._data(date_debut=debut, date_fin=_d(PREVIS_MINIMUM_JOURS + 5)))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r3_preavis_insuffisant_invalide(self):
        debut = _d(3)  # seulement 3 jours de préavis
        form = self._form(self._data(date_debut=debut, date_fin=_d(10)))
        self.assertFalse(form.is_valid())
        self.assertIn("préavis", str(form.errors).lower())

    def test_r3_date_passee_invalide(self):
        debut = _d(-1)
        form = self._form(self._data(date_debut=debut, date_fin=_d(5)))
        self.assertFalse(form.is_valid())
        self.assertIn("préavis", str(form.errors).lower())

    # ════════════════════════════════════════════════════════════════════════
    # R4 — Congé maternité ≤ CONGE_MATERNITE_MAX jours
    # ════════════════════════════════════════════════════════════════════════

    def test_r4_maternite_limite_exacte_valide(self):
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=CONGE_MATERNITE_MAX - 1)
        form = self._form(self._data(type_conge="MATERNITE", date_debut=debut, date_fin=fin))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r4_maternite_depasse_limite_invalide(self):
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=CONGE_MATERNITE_MAX)  # +1 jour au-delà
        form = self._form(self._data(type_conge="MATERNITE", date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("180", str(form.errors))

    # ════════════════════════════════════════════════════════════════════════
    # R5 — Congé paternité ≤ CONGE_PATERNITE_MAX jours
    # ════════════════════════════════════════════════════════════════════════

    def test_r5_paternite_limite_exacte_valide(self):
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=CONGE_PATERNITE_MAX - 1)
        form = self._form(self._data(type_conge="PATERNITE", date_debut=debut, date_fin=fin))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r5_paternite_depasse_limite_invalide(self):
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=CONGE_PATERNITE_MAX)
        form = self._form(self._data(type_conge="PATERNITE", date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("30", str(form.errors))

    # ════════════════════════════════════════════════════════════════════════
    # R6 — Quota annuel (QUOTA_CONGE_ANNUEL)
    # ════════════════════════════════════════════════════════════════════════

    def _create_conge(self, debut: date, fin: date, statut: str = "APPROUVE") -> Conge:
        return Conge.objects.create(
            contractuel=self.contractuel,
            type_conge="ANNUEL",
            date_debut=debut,
            date_fin=fin,
            motif="Test quota",
            statut=statut,
        )

    def test_r6_quota_non_atteint_valide(self):
        """10 jours déjà pris + 10 demandés = 20 ≤ 30 → valide."""
        debut_pris = _d(PREVIS_MINIMUM_JOURS + 100)
        self._create_conge(debut_pris, debut_pris + timedelta(days=9))
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=9)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r6_quota_plein_invalide(self):
        """30 jours déjà pris → quota épuisé."""
        debut_pris = _d(PREVIS_MINIMUM_JOURS + 100)
        self._create_conge(debut_pris, debut_pris + timedelta(days=QUOTA_CONGE_ANNUEL - 1))
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=4)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("épuisé", str(form.errors).lower())

    def test_r6_quota_partiel_invalide(self):
        """20 jours pris + 15 demandés = 35 > 30 → dépassement partiel."""
        debut_pris = _d(PREVIS_MINIMUM_JOURS + 100)
        self._create_conge(debut_pris, debut_pris + timedelta(days=19))
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=14)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("quota", str(form.errors).lower())

    def test_r6_en_attente_compte_dans_quota(self):
        """Les congés EN_ATTENTE consomment aussi le quota."""
        debut_pris = _d(PREVIS_MINIMUM_JOURS + 100)
        self._create_conge(debut_pris, debut_pris + timedelta(days=QUOTA_CONGE_ANNUEL - 1), statut="EN_ATTENTE")
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=2)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())

    def test_r6_rejete_ne_compte_pas_dans_quota(self):
        """Les congés REJETE ne doivent PAS être décomptés du quota."""
        debut_pris = _d(PREVIS_MINIMUM_JOURS + 100)
        self._create_conge(debut_pris, debut_pris + timedelta(days=QUOTA_CONGE_ANNUEL - 1), statut="REJETE")
        debut = _d(PREVIS_MINIMUM_JOURS + 1)
        fin   = debut + timedelta(days=9)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertTrue(form.is_valid(), form.errors)

    # ════════════════════════════════════════════════════════════════════════
    # R7 — Chevauchement de dates
    # ════════════════════════════════════════════════════════════════════════

    def _create_conge_approuve(self, debut: date, fin: date) -> Conge:
        return Conge.objects.create(
            contractuel=self.contractuel,
            type_conge="ANNUEL",
            date_debut=debut,
            date_fin=fin,
            motif="Congé existant",
            statut="APPROUVE",
        )

    def test_r7_chevauchement_total_invalide(self):
        """Nouvelle demande entièrement incluse dans un congé existant."""
        existing_start = _d(PREVIS_MINIMUM_JOURS + 50)
        self._create_conge_approuve(existing_start, existing_start + timedelta(days=20))
        debut = existing_start + timedelta(days=2)
        fin   = existing_start + timedelta(days=8)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("chevauche", str(form.errors).lower())

    def test_r7_chevauchement_partiel_debut_invalide(self):
        """Nouvelle demande commence avant et finit pendant un congé existant."""
        existing_start = _d(PREVIS_MINIMUM_JOURS + 50)
        self._create_conge_approuve(existing_start, existing_start + timedelta(days=10))
        debut = existing_start - timedelta(days=3)
        fin   = existing_start + timedelta(days=5)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("chevauche", str(form.errors).lower())

    def test_r7_chevauchement_partiel_fin_invalide(self):
        """Nouvelle demande commence pendant et finit après un congé existant."""
        existing_start = _d(PREVIS_MINIMUM_JOURS + 50)
        self._create_conge_approuve(existing_start, existing_start + timedelta(days=10))
        debut = existing_start + timedelta(days=5)
        fin   = existing_start + timedelta(days=15)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("chevauche", str(form.errors).lower())

    def test_r7_consecutif_sans_chevauchement_valide(self):
        """Nouvelle demande démarre le lendemain exact d'un congé existant → valide."""
        existing_start = _d(PREVIS_MINIMUM_JOURS + 50)
        existing_end   = existing_start + timedelta(days=5)
        self._create_conge_approuve(existing_start, existing_end)
        debut = existing_end + timedelta(days=1)
        fin   = debut + timedelta(days=4)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r7_rejete_ne_bloque_pas(self):
        """Un congé REJETE sur les mêmes dates ne doit pas bloquer une nouvelle demande."""
        existing_start = _d(PREVIS_MINIMUM_JOURS + 50)
        Conge.objects.create(
            contractuel=self.contractuel,
            type_conge="ANNUEL",
            date_debut=existing_start,
            date_fin=existing_start + timedelta(days=5),
            motif="Congé rejeté",
            statut="REJETE",
        )
        debut = existing_start
        fin   = existing_start + timedelta(days=5)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertTrue(form.is_valid(), form.errors)

    def test_r7_en_attente_bloque(self):
        """Un congé EN_ATTENTE sur les mêmes dates doit bloquer."""
        existing_start = _d(PREVIS_MINIMUM_JOURS + 50)
        Conge.objects.create(
            contractuel=self.contractuel,
            type_conge="ANNUEL",
            date_debut=existing_start,
            date_fin=existing_start + timedelta(days=5),
            motif="En attente",
            statut="EN_ATTENTE",
        )
        debut = existing_start
        fin   = existing_start + timedelta(days=5)
        form = self._form(self._data(date_debut=debut, date_fin=fin))
        self.assertFalse(form.is_valid())
        self.assertIn("chevauche", str(form.errors).lower())
