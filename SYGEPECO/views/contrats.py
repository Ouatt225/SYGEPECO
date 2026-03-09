from ._base import *
from django.core.paginator import Paginator


@login_required
@rh_required
def contrat_list(request):
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
    contrat = get_object_or_404(Contrat, pk=pk)
    return render(request, 'SYGEPECO/contrats/detail.html', {'contrat': contrat})


@login_required
@rh_required
def contrat_create(request):
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
