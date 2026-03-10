"""
CRUD complet des fiches contractuels.
Respecte le périmètre Manager (direction uniquement) et permet l'export PDF.
"""
import os as _os
from io import BytesIO
from ._base import *
from django.core.paginator import Paginator
from ..utils import build_fiche_pdf


@login_required
@rh_required
def contractuel_list(request):
    """Liste paginée des contractuels avec recherche et filtres.

    Filtres disponibles : recherche texte (nom/prénom/matricule),
    direction, statut (ACTIF/INACTIF/SUSPENDU).
    Les Managers ne voient que leur direction.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : 15 contractuels par page.
"""
    q = request.GET.get('q', '')
    dept = request.GET.get('direction', '')
    statut = request.GET.get('statut', '')
    qs = Contractuel.objects.select_related('poste', 'direction').all()
    manager_direction = get_manager_direction(request.user)
    is_manager = manager_direction is not None
    if manager_direction:
        qs = qs.filter(direction=manager_direction)
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(matricule__icontains=q))
    if dept and not is_manager:
        qs = qs.filter(direction__id=dept)
    if statut:
        qs = qs.filter(statut=statut)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'SYGEPECO/contractuels/list.html', {
        'contractuels': page_obj, 'page_obj': page_obj,
        'directions': Direction.objects.all(),
        'q': q, 'dept': dept, 'statut': statut,
        'is_manager': is_manager, 'manager_direction': manager_direction,
    })


@login_required
@rh_required
def contractuel_detail(request, pk):
    """Fiche détaillée d'un contractuel avec ses données associées.

    Charge en une requête : contrats, présences récentes, congés, permissions.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du contractuel.

    Returns:
        HttpResponse : template contractuels/detail.html.
"""
    # select_related evite N+1 sur poste, direction et entreprise
    c = get_object_or_404(
        Contractuel.objects.select_related('poste', 'direction', 'entreprise'),
        pk=pk,
    )
    return render(request, 'SYGEPECO/contractuels/detail.html', {
        'contractuel': c,
        # select_related sur type_contrat et created_by : 1 requete avec JOIN
        'contrats': c.contrats.select_related('type_contrat', 'created_by')
                               .order_by('-created_at'),
        # Slicing dans le queryset (LIMIT en SQL) et non en Python
        'presences': c.presences.order_by('-date')[:10],
        # select_related sur approuve_par et valide_par_manager
        'conges': c.conges.select_related('approuve_par', 'valide_par_manager')
                           .order_by('-created_at')[:5],
        'permissions': c.permissions.select_related('approuve_par')
                                    .order_by('-created_at')[:5],
    })


@login_required
@rh_required
def contractuel_create(request):
    """Crée un nouveau contractuel.

    Valide le formulaire incluant la photo (vérification MIME).
    Enregistre l'action dans ActionLog.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection vers la fiche créée.
"""
    form = ContractuelForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Creation du contractuel {obj}", 'Contractuel', obj.pk)
        messages.success(request, f"Contractuel {obj.get_full_name()} cree.")
        return redirect('contractuel_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contractuels/form.html',
                  {'form': form, 'titre': 'Nouveau Contractuel'})


@login_required
@rh_required
def contractuel_update(request, pk):
    """Modifie un contractuel existant.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du contractuel.

    Returns:
        HttpResponse : formulaire pré-rempli ou redirection.
"""
    obj = get_object_or_404(Contractuel, pk=pk)
    form = ContractuelForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        log_action(request.user, f"Modification du contractuel {obj}", 'Contractuel', obj.pk)
        messages.success(request, "Contractuel mis a jour.")
        return redirect('contractuel_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contractuels/form.html',
                  {'form': form, 'titre': 'Modifier le Contractuel', 'obj': obj})


@login_required
@rh_required
def contractuel_delete(request, pk):
    """Supprime un contractuel (POST uniquement).

    Enregistre la suppression dans ActionLog avant de supprimer.

    Args:
        request: HttpRequest Django (POST requis).
        pk (int): Clé primaire du contractuel.

    Returns:
        HttpResponseRedirect vers la liste.
"""
    obj = get_object_or_404(Contractuel, pk=pk)
    if request.method == 'POST':
        nom = obj.get_full_name()
        log_action(request.user, f"Suppression du contractuel {obj}", 'Contractuel', obj.pk)
        obj.delete()
        messages.success(request, f"Contractuel {nom} supprime.")
        return redirect('contractuel_list')
    return render(request, 'SYGEPECO/contractuels/confirm_delete.html', {'obj': obj})


@login_required
@rh_required
def telecharger_profil_agent(request, pk):
    """Génère et télécharge la fiche PDF d'un contractuel.

    Contrôle d'accès : les Managers ne peuvent exporter que leur direction.
    Utilise build_fiche_pdf() de utils.py (ReportLab).

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du contractuel.

    Returns:
        FileResponse : PDF en attachment.
"""
    from django.http import Http404
    c = get_object_or_404(Contractuel, pk=pk)
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else 'ADMINISTRATEUR'
    if role == 'MANAGER':
        direction = getattr(profile, 'direction', None)
        if not direction or c.direction != direction:
            raise Http404
    elif role == 'ENTREPRISE':
        ent = get_entreprise_for_user(request.user)
        if not ent or c.entreprise != ent:
            raise Http404
    buf = build_fiche_pdf(c)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="Fiche_{c.nom}_{c.prenom}.pdf"'
    return resp
