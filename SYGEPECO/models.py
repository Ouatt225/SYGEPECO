from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMINISTRATEUR', 'Administrateur'),
        ('ENTREPRISE', 'Entreprise'),
        ('MANAGER', 'Manager'),
        ('EMPLOYE', 'Employé'),
        # Anciens rôles conservés pour compatibilité
        ('DRH', 'Directeur des Ressources Humaines'),
        ('RH', 'Responsable RH'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='EMPLOYE')
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True)
    entreprise = models.ForeignKey(
        'Entreprise', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='gestionnaires',
        verbose_name="Entreprise gérée"
    )
    direction = models.ForeignKey(
        'Direction', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='managers',
        verbose_name="Direction"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_role_display()}"

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"


class Direction(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='directions_gerees'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
        ordering = ['nom']


class Poste(models.Model):
    titre = models.CharField(max_length=100)
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True, related_name='postes')
    description = models.TextField(blank=True)

    def __str__(self):
        dir_nom = self.direction.nom if self.direction else "—"
        return f"{self.titre} ({dir_nom})"

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['titre']


class TypeContrat(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    duree_max_jours = models.IntegerField(null=True, blank=True, help_text="Durée max en jours (vide = illimité)")

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Type de Contrat"
        verbose_name_plural = "Types de Contrat"
        ordering = ['nom']


class Entreprise(models.Model):
    SECTEUR_CHOICES = [
        ('SECURITE',    'Sécurité / Gardiennage'),
        ('BTP',         'BTP / Construction'),
        ('COMMERCE',    'Commerce'),
        ('INDUSTRIE',   'Industrie'),
        ('SERVICES',    'Services'),
        ('INFORMATIQUE','Informatique'),
        ('AUTRE',       'Autre'),
    ]
    nom        = models.CharField(max_length=150, unique=True, verbose_name="Raison sociale")
    sigle      = models.CharField(max_length=30, blank=True, verbose_name="Sigle / Abréviation")
    secteur    = models.CharField(max_length=15, choices=SECTEUR_CHOICES, default='AUTRE')
    adresse    = models.TextField(blank=True)
    telephone  = models.CharField(max_length=20, blank=True)
    email      = models.EmailField(blank=True)
    logo       = models.ImageField(upload_to='entreprises/', blank=True, null=True)
    description = models.TextField(blank=True)
    active     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sigle if self.sigle else self.nom

    def nb_contractuels(self):
        return self.contractuels.filter(statut='ACTIF').count()

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ['nom']


class Contractuel(models.Model):
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('INACTIF', 'Inactif'),
        ('SUSPENDU', 'Suspendu'),
    ]
    GENRE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    SITUATION_FAMILLE_CHOICES = [
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE',       'Marié(e)'),
        ('DIVORCE',     'Divorcé(e)'),
        ('VEUF',        'Veuf / Veuve'),
        ('UNION_LIBRE', 'Union libre'),
    ]
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='contractuel',
        verbose_name="Compte utilisateur"
    )
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100, blank=True)
    nationalite = models.CharField(max_length=50, default='Ivoirienne')
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    photo = models.ImageField(upload_to='contractuels/', blank=True, null=True)
    # ── Infos sociales (renseignées par l'agent) ──────────────
    numero_cnps       = models.CharField(max_length=30,  blank=True, verbose_name="Numéro CNPS")
    commune           = models.CharField(max_length=100, blank=True, verbose_name="Commune")
    ville             = models.CharField(max_length=100, blank=True, default='ABIDJAN', verbose_name="Ville")
    situation_famille = models.CharField(max_length=15,  blank=True, choices=[
        ('CELIBATAIRE', 'Célibataire'), ('MARIE', 'Marié(e)'),
        ('DIVORCE', 'Divorcé(e)'), ('VEUF', 'Veuf / Veuve'), ('UNION_LIBRE', 'Union libre'),
    ], verbose_name="Situation familiale")
    nombre_enfants    = models.PositiveIntegerField(default=0, verbose_name="Nombre d'enfants")
    entreprise  = models.ForeignKey('Entreprise', on_delete=models.SET_NULL, null=True, blank=True, related_name='contractuels', verbose_name="Entreprise")
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, related_name='contractuels')
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, related_name='contractuels')
    date_embauche = models.DateField()
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ACTIF')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.matricule} — {self.nom} {self.prenom}"

    def get_full_name(self):
        return f"{self.nom} {self.prenom}"

    def get_contrat_actif(self):
        return self.contrats.filter(statut='EN_COURS').first()

    class Meta:
        verbose_name = "Contractuel"
        verbose_name_plural = "Contractuels"
        ordering = ['nom', 'prenom']


