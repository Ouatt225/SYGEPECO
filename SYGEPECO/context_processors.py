from datetime import date, timedelta
from .models import Conge, Permission, Contractuel, ActionLog


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    today = date.today()
    conges_attente = Conge.objects.filter(statut='EN_ATTENTE').count()
    permissions_attente = Permission.objects.filter(statut='EN_ATTENTE').count()
    total_notifications = conges_attente + permissions_attente

    # Anniversaires dans 7 jours
    anniversaires_proches = []
    for c in Contractuel.objects.filter(statut='ACTIF'):
        try:
            anniv = c.date_naissance.replace(year=today.year)
        except ValueError:
            anniv = c.date_naissance.replace(year=today.year, day=28)
        delta = (anniv - today).days
        if 0 <= delta <= 7:
            anniversaires_proches.append({'contractuel': c, 'jours': delta})

    return {
        'conges_attente_count': conges_attente,
        'permissions_attente_count': permissions_attente,
        'total_notifications': total_notifications,
        'anniversaires_proches': anniversaires_proches[:3],
    }
