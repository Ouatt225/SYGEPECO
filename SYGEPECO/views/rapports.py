from ._base import *


@login_required
@rh_required
def calendrier(request):
    return render(request, 'SYGEPECO/calendrier/index.html')


@login_required
@rh_required
def rapports(request):
    today = date.today()
    manager_direction = get_manager_direction(request.user)

    def qs_c():
        qs = Contractuel.objects.filter(statut='ACTIF')
        if manager_direction:
            qs = qs.filter(direction=manager_direction)
        return qs

    def qs_contrat():
        qs = Contrat.objects.filter(statut='EN_COURS')
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    def qs_pres():
        qs = Presence.objects.all()
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    def qs_cg():
        qs = Conge.objects.all()
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    def qs_perm():
        qs = Permission.objects.all()
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    stats_dept = qs_c().values('direction__nom').annotate(total=Count('id')).order_by('-total')
    contrats_par_type = qs_contrat().values('type_contrat__nom').annotate(
        total=Count('id')).order_by('-total')

    context = {
        'stats_dept': list(stats_dept),
        'contrats_par_type': list(contrats_par_type),
        'total_actifs': qs_c().count(),
        'total_contrats': qs_contrat().count(),
        'total_presences_mois': qs_pres().filter(
            date__month=today.month, date__year=today.year).count(),
        'conges_mois': qs_cg().filter(
            date_debut__month=today.month, date_debut__year=today.year).count(),
        'conges_attente': qs_cg().filter(statut='EN_ATTENTE').count(),
        'permissions_mois': qs_perm().filter(
            date_debut__month=today.month, date_debut__year=today.year).count(),
        'permissions_attente': qs_perm().filter(statut='EN_ATTENTE').count(),
        'mois_courant': today.month,
        'annee_courante': today.year,
        'mois_nom': today.strftime('%B %Y'),
        'manager_direction': manager_direction,
    }
    return render(request, 'SYGEPECO/rapports/index.html', context)


@login_required
@rh_required
def rapports_exporter(request):
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))
    direction = get_manager_direction(request.user)
    return export_presences_excel(mois, annee, direction=direction)


@login_required
@rh_required
def rapports_exporter_conges(request):
    mois_param = request.GET.get('mois', '')
    annee_param = request.GET.get('annee', '')
    mois = int(mois_param) if mois_param else None
    annee = int(annee_param) if annee_param else None
    direction = get_manager_direction(request.user)
    return export_conges_excel(mois, annee, direction=direction)


@login_required
@rh_required
def rapports_exporter_permissions(request):
    mois_param = request.GET.get('mois', '')
    annee_param = request.GET.get('annee', '')
    mois = int(mois_param) if mois_param else None
    annee = int(annee_param) if annee_param else None
    direction = get_manager_direction(request.user)
    return export_permissions_excel(mois, annee, direction=direction)


@login_required
@rh_required
def rapports_exporter_contractuels(request):
    direction = get_manager_direction(request.user)
    return export_contractuels_excel(direction=direction)


@login_required
@rh_required
def historique(request):
    logs = ActionLog.objects.select_related('utilisateur').all()[:100]
    return render(request, 'SYGEPECO/historique/index.html', {'logs': logs})
