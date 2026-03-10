"""
CRUD des contrats de travail (CDI, CDD, Stage, Prestation).
Inclut le renouvellement automatique avec transfert des données.
"""
from ._base import *
from django.core.paginator import Paginator


@login_required
@rh_required
def contrat_list(request):
    """Liste paginée des contrats de travail.

    Filtrable par statut (EN_COURS, EXPIRE, RESILIE, RENOUVELE).

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : 15 contrats par page.
"""
    qs = Contrat.objects.select_related('contractuel', 'type_contrat').all()
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        qs = qs.filter(contractuel__direction=manager_dir)
    statut = request.GET.get('statut', '')
    if statut:
        qs = qs.filter(statut=statut)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'SYGEPECO/contrats/list.html', {'contrats': page_obj, 'page_obj': page_obj, 'statut': statut})


@login_required
@rh_required
def contrat_detail(request, pk):
    """Détail d'un contrat de travail.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du contrat.

    Returns:
        HttpResponse : template contrats/detail.html.
"""
    contrat = get_object_or_404(Contrat, pk=pk)
    return render(request, 'SYGEPECO/contrats/detail.html', {'contrat': contrat})


@login_required
@rh_required
def contrat_create(request):
    """Crée un nouveau contrat lié à un contractuel.

    Sauvegarde created_by = utilisateur connecté. Log l'action.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection.
"""
    form = ContratForm(request.POST or None)
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        form.fields['contractuel'].queryset = Contractuel.objects.filter(
            direction=manager_dir, statut='ACTIF')
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        log_action(request.user, f"Nouveau contrat pour {obj.contractuel}", 'Contrat', obj.pk)
        messages.success(request, "Contrat cree avec succes.")
        return redirect('contrat_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contrats/form.html',
                  {'form': form, 'titre': 'Nouveau Contrat'})


@login_required
@rh_required
def contrat_update(request, pk):
    """Modifie un contrat existant.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du contrat.

    Returns:
        HttpResponse : formulaire pré-rempli ou redirection.
"""
    obj = get_object_or_404(Contrat, pk=pk)
    form = ContratForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        log_action(request.user, f"Modification contrat {obj}", 'Contrat', obj.pk)
        messages.success(request, "Contrat mis a jour.")
        return redirect('contrat_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contrats/form.html',
                  {'form': form, 'titre': 'Modifier le Contrat', 'obj': obj})


@login_required
@rh_required
def contrat_renouveler(request, pk):
    """Renouvelle un contrat expirant.

    Passe l'ancien contrat à statut RENOUVELE.
    Crée un nouveau contrat pré-rempli avec les données de l'ancien.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du contrat à renouveler.

    Returns:
        HttpResponse : formulaire pré-rempli pour le nouveau contrat.
"""
    ancien = get_object_or_404(Contrat, pk=pk)
    if request.method == 'POST':
        form = ContratForm(request.POST)
        if form.is_valid():
            ancien.statut = 'RENOUVELE'
            ancien.save()
            nouveau = form.save(commit=False)
            nouveau.created_by = request.user
            nouveau.save()
            log_action(request.user, f"Renouvellement contrat {ancien}", 'Contrat', nouveau.pk)
            messages.success(request, "Contrat renouvele avec succes.")
            return redirect('contrat_detail', pk=nouveau.pk)
    else:
        initial = {
            'contractuel': ancien.contractuel,
            'type_contrat': ancien.type_contrat,
            'salaire': ancien.salaire,
            'date_debut': ancien.date_fin + timedelta(days=1) if ancien.date_fin else date.today(),
        }
        form = ContratForm(initial=initial)
    return render(request, 'SYGEPECO/contrats/form.html', {
        'form': form, 'titre': 'Renouveler le Contrat', 'ancien': ancien
    })
