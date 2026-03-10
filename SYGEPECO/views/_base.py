"""
Utilitaires partagés entre toutes les vues.
Récupération de l'entreprise associée à un utilisateur.
"""
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth, ExtractDay
from django.utils import timezone

from ..models import (
    Contractuel, Contrat, Presence, Conge, Permission,
    Direction, Poste, TypeContrat, ActionLog, UserProfile, Entreprise
)
from ..forms import (
    LoginForm, ContractuelForm, ContratForm, PresenceForm,
    CongeForm, CongeDecisionForm, PermissionForm, PermissionDecisionForm, RapportFiltreForm,
    EspaceProfilForm, EspaceCongeForm, EspacePermissionForm,
)
from ..utils import (
    log_action, export_presences_excel, export_conges_excel,
    export_permissions_excel, export_contractuels_excel,
)
from ..decorators import contractuel_required, rh_required, administrateur_required
from ..utils import get_manager_direction
import logging
logger = logging.getLogger('SYGEPECO')


def redirect_by_role(user):
    if hasattr(user, 'contractuel') and user.contractuel is not None:
        return redirect('espace_home')
    if hasattr(user, 'profile') and user.profile.role == 'ENTREPRISE':
        return redirect('entreprise_espace_home')
    return redirect('dashboard')


def build_alertes_conges(conges_qs, today):
    j1 = list(conges_qs.filter(
        statut='APPROUVE', date_debut=today + timedelta(days=1)
    ).select_related('contractuel').order_by('date_debut'))
    j7 = list(conges_qs.filter(
        statut='APPROUVE', date_debut=today + timedelta(days=7)
    ).select_related('contractuel').order_by('date_debut'))
    exclus = [today + timedelta(days=1), today + timedelta(days=7)]
    nouveaux = list(conges_qs.filter(
        statut='APPROUVE',
        date_debut__gt=today,
        date_debut__lte=today + timedelta(days=30),
    ).exclude(date_debut__in=exclus).select_related('contractuel').order_by('date_debut')[:10])
    return {'j1': j1, 'j7': j7, 'nouveaux': nouveaux,
            'total': len(j1) + len(j7) + len(nouveaux)}


def get_entreprise_for_user(user):
    try:
        profile = user.profile
    except Exception:  # UserProfile.DoesNotExist ou AttributeError
        return None
    if profile.role in ('ADMINISTRATEUR', 'DRH'):
        return None
    return profile.entreprise


def ent_check(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role not in (
            'ENTREPRISE', 'ADMINISTRATEUR', 'DRH'):
        messages.error(request, "Accès non autorisé.")
        return None, redirect('login')
    return get_entreprise_for_user(request.user), None