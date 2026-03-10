from datetime import date, timedelta
from django.core.cache import cache
from django.db.models import Q
from django.db.models.functions import ExtractMonth, ExtractDay
from .models import Conge, Permission, Contractuel
from .utils import get_manager_direction

# Durées de cache
_TTL_COUNTS  = 120       # 2 min  — compteurs de notifications (quasi temps-réel)
_TTL_ANNIVS  = 3_600     # 1 h    — anniversaires (stables dans la journée)


def global_context(request):
    if not request.user.is_authenticated:
        return {}

    today             = date.today()
    manager_direction = get_manager_direction(request.user)
    dir_pk            = manager_direction.pk if manager_direction else 0

    # ── Cache des compteurs (conges + permissions EN_ATTENTE) ────────────
    counts_key = f'ctx_counts_{request.user.pk}_{dir_pk}'
    counts     = cache.get(counts_key)

    if counts is None:
        qs_conges      = Conge.objects.filter(statut='EN_ATTENTE')
        qs_permissions = Permission.objects.filter(statut='EN_ATTENTE')
        if manager_direction:
            qs_conges      = qs_conges.filter(contractuel__direction=manager_direction)
            qs_permissions = qs_permissions.filter(contractuel__direction=manager_direction)

        counts = {
            'conges_attente_count':      qs_conges.count(),
            'permissions_attente_count': qs_permissions.count(),
        }
        counts['total_notifications'] = (
            counts['conges_attente_count'] + counts['permissions_attente_count']
        )
        cache.set(counts_key, counts, _TTL_COUNTS)

    # ── Cache des anniversaires (stable dans la journée) ─────────────────
    anniv_key = f'ctx_annivs_{request.user.pk}_{dir_pk}_{today.isoformat()}'
    anniversaires_proches = cache.get(anniv_key)

    if anniversaires_proches is None:
        qs_contractuels = Contractuel.objects.filter(statut='ACTIF')
        if manager_direction:
            qs_contractuels = qs_contractuels.filter(direction=manager_direction)

        _end      = today + timedelta(days=7)
        _anniv_qs = qs_contractuels.filter(date_naissance__isnull=False).annotate(
            birth_month=ExtractMonth('date_naissance'),
            birth_day=ExtractDay('date_naissance'),
        )

        if _end.month == today.month:
            _anniv_qs = _anniv_qs.filter(
                birth_month=today.month,
                birth_day__gte=today.day,
                birth_day__lte=_end.day,
            )
        else:
            _anniv_qs = _anniv_qs.filter(
                Q(birth_month=today.month, birth_day__gte=today.day) |
                Q(birth_month=_end.month,  birth_day__lte=_end.day)
            )

        anniversaires_proches = []
        for c in _anniv_qs:
            try:
                anniv = c.date_naissance.replace(year=today.year)
            except ValueError:
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
        anniversaires_proches = anniversaires_proches[:3]

        # On ne cache PAS les objets ORM directement (ils ne sont pas sérialisables
        # de façon fiable en mémoire entre process). On cache uniquement les données
        # simples et on reconstruit si nécessaire.
        # Pour la mémoire locale (LocMemCache, défaut Django), les objets Python
        # sont stockés tels quels — c'est safe en développement et sur un serveur
        # mono-process. Sur multi-process (gunicorn), utiliser Redis.
        cache.set(anniv_key, anniversaires_proches, _TTL_ANNIVS)

    return {
        **counts,
        'anniversaires_proches': anniversaires_proches,
    }
