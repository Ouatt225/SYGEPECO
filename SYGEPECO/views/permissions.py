"""
Gestion des permissions d'absence courte durée.
Workflow : EN_ATTENTE → APPROUVE/REJETE par RH ou Entreprise.
"""
from ._base import *
from django.core.paginator import Paginator


@login_required
@rh_required
def permission_list(request):
    """Liste des permissions filtrée selon le rôle.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : template permissions/list.html.
"""
    statut = request.GET.get('statut', '')
    qs = Permission.objects.select_related('contractuel', 'approuve_par').all()
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        qs = qs.filter(contractuel__direction=manager_dir)
    if statut:
        qs = qs.filter(statut=statut)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'SYGEPECO/permissions/list.html', {'permissions': page_obj, 'page_obj': page_obj, 'statut': statut})


@login_required
@rh_required
def permission_detail(request, pk):
    """Détail d'une demande de permission.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire de la permission.

    Returns:
        HttpResponse : template permissions/detail.html.
"""
    perm = get_object_or_404(Permission, pk=pk)
    return render(request, 'SYGEPECO/permissions/detail.html', {'permission': perm})


@login_required
@rh_required
def permission_create(request):
    """Crée une demande de permission (par le RH pour un agent).

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection.
"""
    form = PermissionForm(request.POST or None)
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        form.fields['contractuel'].queryset = Contractuel.objects.filter(
            direction=manager_dir, statut='ACTIF')
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Demande de permission pour {obj.contractuel}", 'Permission', obj.pk)
        messages.success(request, "Demande de permission soumise.")
        return redirect('permission_list')
    return render(request, 'SYGEPECO/permissions/form.html', {'form': form})



def _perm_rh_decision(request, pk):
    """Charge la permission et verifie l'acces manager. Retourne (perm, None) ou (None, redirect)."""
    perm = get_object_or_404(Permission, pk=pk)
    manager_dir = get_manager_direction(request.user)
    if manager_dir and perm.contractuel.direction != manager_dir:
        messages.error(request, "Vous ne pouvez pas traiter cette permission : hors de votre direction.")
        return None, redirect('permission_detail', pk=pk)
    return perm, None

@login_required
@rh_required
def permission_approuver(request, pk):
    """Approuve une permission (RH/DRH).

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire de la permission.

    Returns:
        HttpResponseRedirect vers la liste.
"""
    perm, err = _perm_rh_decision(request, pk)
    if err: return err
    form = PermissionDecisionForm(request.POST or None, instance=perm)
    if request.method == 'POST' and form.is_valid():
        perm.statut = 'APPROUVE'
        perm.approuve_par = request.user
        perm.save()
        log_action(request.user, f"Permission approuvee pour {perm.contractuel}", 'Permission', perm.pk)
        messages.success(request, "Permission approuvee.")
        return redirect('permission_detail', pk=pk)
    return render(request, 'SYGEPECO/permissions/decision.html',
                  {'permission': perm, 'form': form, 'action': 'approuver'})


@login_required
@rh_required
def permission_rejeter(request, pk):
    """Rejette une permission avec motif (RH/DRH).

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire de la permission.

    Returns:
        HttpResponseRedirect vers la liste.
"""
    perm, err = _perm_rh_decision(request, pk)
    if err: return err
    form = PermissionDecisionForm(request.POST or None, instance=perm)
    if request.method == 'POST' and form.is_valid():
        perm.statut = 'REJETE'
        perm.approuve_par = request.user
        perm.save()
        log_action(request.user, f"Permission rejetee pour {perm.contractuel}", 'Permission', perm.pk)
        messages.warning(request, "Permission rejetee.")
        return redirect('permission_detail', pk=pk)
    return render(request, 'SYGEPECO/permissions/decision.html',
                  {'permission': perm, 'form': form, 'action': 'rejeter'})


@login_required
def entreprise_permission_approuver(request, pk):
    """Approuve une permission depuis l'espace Entreprise.

    Vérifie que la permission concerne un agent de l'entreprise.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire de la permission.

    Returns:
        HttpResponseRedirect vers la liste entreprise.
"""
    ent, err = ent_check(request)
    if err: return err
    perm = get_object_or_404(Permission, pk=pk)
    if ent and perm.contractuel.entreprise != ent:
        messages.error(request, "Acces refuse : cette permission n'appartient pas a votre entreprise.")
        return redirect('entreprise_espace_permissions')
    if perm.statut != 'EN_ATTENTE':
        messages.warning(request, "Cette permission ne peut pas etre approuvee.")
        return redirect('entreprise_espace_permissions')
    perm.statut = 'APPROUVE'
    perm.approuve_par = request.user
    perm.save()
    log_action(request.user, f"Permission approuvee (entreprise) pour {perm.contractuel}", 'Permission', perm.pk)
    messages.success(request, "Permission approuvee.")
    return redirect('entreprise_espace_permissions')


@login_required
def entreprise_permission_rejeter(request, pk):
    """Rejette une permission depuis l'espace Entreprise.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire de la permission.

    Returns:
        HttpResponseRedirect vers la liste entreprise.
"""
    ent, err = ent_check(request)
    if err: return err
    perm = get_object_or_404(Permission, pk=pk)
    if ent and perm.contractuel.entreprise != ent:
        messages.error(request, "Acces refuse : cette permission n'appartient pas a votre entreprise.")
        return redirect('entreprise_espace_permissions')
    if perm.statut != 'EN_ATTENTE':
        messages.warning(request, "Cette permission ne peut pas etre rejetee.")
        return redirect('entreprise_espace_permissions')
    perm.statut = 'REJETE'
    perm.approuve_par = request.user
    perm.save()
    log_action(request.user, f"Permission rejetee (entreprise) pour {perm.contractuel}", 'Permission', perm.pk)
    messages.warning(request, "Permission rejetee.")
    return redirect('entreprise_espace_permissions')
