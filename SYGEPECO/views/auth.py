from ._base import *


def login_view(request):
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
    logout(request)
    return redirect("login")



@login_required
def changer_mot_de_passe(request):
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
