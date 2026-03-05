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

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_role_display()}"

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"


class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='departements_geres'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['nom']


class Poste(models.Model):
    titre = models.CharField(max_length=100)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='postes')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.titre} ({self.departement.nom})"

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
    telephone = models.CharField(max_length=20)
    adresse = models.TextField(blank=True)
    photo = models.ImageField(upload_to='contractuels/', blank=True, null=True)
    entreprise  = models.ForeignKey('Entreprise', on_delete=models.SET_NULL, null=True, blank=True, related_name='contractuels', verbose_name="Entreprise")
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, related_name='contractuels')
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, related_name='contractuels')
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
        ('SANS_SOLDE', 'Congé sans solde'),
        ('EXCEPTIONNEL', 'Congé exceptionnel'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
        ('ANNULE', 'Annulé'),
    ]
    contractuel = models.ForeignKey(Contractuel, on_delete=models.CASCADE, related_name='conges')
    type_conge = models.CharField(max_length=15, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    statut = models.CharField(max_length=12, choices=STATUT_CHOICES, default='EN_ATTENTE')
    approuve_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_approuves'
    )
    commentaire_rh = models.TextField(blank=True)
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
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    motif = models.TextField()
    statut = models.CharField(max_length=12, choices=STATUT_CHOICES, default='EN_ATTENTE')
    approuve_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='permissions_approuvees'
    )
    commentaire_rh = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contractuel} — Permission {self.date} ({self.heure_debut}→{self.heure_fin})"

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
