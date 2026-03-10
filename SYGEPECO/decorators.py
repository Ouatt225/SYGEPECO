"""
Décorateurs de contrôle d'accès par rôle pour SYGEPECO.
Rôles disponibles : ADMINISTRATEUR, DRH, RH, MANAGER, ENTREPRISE, EMPLOYE.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def get_role(user):
    """Retourne le role du UserProfile ou None."""
    try:
        return user.profile.role
    except AttributeError:
        return None


def roles_required(*roles, redirect_to='dashboard', msg=None):
    """
    Decorateur parametrable : autorise uniquement les roles specifies.

    Usage :
        @roles_required('ADMINISTRATEUR', 'MANAGER')
        def ma_vue(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            role = get_role(request.user)
            if role not in roles:
                error_msg = msg or f"Acces reserve aux roles : {', '.join(roles)}."
                messages.error(request, error_msg)
                return redirect(redirect_to)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def contractuel_required(view_func):
    """Reserve la vue aux utilisateurs lies a un Contractuel."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'contractuel') or request.user.contractuel is None:
            messages.error(request, "Acces refuse : espace reserve aux contractuels.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def rh_required(view_func):
    """Reserve la vue aux roles RH/Admin (pas aux contractuels ni aux entreprises)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if hasattr(request.user, 'contractuel') and request.user.contractuel is not None:
            messages.warning(request, "Acces refuse : reserve aux gestionnaires RH.")
            return redirect('espace_home')
        role = get_role(request.user)
        if role == 'ENTREPRISE':
            return redirect('entreprise_espace_home')
        return view_func(request, *args, **kwargs)
    return wrapper


def administrateur_required(view_func):
    """Reserve la vue au role Administrateur uniquement."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_role(request.user)
        if role not in ('ADMINISTRATEUR', 'DRH'):
            messages.error(request, "Acces reserve aux administrateurs.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def entreprise_required(view_func):
    """Reserve la vue au role Entreprise (et Administrateur)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_role(request.user)
        if role not in ('ADMINISTRATEUR', 'ENTREPRISE', 'DRH'):
            messages.error(request, "Acces reserve au role Entreprise.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Reserve la vue au role Manager (et Administrateur)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_role(request.user)
        if role not in ('ADMINISTRATEUR', 'MANAGER', 'DRH'):
            messages.error(request, "Acces reserve au role Manager.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Alias pratiques pour les vues espace-entreprise ───────────────
# Usage : @roles_required(*ROLES_ACCES_ENTREPRISE)
from .constants import ROLES_ACCES_ENTREPRISE, ROLES_ACCES_MANAGER, ROLES_ACCES_ADMIN
