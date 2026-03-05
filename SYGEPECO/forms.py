from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Contractuel, Contrat, Presence, Conge, Permission, Departement, Poste, TypeContrat, Entreprise


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
    class Meta:
        model = Contractuel
        fields = [
            'matricule', 'nom', 'prenom', 'genre', 'date_naissance', 'lieu_naissance',
            'nationalite', 'email', 'telephone', 'adresse', 'photo',
            'poste', 'departement', 'date_embauche', 'statut',
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
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
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
        fields = ['contractuel', 'date', 'heure_debut', 'heure_fin', 'motif']
        widgets = {
            'contractuel': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
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
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.all(),
        required=False,
        empty_label="Tous les départements",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# ─── Formulaires Espace Contractuel ─────────────────────────

class EspaceProfilForm(forms.ModelForm):
    """Le contractuel ne peut modifier que ses infos de contact."""
    class Meta:
        model = Contractuel
        fields = ['photo', 'email', 'telephone', 'adresse']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EspaceCongeForm(forms.ModelForm):
    """Demande de congé par le contractuel (sans champ contractuel)."""
    class Meta:
        model = Conge
        fields = ['type_conge', 'date_debut', 'date_fin', 'motif']
        widgets = {
            'type_conge': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                           'placeholder': 'Précisez le motif de votre demande…'}),
        }

    def clean(self):
        cleaned = super().clean()
        d1 = cleaned.get('date_debut')
        d2 = cleaned.get('date_fin')
        if d1 and d2 and d2 < d1:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        return cleaned


class EspacePermissionForm(forms.ModelForm):
    """Demande de permission par le contractuel (sans champ contractuel)."""
    class Meta:
        model = Permission
        fields = ['date', 'heure_debut', 'heure_fin', 'motif']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                           'placeholder': 'Précisez le motif de votre demande…'}),
        }

    def clean(self):
        cleaned = super().clean()
        h1 = cleaned.get('heure_debut')
        h2 = cleaned.get('heure_fin')
        if h1 and h2 and h2 <= h1:
            raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")
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