class Contrat(models.Model):
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('EXPIRE', 'Expiré'),
        ('RESILIE', 'Résilié'),
        ('RENOUVELE', 'Renouvelé'),
    ]
    contractuel = models.ForeignKey(Contractuel, on_delete=models.CASCADE, related_name='contrats')
    type_contrat = models.ForeignKey(TypeContrat, on_delete=models.PROTECT)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    salaire = models.DecimalField(max_digits=12, decimal_places=2)
    observations = models.TextField(blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='EN_COURS')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contrats_crees')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrat {self.type_contrat} — {self.contractuel}"

    def is_expired(self):
        if self.date_fin:
            return self.date_fin < timezone.now().date()
        return False

    class Meta:
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        ordering = ['-created_at']


class Presence(models.Model):
    STATUT_CHOICES = [
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('RETARD', 'En retard'),
        ('JUSTIFIE', 'Absence justifiée'),
        ('CONGE', 'En congé'),
        ('PERMISSION', 'En permission'),
    ]
    contractuel = models.ForeignKey(Contractuel, on_delete=models.CASCADE, related_name='presences')
    date = models.DateField(default=timezone.now)
    heure_arrivee = models.TimeField(null=True, blank=True)
    heure_depart = models.TimeField(null=True, blank=True)
    statut = models.CharField(max_length=12, choices=STATUT_CHOICES, default='PRESENT')
    observations = models.TextField(blank=True)

    def __str__(self):
        return f"{self.contractuel} — {self.date} ({self.get_statut_display()})"

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        ordering = ['-date']
        unique_together = ('contractuel', 'date')


class Conge(models.Model):
    TYPE_CHOICES = [
        ('ANNUEL', 'Congé annuel'),
        ('MALADIE', 'Congé maladie'),
        ('MATERNITE', 'Congé maternité'),
        ('PATERNITE', 'Congé paternité'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE_MANAGER', 'Validé par le manager'),
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
        ('ANNULE', 'Annulé'),
    ]
    contractuel = models.ForeignKey(Contractuel, on_delete=models.CASCADE, related_name='conges')
    type_conge = models.CharField(max_length=15, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='EN_ATTENTE')
    approuve_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_approuves'
    )
    commentaire_rh = models.TextField(blank=True)
    valide_par_manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conges_valides_manager',
        verbose_name="Validé par (manager)"
    )
    commentaire_manager = models.TextField(blank=True, verbose_name="Commentaire manager")
    document_medical = models.FileField(
        upload_to='conges/documents/',
        blank=True, null=True,
        verbose_name="Document médical (arrêt maladie)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.contractuel} — {self.get_type_conge_display()} ({self.date_debut} → {self.date_fin})"

    def nb_jours(self):
        delta = self.date_fin - self.date_debut
        return delta.days + 1

    class Meta:
        verbose_name = "Congé"
        verbose_name_plural = "Congés"
        ordering = ['-created_at']


class Permission(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
    ]
    contractuel = models.ForeignKey(Contractuel, on_delete=models.CASCADE, related_name='permissions')
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    statut = models.CharField(max_length=12, choices=STATUT_CHOICES, default='EN_ATTENTE')
    approuve_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='permissions_approuvees'
    )
    commentaire_rh = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contractuel} — Permission {self.date_debut} → {self.date_fin}"

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ['-created_at']


class ActionLog(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actions')
    action = models.CharField(max_length=200)
    modele_concerne = models.CharField(max_length=50, blank=True)
    objet_id = models.IntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.utilisateur} — {self.action} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"

    class Meta:
        verbose_name = "Journal d'action"
        verbose_name_plural = "Journal des actions"
        ordering = ['-created_at']


# ─── Synchronisation direction Contractuel ↔ UserProfile ─────────────────────
import logging
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver


logger = logging.getLogger('SYGEPECO')

@receiver(post_save, sender='SYGEPECO.Contractuel')
def _sync_contractuel_dir_to_profile(sender, instance, **kwargs):
    """Contractuel.direction changée → met à jour UserProfile.direction."""
    # Évite la boucle : si update_fields == ['direction'] c'est nous qui avons lancé la mise à jour
    update_fields = kwargs.get('update_fields')
    if update_fields is not None and set(update_fields) == {'direction'}:
        return
    try:
        if instance.user_id:
            UserProfile.objects.filter(
                user_id=instance.user_id
            ).exclude(
                direction_id=instance.direction_id
            ).update(direction=instance.direction)
    except Exception:
        pass


@receiver(post_save, sender='SYGEPECO.UserProfile')
def _sync_profile_dir_to_contractuel(sender, instance, **kwargs):
    """UserProfile.direction changée → met à jour Contractuel.direction."""
    update_fields = kwargs.get('update_fields')
    if update_fields is not None and set(update_fields) == {'direction'}:
        return
    try:
        Contractuel.objects.filter(
            user_id=instance.user_id
        ).exclude(
            direction_id=instance.direction_id
        ).update(direction=instance.direction)
    except Exception:
        logger.exception('Erreur sync direction Profile→Contractuel (pk=%s)', getattr(instance, 'pk', '?'))
