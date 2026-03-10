"""
Vues d'authentification — connexion, deconnexion, changement de mot de passe.
Redirection intelligente par role apres login.

Rate limiting (implementation manuelle via django.core.cache) :
  - 10 tentatives / 5 min par adresse IP
  - 5 tentatives / 5 min par nom d'utilisateur soumis
Les compteurs sont stockes dans le cache Django (DatabaseCache / Redis).
"""
from django.core.cache import cache
from ._base import *

# ── Parametres de rate limiting ─────────────────────────────────────────────
_RL_WINDOW   = 300   # fenetre de 5 minutes (secondes)
_RL_MAX_IP   = 10    # tentatives max par IP dans la fenetre
_RL_MAX_USER = 5     # tentatives max par username dans la fenetre


def _get_client_ip(request):
    """Retourne l'IP reelle du client (supporte X-Forwarded-For derriere proxy)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _rl_is_blocked(ip, username):
    """Verifie si l'IP ou le username a depasse la limite de tentatives.

    Args:
        ip (str): Adresse IP du client.
        username (str): Nom d'utilisateur soumis dans le formulaire.

    Returns:
        bool: True si acces bloque, False sinon.
    """
    ip_key   = f'rl:login:ip:{ip}'
    user_key = f'rl:login:user:{username.lower()[:64]}'
    ip_count   = cache.get(ip_key,   0)
    user_count = cache.get(user_key, 0)
    return ip_count >= _RL_MAX_IP or user_count >= _RL_MAX_USER


def _rl_record(ip, username):
    """Incrémente les compteurs de tentatives pour cette IP et ce username.

    Initialise le compteur avec TTL si absent, sinon l'incremente.
    DatabaseCache.incr() est suffisamment atomique pour un usage non-concurrent.

    Args:
        ip (str): Adresse IP du client.
        username (str): Nom d'utilisateur soumis dans le formulaire.
    """
    ip_key   = f'rl:login:ip:{ip}'
    user_key = f'rl:login:user:{username.lower()[:64]}'
    for key in (ip_key, user_key):
        if cache.get(key) is None:
            cache.set(key, 1, _RL_WINDOW)
        else:
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, _RL_WINDOW)


def login_view(request):
    """Gere la connexion utilisateur avec redirection par role.

    Protege contre le brute-force :
      - 10 tentatives / 5 min par IP
      - 5 tentatives / 5 min par username

    Apres login reussi :
      - Contractuel (EMPLOYE) -> /espace/
      - Entreprise -> /entreprise-espace/
      - RH/Admin/Manager -> /dashboard/

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire (200/429) ou redirection.
    """
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    ip       = _get_client_ip(request)
    username = request.POST.get('username', '') if request.method == 'POST' else ''

    # ── Verifier le rate limit avant tout traitement ──────────────────────────
    if request.method == 'POST' and _rl_is_blocked(ip, username):
        logger.warning(
            '[RATELIMIT] Login bloque | IP: %s | username: %s',
            ip, username or '?',
        )
        return render(
            request,
            'SYGEPECO/auth/login.html',
            {'form': LoginForm(), 'ratelimited': True},
            status=429,
        )

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_action(user, 'CONNEXION', 'User', user.pk,
                       'Login reussi depuis ' + ip)
            logger.info('[AUTH] Login reussi | user: %s | IP: %s', user.username, ip)
            return redirect_by_role(user)
        else:
            # Tentative echouee : on incremente le compteur
            _rl_record(ip, username)
            logger.warning(
                '[AUTH] Tentative echouee | username: %s | IP: %s',
                username or '?', ip,
            )

    return render(request, 'SYGEPECO/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """Deconnecte l'utilisateur, trace l'action et redirige vers le login.

    Args:
        request: HttpRequest Django (doit etre authentifie).

    Returns:
        HttpResponseRedirect vers /auth/login/.
    """
    ip = _get_client_ip(request)
    log_action(request.user, 'DECONNEXION', 'User', request.user.pk,
               'Logout depuis ' + ip)
    logger.info('[AUTH] Logout | user: %s | IP: %s', request.user.username, ip)
    logout(request)
    return redirect('login')


@login_required
def changer_mot_de_passe(request):
    """Permet a l'utilisateur connecte de changer son mot de passe.

    Met a jour le hash de session pour eviter la deconnexion automatique.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection apres succes.
    """
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a ete modifie avec succes.")
            return redirect_by_role(request.user)
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "SYGEPECO/auth/changer_mot_de_passe.html", {"form": form})
