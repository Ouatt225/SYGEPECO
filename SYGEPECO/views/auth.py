"""
Vues d'authentification — connexion, déconnexion, changement de mot de passe.
Redirection intelligente par rôle après login.
"""
from ._base import *


def login_view(request):
    """Gère la connexion utilisateur avec redirection par rôle.

    Redirige les utilisateurs déjà connectés vers leur espace.
    Après login :
      - Contractuel (EMPLOYE) → /espace/
      - Entreprise → /entreprise-espace/
      - RH/Admin/Manager → /dashboard/

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire de login ou redirection.
"""
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect_by_role(user)
    return render(request, "SYGEPECO/auth/login.html", {"form": form})


@login_required
def logout_view(request):
    """Déconnecte l'utilisateur et redirige vers la page de login.

    Args:
        request: HttpRequest Django (doit être authentifié).

    Returns:
        HttpResponseRedirect vers /auth/login/.
"""
    logout(request)
    return redirect("login")



@login_required
def changer_mot_de_passe(request):
    """Permet à l'utilisateur connecté de changer son mot de passe.

    Met à jour le hash de session pour éviter la déconnexion automatique.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection après succès.
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
