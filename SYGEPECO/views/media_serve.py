"""
Serveur de medias proteges — acces restreint par authentification et role.

Architecture :
  - Tout fichier sous /media/ exige @login_required.
  - Les dossiers sensibles (documents medicaux) exigent un role RH
    ou d'etre le proprietaire du document / l'entreprise concernee.
  - Les photos (profiles/, entreprises/, contractuels/) sont accessibles
    a tout utilisateur authentifie (comportement acceptable en RH interne).

Headers de securite poses sur chaque reponse :
  - Cache-Control: private, no-store  (pas de mise en cache proxy/CDN)
  - X-Content-Type-Options: nosniff   (pas de sniffing MIME)

Production (Nginx) :
  Activer SYGEPECO_USE_XACCEL = True dans settings.py et configurer Nginx :
    location /protected-media/ {
        internal;
        alias /chemin/vers/media/;
    }
  Django renverra X-Accel-Redirect au lieu d'un FileResponse — Nginx
  sert le fichier directement (efficace) tout en laissant Django controler l'acces.
"""
import logging
import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect

logger = logging.getLogger('SYGEPECO')

# ── Dossiers dont l'acces est limite au role RH ou au proprietaire ────────────
_SENSITIVE_PREFIXES = (
    'conges/documents/',   # justificatifs medicaux
)

# Roles autorises a consulter n'importe quel document sensible
_ROLES_RH = frozenset(('ADMINISTRATEUR', 'DRH', 'RH', 'MANAGER'))

# En-tetes de securite poses sur toutes les reponses media
_SECURITY_HEADERS = {
    'Cache-Control': 'private, no-store',
    'X-Content-Type-Options': 'nosniff',
}


def _get_client_ip(request):
    """Retourne l'IP reelle du client."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '?')


def _has_rh_access(user):
    """Renvoie True si l'utilisateur a un role RH/Admin/Manager."""
    try:
        return user.profile.role in _ROLES_RH
    except AttributeError:
        return False


def _find_conge(rel_path):
    """Recherche le Conge correspondant au chemin du document medical.

    Essaie les deux separateurs (/ et \\) pour compatibilite Windows.

    Args:
        rel_path (str): Chemin relatif sous MEDIA_ROOT.

    Returns:
        Conge | None
    """
    from ..models import Conge
    fwd = rel_path.replace('\\', '/')
    bwd = rel_path.replace('/', '\\')
    try:
        return (
            Conge.objects
            .select_related('contractuel', 'contractuel__entreprise')
            .filter(document_medical__in={fwd, bwd})
            .first()
        )
    except Exception:
        logger.warning(
            'media_serve._find_conge: erreur DB pour path=%s', rel_path,
            exc_info=True,
        )
        return None


def _has_doc_access(user, rel_path):
    """Verifie si l'utilisateur peut acceder a un document medical.

    Acces autorise pour :
      - Le contractuel proprietaire du conge
      - L'entreprise dont l'agent fait partie (role ENTREPRISE)

    Args:
        user: Utilisateur Django authentifie.
        rel_path (str): Chemin relatif du document.

    Returns:
        bool
    """
    conge = _find_conge(rel_path)
    if conge is None:
        return False

    # Agent lui-meme
    if hasattr(user, 'contractuel') and user.contractuel == conge.contractuel:
        return True

    # Entreprise de l'agent
    try:
        if user.profile.role == 'ENTREPRISE':
            ent = user.profile.entreprise
            if ent and conge.contractuel.entreprise_id == ent.pk:
                return True
    except Exception:
        logger.warning(
            'media_serve._has_doc_access: erreur pour user=%s path=%s',
            getattr(user, 'username', '?'), rel_path,
            exc_info=True,
        )
    return False


def _deny(request, message='Acces refuse : document confidentiel.'):
    """Redirige avec message d'erreur selon le role de l'utilisateur.

    Args:
        request: HttpRequest Django.
        message (str): Message d'erreur a afficher.

    Returns:
        HttpResponseRedirect vers l'espace approprie.
    """
    messages.error(request, message)
    if hasattr(request.user, 'contractuel') and request.user.contractuel:
        return redirect('espace_home')
    try:
        if request.user.profile.role == 'ENTREPRISE':
            return redirect('entreprise_espace_conges')
    except AttributeError:
        pass
    return redirect('dashboard')


def _build_response(target, rel_path):
    """Construit la HttpResponse appropriee pour le fichier media.

    En production (SYGEPECO_USE_XACCEL=True dans settings), utilise
    X-Accel-Redirect pour que Nginx serve le fichier directement
    (plus efficace — Django ne lit pas le fichier).

    En developpement, retourne un FileResponse classique.

    Args:
        target (Path): Chemin absolu du fichier.
        rel_path (str): Chemin relatif sous MEDIA_ROOT.

    Returns:
        HttpResponse avec headers de securite.
    """
    content_type, _ = mimetypes.guess_type(str(target))
    content_type = content_type or 'application/octet-stream'

    use_xaccel = getattr(settings, 'SYGEPECO_USE_XACCEL', False)

    if use_xaccel:
        # Nginx lit le fichier depuis l'alias /protected-media/<rel_path>
        # Django ne charge pas le fichier en memoire.
        response = HttpResponse(content_type=content_type)
        response['X-Accel-Redirect'] = '/protected-media/' + rel_path.lstrip('/')
    else:
        response = FileResponse(open(target, 'rb'), content_type=content_type)

    # Headers de securite communs
    for header, value in _SECURITY_HEADERS.items():
        response[header] = value

    return response


@login_required
def protected_media(request, path):
    """Sert les fichiers media uniquement aux utilisateurs authentifies.

    Securite :
      - @login_required : acces refuse aux anonymes (redirect /auth/login/).
      - Protection path traversal : resolution absolue + verification prefixe.
      - Dossiers sensibles (_SENSITIVE_PREFIXES) : role RH ou proprietaire.
      - Headers : Cache-Control: private, no-store + X-Content-Type-Options.
      - Production : X-Accel-Redirect pour Nginx si SYGEPECO_USE_XACCEL=True.

    Args:
        request: HttpRequest Django (utilisateur authentifie).
        path (str): Chemin relatif sous MEDIA_ROOT (capture par <path:path>).

    Returns:
        FileResponse (dev) ou HttpResponse avec X-Accel-Redirect (prod).

    Raises:
        Http404: Fichier absent ou path traversal detecte.
    """
    ip = _get_client_ip(request)

    # ── 1. Protection path traversal ─────────────────────────────────────────
    media_root = Path(settings.MEDIA_ROOT).resolve()
    target = (media_root / path).resolve()
    if not str(target).startswith(str(media_root)):
        logger.warning(
            '[MEDIA] Path traversal tente | user: %s | IP: %s | path: %s',
            request.user.username, ip, path,
        )
        raise Http404

    # ── 2. Existence du fichier ───────────────────────────────────────────────
    if not target.exists() or not target.is_file():
        raise Http404

    # ── 3. Controle acces dossiers sensibles ─────────────────────────────────
    rel = path.replace('\\', '/')
    if any(rel.startswith(prefix) for prefix in _SENSITIVE_PREFIXES):
        if not _has_rh_access(request.user) and not _has_doc_access(request.user, rel):
            logger.warning(
                '[MEDIA] Acces refuse document sensible | user: %s | IP: %s | path: %s',
                request.user.username, ip, rel,
            )
            return _deny(request)
        # Log acces aux documents sensibles (audit trail)
        logger.info(
            '[MEDIA] Acces document sensible autorise | user: %s | IP: %s | path: %s',
            request.user.username, ip, rel,
        )

    return _build_response(target, rel)
