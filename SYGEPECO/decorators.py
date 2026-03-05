from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# Rôles qui ont accès au dashboard RH
ROLES_RH = ('ADMINISTRATEUR', 'ENTREPRISE', 'MANAGER', 'DRH', 'RH')


def get_role(user):
    """Retourne le rôle du UserProfile ou None."""
    try:
        return user.profile.role
    except Exception:
        return None


def contractuel_required(view_func):
    """Réserve la vue aux utilisateurs liés à un Contractuel."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'contractuel') or request.user.contractuel is None:
            messages.error(request, "Accès refusé : espace réservé aux contractuels.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def rh_required(view_func):
    """Réserve la vue aux rôles RH/Admin (pas aux contractuels)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if hasattr(request.user, 'contractuel') and request.user.contractuel is not None:
            messages.warning(request, "Accès refusé : réservé aux gestionnaires RH.")
            return redirect('espace_home')
        return view_func(request, *args, **kwargs)
    return wrapper


def administrateur_required(view_func):
    """Réserve la vue au rôle Administrateur uniquement."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_role(request.user)
        if role not in ('ADMINISTRATEUR', 'DRH') and not request.user.is_superuser:
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def entreprise_required(view_func):
    """Réserve la vue au rôle Entreprise (et Administrateur)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_role(request.user)
        if role not in ('ADMINISTRATEUR', 'ENTREPRISE', 'DRH') and not request.user.is_superuser:
            messages.error(request, "Accès réservé au rôle Entreprise.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Réserve la vue au rôle Manager (et Administrateur)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_role(request.user)
        if role not in ('ADMINISTRATEUR', 'MANAGER', 'DRH') and not request.user.is_superuser:
            messages.error(request, "Accès réservé au rôle Manager.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
