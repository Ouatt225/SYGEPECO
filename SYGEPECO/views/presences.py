"""
Pointage quotidien et rapports de présence mensuel.
Filtrable par date et direction.
"""
from ._base import *
from django.core.paginator import Paginator


@login_required
@rh_required
def presence_list(request):
    """Liste des présences pour une date donnée (aujourd'hui par défaut).

    Paginée à 20 enregistrements par page.
    Les Managers ne voient que leur direction.

    Args:
        request: HttpRequest Django. Paramètre GET `date` (YYYY-MM-DD).

    Returns:
        HttpResponse : template presences/list.html.
"""
    today = date.today()
    date_filtre = request.GET.get('date', str(today))
    try:
        date_filtre = date.fromisoformat(date_filtre)
    except ValueError:
        date_filtre = today
    presences = Presence.objects.filter(date=date_filtre).select_related('contractuel')
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        presences = presences.filter(contractuel__direction=manager_dir)
    paginator = Paginator(presences, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'SYGEPECO/presences/list.html', {
        'presences': page_obj, 'page_obj': page_obj, 'date_filtre': date_filtre,
    })


@login_required
@rh_required
def presence_create(request):
    """Enregistre une présence pour un contractuel.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection.
"""
    form = PresenceForm(request.POST or None)
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        form.fields['contractuel'].queryset = Contractuel.objects.filter(
            direction=manager_dir, statut='ACTIF')
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Presence enregistree pour {obj.contractuel}", 'Presence', obj.pk)
        messages.success(request, "Presence enregistree.")
        return redirect('presence_list')
    return render(request, 'SYGEPECO/presences/form.html', {'form': form})


@login_required
@rh_required
def presence_rapport(request):
    """Rapport de présence mensuel agrégé par contractuel.

    Compte les jours PRESENT/ABSENT/RETARD par agent pour le mois sélectionné.

    Args:
        request: HttpRequest Django. Paramètres GET `mois` et `annee`.

    Returns:
        HttpResponse : template presences/rapport.html.
"""
    today = date.today()
    manager_dir = get_manager_direction(request.user)
    is_manager = manager_dir is not None
    form = RapportFiltreForm(request.GET or {'mois': today.month, 'annee': today.year})
    data = []
    if form.is_valid():
        mois = int(form.cleaned_data['mois'])
        annee = int(form.cleaned_data['annee'])
        dept = form.cleaned_data.get('direction')
        qs = Contractuel.objects.filter(statut='ACTIF')
        if manager_dir:
            qs = qs.filter(direction=manager_dir)
        elif dept:
            qs = qs.filter(direction=dept)
        for c in qs:
            presences = Presence.objects.filter(
                contractuel=c, date__month=mois, date__year=annee)
            data.append({
                'contractuel': c,
                'present': presences.filter(statut='PRESENT').count(),
                'absent': presences.filter(statut='ABSENT').count(),
                'retard': presences.filter(statut='RETARD').count(),
            })
    return render(request, 'SYGEPECO/presences/rapport.html', {
        'form': form, 'data': data,
        'is_manager': is_manager, 'manager_dir': manager_dir,
    })
