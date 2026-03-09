from ._base import *


@login_required
@rh_required
def api_dashboard_stats(request):
    today = date.today()
    return JsonResponse({
        'total_actifs': Contractuel.objects.filter(statut='ACTIF').count(),
        'presences_today': Presence.objects.filter(date=today, statut='PRESENT').count(),
        'conges_attente': Conge.objects.filter(statut='EN_ATTENTE').count(),
        'permissions_attente': Permission.objects.filter(statut='EN_ATTENTE').count(),
    })


@login_required
@rh_required
def api_calendrier_events(request):
    events = []
    for c in Conge.objects.filter(statut='APPROUVE').select_related('contractuel'):
        events.append({
            'title': f"Conge — {c.contractuel.get_full_name()}",
            'start': str(c.date_debut),
            'end': str(c.date_fin + timedelta(days=1)),
            'color': '#22C55E',
            'type': 'conge',
        })
    for p in Permission.objects.filter(statut='APPROUVE').select_related('contractuel'):
        events.append({
            'title': f"Permission — {p.contractuel.get_full_name()}",
            'start': str(p.date_debut),
            'end': str(p.date_fin),
            'color': '#4A6CF7',
            'type': 'permission',
        })
    return JsonResponse({'events': events})


@login_required
@rh_required
def api_chart_presences(request):
    today = date.today()
    labels, presents, absents = [], [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%d/%m'))
        presents.append(Presence.objects.filter(date=d, statut='PRESENT').count())
        absents.append(Presence.objects.filter(date=d, statut='ABSENT').count())
    return JsonResponse({'labels': labels, 'presents': presents, 'absents': absents})


@login_required
def api_postes_entreprise(request):
    entreprise_id = request.GET.get('entreprise_id')
    if not entreprise_id:
        postes = Poste.objects.select_related('direction').all().order_by('titre')
    else:
        poste_ids = Contractuel.objects.filter(
            entreprise_id=entreprise_id
        ).values_list('poste_id', flat=True).distinct()
        postes = Poste.objects.filter(id__in=poste_ids).select_related('direction').order_by('titre')
        if not postes.exists():
            postes = Poste.objects.select_related('direction').all().order_by('titre')
    data = [{'id': p.id, 'titre': p.titre,
             'direction_id': p.direction_id, 'direction_nom': p.direction.nom}
            for p in postes]
    return JsonResponse({'postes': data})


@login_required
def api_conges_notifs(request):
    # Retourne les conges approuves debutant dans 1 ou 7 jours pour l utilisateur courant.
    from datetime import date, timedelta
    today = date.today()
    in_7  = today + timedelta(days=7)
    in_1  = today + timedelta(days=1)

    qs = Conge.objects.filter(
        statut='APPROUVE',
        date_debut__in=[in_7, in_1],
    ).select_related('contractuel', 'contractuel__entreprise')

    try:
        role = request.user.profile.role if hasattr(request.user, 'profile') else 'NONE'
    except Exception:
        role = 'NONE'

    if role in ('ADMINISTRATEUR', 'DRH', 'RH'):
        pass  # voit tout
    elif role == 'MANAGER':
        manager_dir = get_manager_direction(request.user)
        if manager_dir:
            qs = qs.filter(contractuel__direction=manager_dir)
        else:
            qs = qs.none()
    elif role == 'ENTREPRISE':
        try:
            ent = request.user.profile.entreprise
            if ent:
                qs = qs.filter(contractuel__entreprise=ent)
        except Exception:
            qs = qs.none()
    else:
        # Agent : uniquement son propre congé
        try:
            if hasattr(request.user, 'contractuel') and request.user.contractuel:
                qs = qs.filter(contractuel=request.user.contractuel)
            else:
                qs = qs.none()
        except Exception:
            qs = qs.none()

    data = []
    for cg in qs:
        days_until = (cg.date_debut - today).days
        data.append({
            'id':         cg.pk,
            'key':        f"{cg.pk}_{days_until}",
            'agent':      cg.contractuel.get_full_name(),
            'type_conge': cg.get_type_conge_display(),
            'date_debut': cg.date_debut.strftime('%d/%m/%Y'),
            'days_until': days_until,
        })
    return JsonResponse({'notifications': data})

