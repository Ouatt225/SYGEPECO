import logging

logger = logging.getLogger('SYGEPECO')
from django.shortcuts import redirect


class RoleRoutingMiddleware:
    """
    Redirige automatiquement chaque rôle vers son espace dédié
    si l'utilisateur tente d'accéder à une URL qui ne lui appartient pas.
    """

    # Préfixes autorisés pour chaque rôle
    ALLOWED_PREFIXES = {
        'ENTREPRISE': ('/entreprise-espace/', '/auth/'),
    }

    # URLs toujours accessibles (login, logout, admin, static, media)
    ALWAYS_ALLOWED = ('/auth/', '/admin/', '/static/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            path = request.path
            # Ne pas bloquer les URLs toujours autorisées
            if not any(path.startswith(p) for p in self.ALWAYS_ALLOWED):
                try:
                    role = user.profile.role
                except Exception:  # Superuser ou compte sans UserProfile
                    role = None

                if role == 'ENTREPRISE':
                    if not path.startswith('/entreprise-espace/'):
                        return redirect('entreprise_espace_home')

        return self.get_response(request)
