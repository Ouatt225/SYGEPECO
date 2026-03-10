import logging

logger = logging.getLogger('SYGEPECO')

from django.conf import settings
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from pathlib import Path


# Dossiers dont l'acces est restreint
_SENSITIVE_PREFIXES = (
    "conges/documents/",
)

_ROLES_RH = ("ADMINISTRATEUR", "DRH", "RH", "MANAGER")


def _has_rh_access(user):
    try:
        return user.profile.role in _ROLES_RH
    except AttributeError:
        return False


def _find_conge(rel_path):
    """
    Recherche le Conge correspondant au chemin du document.
    Essaie les deux variantes de séparateurs (/ et \\) pour compatibilité Windows.
    Renvoie None si introuvable.
    """
    from ..models import Conge
    # Générer les deux variantes de chemin
    fwd = rel_path.replace("\\", "/")
    bwd = rel_path.replace("/", "\\")
    paths = {fwd, bwd}
    try:
        return (
            Conge.objects
            .select_related("contractuel", "contractuel__entreprise")
            .filter(document_medical__in=paths)
            .first()
        )
    except Exception:
        logger.warning('media_serve._find_conge: erreur DB pour path=%s', rel_path, exc_info=True)
        return None


def _has_doc_access(user, rel_path):
    """
    Accès élargi aux documents médicaux :
      - le contractuel propriétaire du congé
      - un utilisateur ENTREPRISE dont l'agent appartient à l'entreprise
    """
    conge = _find_conge(rel_path)
    if conge is None:
        return False

    # Agent lui-même
    if hasattr(user, "contractuel") and user.contractuel == conge.contractuel:
        return True

    # Entreprise de l'agent
    try:
        if user.profile.role == "ENTREPRISE":
            ent = user.profile.entreprise
            if ent and conge.contractuel.entreprise_id == ent.pk:
                return True
    except Exception:
        logger.warning('media_serve._has_doc_access: erreur pour user=%s path=%s', getattr(user, "username", "?"), rel_path, exc_info=True)

    return False


def _deny_redirect(request):
    """Redirige selon le rôle après refus d'accès."""
    if hasattr(request.user, "contractuel") and request.user.contractuel:
        messages.error(request, "Accès refusé.")
        return redirect("espace_home")
    try:
        if request.user.profile.role == "ENTREPRISE":
            messages.error(request, "Accès refusé : document confidentiel.")
            return redirect("entreprise_espace_conges")
    except AttributeError:
        pass
    messages.error(request, "Accès refusé : document confidentiel.")
    return redirect("dashboard")


@login_required
def protected_media(request, path):
    """Sert les fichiers media uniquement aux utilisateurs authentifiés.
    Les documents médicaux sont accessibles à l'agent, son entreprise, et le RH."""
    # Sécurité : empêcher le path traversal
    media_root = Path(settings.MEDIA_ROOT).resolve()
    target = (media_root / path).resolve()
    if not str(target).startswith(str(media_root)):
        raise Http404

    if not target.exists() or not target.is_file():
        raise Http404

    # Restriction sur les dossiers sensibles
    rel = path.replace("\\", "/")
    if any(rel.startswith(prefix) for prefix in _SENSITIVE_PREFIXES):
        if not _has_rh_access(request.user) and not _has_doc_access(request.user, rel):
            return _deny_redirect(request)

    return FileResponse(open(target, "rb"))
