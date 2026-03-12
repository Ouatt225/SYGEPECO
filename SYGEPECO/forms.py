from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .constants import (
    QUOTA_CONGE_ANNUEL, PREVIS_MINIMUM_JOURS, CONGE_MATERNITE_MAX,
    CONGE_PATERNITE_MAX, PERMISSION_MAX_HEURES,
)
from .models import Contractuel, Contrat, Presence, Conge, Permission, Direction, Poste, TypeContrat, Entreprise



# ─── Validation MIME côté serveur ───────────────────────────────────
_MAGIC = {
    b'\x25\x50\x44\x46': 'application/pdf',    # %PDF
    b'\xff\xd8\xff':       'image/jpeg',
    b'\x89\x50\x4e\x47': 'image/png',           # \x89PNG
    b'\x47\x49\x46\x38': 'image/gif',           # GIF8
    b'\x52\x49\x46\x46': 'image/webp',          # RIFF (WebP)
}
_ALLOWED_DOC  = {'application/pdf', 'image/jpeg', 'image/png'}
_ALLOWED_IMG  = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


def _check_upload_mime(file_obj, allowed_mimes: set, label: str):
    """
    Lit les 8 premiers octets et compare aux signatures connues.
    Lève forms.ValidationError si le type MIME détecté n'est pas autorisé.
    """
    if file_obj is None:
        return
    file_obj.seek(0)
    header = file_obj.read(8)
    file_obj.seek(0)
    detected = None
    for sig, mime in _MAGIC.items():
        if header[:len(sig)] == sig:
            detected = mime
            break
    if detected not in allowed_mimes:
        friendly = ', '.join(sorted(allowed_mimes))
        raise forms.ValidationError(
            f"Le fichier {label!r} n'est pas d'un type autorise. "
            f"Types acceptes : {friendly}. "
            f"Type detecte : {detected or 'inconnu'}."
        )

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur",
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe',
        })
    )


class ContractuelForm(forms.ModelForm):

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'read'):
            _check_upload_mime(photo, _ALLOWED_IMG, photo.name)
        return photo

    def clean_piece_identite_recto(self):
        f = self.cleaned_data.get('piece_identite_recto')
        if f and hasattr(f, 'read'):
            _check_upload_mime(f, _ALLOWED_IMG, f.name)
        return f

    def clean_piece_identite_verso(self):
        f = self.cleaned_data.get('piece_identite_verso')
        if f and hasattr(f, 'read'):
            _check_upload_mime(f, _ALLOWED_IMG, f.name)
        return f

    def clean_document_prise_service(self):
        f = self.cleaned_data.get('document_prise_service')
        if f and hasattr(f, 'read'):
            _check_upload_mime(f, _ALLOWED_DOC, f.name)
        return f

    class Meta:
        model = Contractuel
        fields = [
            'matricule', 'nom', 'prenom', 'genre', 'date_naissance', 'lieu_naissance',
            'nationalite', 'email', 'telephone', 'adresse', 'photo',
            'poste', 'direction', 'date_embauche', 'statut',
            # Pièce d'identité
            'numero_piece_identite', 'piece_identite_recto', 'piece_identite_verso',
            'document_prise_service',
            # Contact d'urgence
            'urgence_nom', 'urgence_lien', 'urgence_telephone',
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CTR-001'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'poste': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            # Pièce d'identité
            'numero_piece_identite':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CI-123456'}),
            'piece_identite_recto':   forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'piece_identite_verso':   forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'document_prise_service': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'}),
            # Contact d'urgence
            'urgence_nom':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'urgence_lien':      forms.Select(attrs={'class': 'form-select'}),
            'urgence_telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 07 XX XX XX XX'}),
        }


class ContratForm(forms.ModelForm):
    class Meta:
        model = Contrat
        fields = ['contractuel', 'type_contrat', 'date_debut', 'date_fin', 'salaire', 'observations', 'statut']
        widgets = {
            'contractuel': forms.Select(attrs={'class': 'form-select'}),
            'type_contrat': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }


class PresenceForm(forms.ModelForm):
    class Meta:
        model = Presence
        fields = ['contractuel', 'date', 'heure_arrivee', 'heure_depart', 'statut', 'observations']
        widgets = {
            'contractuel': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_arrivee': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_depart': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CongeForm(forms.ModelForm):
    class Meta:
        model = Conge
        fields = ['contractuel', 'type_conge', 'date_debut', 'date_fin', 'motif']
        widgets = {
            'contractuel': forms.Select(attrs={'class': 'form-select'}),
            'type_conge': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CongeDecisionForm(forms.ModelForm):
    class Meta:
        model = Conge
        fields = ['commentaire_rh']
        widgets = {
            'commentaire_rh': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['contractuel', 'date_debut', 'date_fin', 'motif']
        widgets = {
            'contractuel': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PermissionDecisionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['commentaire_rh']
        widgets = {
            'commentaire_rh': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RapportFiltreForm(forms.Form):
    MOIS_CHOICES = [(i, f"{i:02d}") for i in range(1, 13)]
    ANNEE_CHOICES = [(y, str(y)) for y in range(2020, 2030)]

    mois = forms.ChoiceField(choices=MOIS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    annee = forms.ChoiceField(choices=ANNEE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    direction = forms.ModelChoiceField(
        queryset=Direction.objects.all(),
        required=False,
        empty_label="Toutes les directions",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# ─── Formulaires Espace Contractuel ─────────────────────────

class EspaceProfilForm(forms.ModelForm):
    """L'agent peut modifier ses informations personnelles et de contact uniquement.
    Les champs administratifs (matricule, poste, direction, entreprise, date d'embauche)
    sont en lecture seule et gérés exclusivement par les RH.
    """

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'read'):
            _check_upload_mime(photo, _ALLOWED_IMG, photo.name)
        return photo

    def clean_piece_identite_recto(self):
        f = self.cleaned_data.get('piece_identite_recto')
        if f and hasattr(f, 'read'):
            _check_upload_mime(f, _ALLOWED_IMG, f.name)
        return f

    def clean_piece_identite_verso(self):
        f = self.cleaned_data.get('piece_identite_verso')
        if f and hasattr(f, 'read'):
            _check_upload_mime(f, _ALLOWED_IMG, f.name)
        return f

    def clean_document_prise_service(self):
        f = self.cleaned_data.get('document_prise_service')
        if f and hasattr(f, 'read'):
            _check_upload_mime(f, _ALLOWED_DOC, f.name)
        return f

    # Champ salaire hors modèle Contractuel (lié au contrat actif)
    salaire = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        label="Salaire (FCFA)",
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ex: 150000'}),
    )

    class Meta:
        model = Contractuel
        fields = [
            # Photo
            'photo',
            # Identité personnelle (non administrative)
            'nom', 'prenom', 'genre', 'date_naissance', 'lieu_naissance', 'nationalite',
            # Contact
            'email', 'telephone', 'adresse',
            # Infos sociales
            'commune', 'ville', 'situation_famille', 'nombre_enfants', 'numero_cnps',
            # Pièce d'identité
            'numero_piece_identite', 'piece_identite_recto', 'piece_identite_verso',
            'document_prise_service',
            # Contact d'urgence
            'urgence_nom', 'urgence_lien', 'urgence_telephone',
        ]
        widgets = {
            'photo':             forms.FileInput(attrs={'accept': 'image/*'}),
            # Identité
            'nom':               forms.TextInput(),
            'prenom':            forms.TextInput(),
            'genre':             forms.Select(),
            'date_naissance':    forms.DateInput(attrs={'type': 'date'}),
            'lieu_naissance':    forms.TextInput(),
            'nationalite':       forms.TextInput(),
            # Contact
            'email':             forms.EmailInput(),
            'telephone':         forms.TextInput(),
            'adresse':           forms.Textarea(attrs={'rows': 2}),
            # Social
            'commune':           forms.TextInput(),
            'ville':             forms.TextInput(),
            'situation_famille': forms.Select(),
            'nombre_enfants':    forms.NumberInput(attrs={'min': '0', 'max': '20'}),
            'numero_cnps':       forms.TextInput(),
            # Pièce d'identité
            'numero_piece_identite':  forms.TextInput(attrs={'placeholder': 'Ex: CI-123456'}),
            'piece_identite_recto':   forms.FileInput(attrs={'accept': 'image/*'}),
            'piece_identite_verso':   forms.FileInput(attrs={'accept': 'image/*'}),
            'document_prise_service': forms.FileInput(attrs={'accept': '.pdf,image/*'}),
            # Contact d'urgence
            'urgence_nom':       forms.TextInput(attrs={'placeholder': 'Nom complet'}),
            'urgence_lien':      forms.Select(),
            'urgence_telephone': forms.TextInput(attrs={'placeholder': 'Ex: 07 XX XX XX XX'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir le salaire depuis le contrat actif
        if self.instance and self.instance.pk:
            contrat = self.instance.get_contrat_actif()
            if contrat and contrat.salaire:
                self.fields['salaire'].initial = contrat.salaire


class EspaceCongeForm(forms.ModelForm):
    """Demande de congé par le contractuel (sans champ contractuel)."""

    class Meta:
        model = Conge
        fields = ['type_conge', 'date_debut', 'date_fin', 'motif', 'document_medical']
        widgets = {
            'type_conge':       forms.Select(attrs={'class': 'form-select'}),
            'date_debut':       forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'placeholder': 'Sélectionner une date…'}),
            'date_fin':         forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'placeholder': 'Sélectionner une date…'}),
            'motif':            forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                      'placeholder': 'Précisez le motif de votre demande…'}),
            'document_medical': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
        }

    def __init__(self, *args, contractuel=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._contractuel = contractuel
        self.fields['document_medical'].required = False
        self.fields['document_medical'].label = "Justificatif médical (arrêt maladie)"

    def clean_document_medical(self):
        doc = self.cleaned_data.get('document_medical')
        if doc and hasattr(doc, 'read'):
            _check_upload_mime(doc, _ALLOWED_DOC, doc.name)
        return doc

    def clean(self):
        from datetime import date as date_type, timedelta
        cleaned = super().clean()
        d1 = cleaned.get('date_debut')
        d2 = cleaned.get('date_fin')

        if d1 and d2 and d2 < d1:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")

        # ── Congé maladie : justificatif obligatoire ──────────────
        if cleaned.get('type_conge') == 'MALADIE':
            doc = cleaned.get('document_medical')
            if not doc and not getattr(self.instance, 'document_medical', None):
                raise forms.ValidationError(
                    "Un justificatif médical (arrêt maladie) est obligatoire pour un congé maladie. "
                    "Veuillez joindre votre document (PDF, JPG ou PNG)."
                )

        # ── Préavis minimum de 7 jours ────────────────────────────
        if d1:
            delai = (d1 - date_type.today()).days
            if delai < 7:
                date_min = (date_type.today() + timedelta(days=PREVIS_MINIMUM_JOURS)).strftime('%d/%m/%Y')
                raise forms.ValidationError(
                    f"Un préavis de 7 jours minimum est requis. "
                    f"Votre date de début est dans {max(delai, 0)} jour(s). "
                    f"Date de début possible au plus tôt : {date_min}."
                )

        # ── Congé maternité : limité à 180 jours ─────────────────
        if cleaned.get('type_conge') == 'MATERNITE' and d1 and d2:
            jours_demandes = (d2 - d1).days + 1
            if jours_demandes > CONGE_MATERNITE_MAX:
                raise forms.ValidationError(
                    f"Le congé maternité est limité à 180 jours. "
                    f"Vous demandez {jours_demandes} jours."
                )

        # ── Congé paternité : limité à 30 jours ──────────────────
        if cleaned.get('type_conge') == 'PATERNITE' and d1 and d2:
            jours_demandes = (d2 - d1).days + 1
            if jours_demandes > CONGE_PATERNITE_MAX:
                raise forms.ValidationError(
                    f"Le congé paternité est limité à 30 jours. "
                    f"Vous demandez {jours_demandes} jours."
                )

        # ── Contrôle quota congé annuel ──────────────────────────
        if cleaned.get('type_conge') == 'ANNUEL' and d1 and d2 and self._contractuel:
            annee = d1.year
            # Jours déjà consommés ou en attente cette année civile
            deja_pris = sum(
                cg.nb_jours()
                for cg in self._contractuel.conges.filter(
                    type_conge='ANNUEL',
                    statut__in=['APPROUVE', 'EN_ATTENTE'],
                    date_debut__year=annee,
                )
            )
            # Jours demandés dans cette nouvelle requête
            jours_demandes = (d2 - d1).days + 1
            solde_restant = QUOTA_CONGE_ANNUEL - deja_pris

            if jours_demandes > solde_restant:
                if solde_restant <= 0:
                    raise forms.ValidationError(
                        f"Vous avez épuisé votre quota de {QUOTA_CONGE_ANNUEL} jours de congé annuel pour {annee}."
                    )
                else:
                    raise forms.ValidationError(
                        f"Cette demande dépasse votre quota annuel. "
                        f"Il vous reste {solde_restant} jour(s) sur {QUOTA_CONGE_ANNUEL} pour {annee} "
                        f"(déjà pris ou en attente : {deja_pris} j). "
                        f"Vous demandez {jours_demandes} j."
                    )

        # ── Contrôle chevauchement de dates ──────────────────────
        if d1 and d2 and self._contractuel:
            chevauchement = self._contractuel.conges.filter(
                statut__in=['APPROUVE', 'EN_ATTENTE'],
                date_debut__lte=d2,
                date_fin__gte=d1,
            )
            if chevauchement.exists():
                c = chevauchement.first()
                raise forms.ValidationError(
                    f"Ces dates chevauchent un congé existant ({c.get_type_conge_display()} "
                    f"du {c.date_debut.strftime('%d/%m/%Y')} au {c.date_fin.strftime('%d/%m/%Y')}, "
                    f"statut : {c.get_statut_display()})."
                )

        return cleaned


class EspacePermissionForm(forms.ModelForm):
    """Demande de permission par le contractuel (sans champ contractuel)."""
    class Meta:
        model = Permission
        fields = ['date_debut', 'date_fin', 'motif']
        widgets = {
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'placeholder': 'Sélectionner une date…'}),
            'date_fin':   forms.DateInput(attrs={'class': 'form-control', 'type': 'text', 'placeholder': 'Sélectionner une date…'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                           'placeholder': 'Précisez le motif de votre demande…'}),
        }

    def clean(self):
        cleaned = super().clean()
        d1 = cleaned.get('date_debut')
        d2 = cleaned.get('date_fin')
        if d1 and d2:
            if d2 < d1:
                raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
            duree = (d2 - d1).days + 1
            if duree > 3:
                raise forms.ValidationError(
                    f"Une permission ne peut pas dépasser 3 jours (durée saisie : {duree} jour{'s' if duree > 1 else ''})."
                )
        return cleaned


WIDGET_INPUT  = {'class': 'form-control'}
WIDGET_SELECT = {'class': 'form-select'}
WIDGET_AREA   = {'class': 'form-control', 'rows': 3}


class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ['nom', 'sigle', 'secteur', 'telephone', 'email', 'adresse', 'logo', 'description', 'active']
        widgets = {
            'nom':         forms.TextInput(attrs=WIDGET_INPUT),
            'sigle':       forms.TextInput(attrs=WIDGET_INPUT),
            'secteur':     forms.Select(attrs=WIDGET_SELECT),
            'telephone':   forms.TextInput(attrs=WIDGET_INPUT),
            'email':       forms.EmailInput(attrs=WIDGET_INPUT),
            'adresse':     forms.Textarea(attrs=WIDGET_AREA),
            'description': forms.Textarea(attrs=WIDGET_AREA),
        }
