"""
Vue principale du tableau de bord RH.
Calcule les KPIs en temps réel : effectifs, présences, congés, alertes contrats.
"""
from ._base import *


@login_required
@rh_required
def dashboard(request):
    """Tableau de bord principal — KPIs et alertes RH.

    Calcule en temps réel (filtré par direction pour les Managers) :
      - Effectif actif / total
      - Présences et taux d'assiduité du jour
      - Congés et permissions EN_ATTENTE
      - Anniversaires dans les 30 prochains jours
      - Contrats expirant dans les 30 prochains jours

    Accès : @login_required + rôles RH/Admin/Manager.

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : template dashboard/index.html.
"""
    today = date.today()
    manager_direction = get_manager_direction(request.user)

    def qs_contractuels():
        qs = Contractuel.objects.filter(statut='ACTIF')
        if manager_direction:
            qs = qs.filter(direction=manager_direction)
        return qs

    def qs_presences():
        qs = Presence.objects.filter(date=today)
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    def qs_conges():
        qs = Conge.objects.all()
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    def qs_permissions():
        qs = Permission.objects.all()
        if manager_direction:
            qs = qs.filter(contractuel__direction=manager_direction)
        return qs

    total_actifs = qs_contractuels().count()
    presences_today = qs_presences().filter(statut='PRESENT').count()
    absents_today = qs_presences().filter(statut='ABSENT').count()
    conges_attente = qs_conges().filter(statut='EN_ATTENTE').count()
    permissions_attente = qs_permissions().filter(statut='EN_ATTENTE').count()
    en_conge_today = qs_conges().filter(
        statut='APPROUVE', date_debut__lte=today, date_fin__gte=today).count()
    en_permission_today = qs_permissions().filter(
        statut='APPROUVE', date_debut__lte=today, date_fin__gte=today).count()

    # Filtre SQL : uniquement les agents dont l'anniversaire tombe dans les 30 prochains jours
    _end = today + timedelta(days=30)
    _anniv_qs = qs_contractuels().filter(date_naissance__isnull=False).annotate(
        birth_month=ExtractMonth('date_naissance'),
        birth_day=ExtractDay('date_naissance'),
    )
    if _end.year == today.year:
        if _end.month == today.month:
            _anniv_qs = _anniv_qs.filter(
                birth_month=today.month,
                birth_day__gte=today.day,
                birth_day__lte=_end.day,
            )
        else:
            _anniv_qs = _anniv_qs.filter(
                Q(birth_month=today.month, birth_day__gte=today.day) |
                Q(birth_month__gt=today.month, birth_month__lt=_end.month) |
                Q(birth_month=_end.month, birth_day__lte=_end.day)
            )
    else:
        # Franchissement d'année (ex : 15 déc → 14 jan)
        _anniv_qs = _anniv_qs.filter(
            Q(birth_month=today.month, birth_day__gte=today.day) |
            Q(birth_month__gt=today.month) |
            Q(birth_month__lt=_end.month) |
            Q(birth_month=_end.month, birth_day__lte=_end.day)
        )
    # Calcul du delta en Python — sur un petit sous-ensemble déjà filtré en base
    anniversaires = []
    for c in _anniv_qs:
        try:
            anniv_date = c.date_naissance.replace(year=today.year)
        except ValueError:
            anniv_date = c.date_naissance.replace(year=today.year, day=28)
        delta = (anniv_date - today).days
        if delta < 0:
            # Anniversaire déjà passé cette année → prendre l'an prochain
            try:
                anniv_date = c.date_naissance.replace(year=today.year + 1)
            except ValueError:
                anniv_date = c.date_naissance.replace(year=today.year + 1, day=28)
            delta = (anniv_date - today).days
        anniversaires.append({'contractuel': c, 'jours': delta, 'date': anniv_date})
    anniversaires.sort(key=lambda x: x['jours'])

    contrats_expirer_qs = Contrat.objects.filter(
        statut='EN_COURS',
        date_fin__range=[today, today + timedelta(days=30)]
    ).select_related('contractuel')
    if manager_direction:
        contrats_expirer_qs = contrats_expirer_qs.filter(
            contractuel__direction=manager_direction)

    taux_presence = round(
        (presences_today / total_actifs * 100) if total_actifs else 0, 1)
    alertes_conges = build_alertes_conges(qs_conges(), today)

    context = {
        'total_actifs': total_actifs,
        'presences_today': presences_today,
        'conges_attente': conges_attente,
        'permissions_attente': permissions_attente,
        'en_conge_today': en_conge_today,
        'en_permission_today': en_permission_today,
        'absents_today': absents_today,
        'taux_presence': taux_presence,
        'anniversaires': anniversaires[:5],
        'contrats_expirer': contrats_expirer_qs[:5],
        'today': today,
        'manager_direction': manager_direction,
        'alertes_conges': alertes_conges,
    }
    return render(request, 'SYGEPECO/dashboard/index.html', context)
