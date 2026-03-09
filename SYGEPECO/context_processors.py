from datetime import date, timedelta
from django.db.models import Q
from django.db.models.functions import ExtractMonth, ExtractDay
from .models import Conge, Permission, Contractuel
from .utils import get_manager_direction


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    today = date.today()
    manager_direction = get_manager_direction(request.user)

    # Requêtes de base — filtrées par direction si l'utilisateur est Manager
    qs_conges       = Conge.objects.filter(statut='EN_ATTENTE')
    qs_permissions  = Permission.objects.filter(statut='EN_ATTENTE')
    qs_contractuels = Contractuel.objects.filter(statut='ACTIF')

    if manager_direction:
        qs_conges      = qs_conges.filter(contractuel__direction=manager_direction)
        qs_permissions = qs_permissions.filter(contractuel__direction=manager_direction)
        qs_contractuels = qs_contractuels.filter(direction=manager_direction)

    conges_attente     = qs_conges.count()
    permissions_attente = qs_permissions.count()

    # Anniversaires dans 7 jours — requête SQL annotée (remplace l'ancienne boucle Python)
    _end = today + timedelta(days=7)
    _anniv_qs = qs_contractuels.filter(date_naissance__isnull=False).annotate(
        birth_month=ExtractMonth('date_naissance'),
        birth_day=ExtractDay('date_naissance'),
    )

    if _end.month == today.month:
        # Fenêtre dans le même mois
        _anniv_qs = _anniv_qs.filter(
            birth_month=today.month,
            birth_day__gte=today.day,
            birth_day__lte=_end.day,
        )
    else:
        # Chevauchement de deux mois (ex : 28 janv → 4 févr, ou 29 déc → 5 janv)
        _anniv_qs = _anniv_qs.filter(
            Q(birth_month=today.month, birth_day__gte=today.day) |
            Q(birth_month=_end.month,  birth_day__lte=_end.day)
        )

    # Calcul du delta en Python — sur le petit sous-ensemble déjà filtré en base
    anniversaires_proches = []
    for c in _anniv_qs:
        try:
            anniv = c.date_naissance.replace(year=today.year)
        except ValueError:                          # 29 fév sur année non-bissextile
            anniv = c.date_naissance.replace(year=today.year, day=28)
        delta = (anniv - today).days
        if delta < 0:
            try:
                anniv = c.date_naissance.replace(year=today.year + 1)
            except ValueError:
                anniv = c.date_naissance.replace(year=today.year + 1, day=28)
            delta = (anniv - today).days
        anniversaires_proches.append({'contractuel': c, 'jours': delta})

    anniversaires_proches.sort(key=lambda x: x['jours'])

    return {
        'conges_attente_count':     conges_attente,
        'permissions_attente_count': permissions_attente,
        'total_notifications':       conges_attente + permissions_attente,
        'anniversaires_proches':     anniversaires_proches[:3],
    }
