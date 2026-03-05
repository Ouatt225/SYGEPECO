import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Contractuel, Contrat, Presence, Conge, Permission,
    Departement, Poste, TypeContrat, ActionLog, UserProfile, Entreprise
)
from .forms import (
    LoginForm, ContractuelForm, ContratForm, PresenceForm,
    CongeForm, CongeDecisionForm, PermissionForm, PermissionDecisionForm, RapportFiltreForm,
    EspaceProfilForm, EspaceCongeForm, EspacePermissionForm,
)
from .utils import log_action, export_presences_excel, export_conges_excel, export_permissions_excel, export_contractuels_excel
from .decorators import contractuel_required, rh_required


# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────

def _redirect_by_role(user):
    """Retourne la bonne URL de redirection selon le rôle de l'utilisateur."""
    if hasattr(user, 'contractuel') and user.contractuel is not None:
        return redirect('espace_home')
    if hasattr(user, 'profile') and user.profile.role == 'ENTREPRISE':
        return redirect('entreprise_espace_home')
    return redirect('dashboard')


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return _redirect_by_role(user)
    return render(request, 'SYGEPECO/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = date.today()
    total_actifs = Contractuel.objects.filter(statut='ACTIF').count()
    presences_today = Presence.objects.filter(date=today, statut='PRESENT').count()
    conges_attente = Conge.objects.filter(statut='EN_ATTENTE').count()
    permissions_attente = Permission.objects.filter(statut='EN_ATTENTE').count()
    en_conge_today = Conge.objects.filter(
        statut='APPROUVE', date_debut__lte=today, date_fin__gte=today
    ).count()
    en_permission_today = Permission.objects.filter(
        statut='APPROUVE', date=today
    ).count()
    absents_today = Presence.objects.filter(date=today, statut='ABSENT').count()

    # Alertes anniversaires (30 prochains jours)
    anniversaires = []
    for c in Contractuel.objects.filter(statut='ACTIF'):
        try:
            anniv = c.date_naissance.replace(year=today.year)
        except ValueError:
            anniv = c.date_naissance.replace(year=today.year, day=28)
        delta = (anniv - today).days
        if 0 <= delta <= 30:
            anniversaires.append({'contractuel': c, 'jours': delta, 'date': anniv})
    anniversaires.sort(key=lambda x: x['jours'])

    # Contrats expirant dans 30 jours
    contrats_expirer = Contrat.objects.filter(
        statut='EN_COURS',
        date_fin__range=[today, today + timedelta(days=30)]
    ).select_related('contractuel')

    taux_presence = round((presences_today / total_actifs * 100) if total_actifs else 0, 1)

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
        'contrats_expirer': contrats_expirer[:5],
        'today': today,
    }
    return render(request, 'SYGEPECO/dashboard/index.html', context)


# ─────────────────────────────────────────────────────────────
# CONTRACTUELS
# ─────────────────────────────────────────────────────────────

@login_required
def contractuel_list(request):
    q = request.GET.get('q', '')
    dept = request.GET.get('departement', '')
    statut = request.GET.get('statut', '')
    qs = Contractuel.objects.select_related('poste', 'departement').all()
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(matricule__icontains=q))
    if dept:
        qs = qs.filter(departement__id=dept)
    if statut:
        qs = qs.filter(statut=statut)
    departements = Departement.objects.all()
    return render(request, 'SYGEPECO/contractuels/list.html', {
        'contractuels': qs,
        'departements': departements,
        'q': q, 'dept': dept, 'statut': statut,
    })


@login_required
def contractuel_detail(request, pk):
    c = get_object_or_404(Contractuel, pk=pk)
    contrats = c.contrats.all()
    presences = c.presences.all()[:10]
    conges = c.conges.all()[:5]
    permissions = c.permissions.all()[:5]
    return render(request, 'SYGEPECO/contractuels/detail.html', {
        'contractuel': c,
        'contrats': contrats,
        'presences': presences,
        'conges': conges,
        'permissions': permissions,
    })


@login_required
def contractuel_create(request):
    form = ContractuelForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Création du contractuel {obj}", 'Contractuel', obj.pk)
        messages.success(request, f"Contractuel {obj.get_full_name()} créé avec succès.")
        return redirect('contractuel_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contractuels/form.html', {'form': form, 'titre': 'Nouveau Contractuel'})


@login_required
def contractuel_update(request, pk):
    obj = get_object_or_404(Contractuel, pk=pk)
    form = ContractuelForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        log_action(request.user, f"Modification du contractuel {obj}", 'Contractuel', obj.pk)
        messages.success(request, "Contractuel mis à jour.")
        return redirect('contractuel_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contractuels/form.html', {'form': form, 'titre': 'Modifier le Contractuel', 'obj': obj})


@login_required
def contractuel_delete(request, pk):
    obj = get_object_or_404(Contractuel, pk=pk)
    if request.method == 'POST':
        nom = obj.get_full_name()
        log_action(request.user, f"Suppression du contractuel {obj}", 'Contractuel', obj.pk)
        obj.delete()
        messages.success(request, f"Contractuel {nom} supprimé.")
        return redirect('contractuel_list')
    return render(request, 'SYGEPECO/contractuels/confirm_delete.html', {'obj': obj})


# ─────────────────────────────────────────────────────────────
# CONTRATS
# ─────────────────────────────────────────────────────────────

@login_required
def contrat_list(request):
    qs = Contrat.objects.select_related('contractuel', 'type_contrat').all()
    statut = request.GET.get('statut', '')
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, 'SYGEPECO/contrats/list.html', {'contrats': qs, 'statut': statut})


@login_required
def contrat_detail(request, pk):
    contrat = get_object_or_404(Contrat, pk=pk)
    return render(request, 'SYGEPECO/contrats/detail.html', {'contrat': contrat})


@login_required
def contrat_create(request):
    form = ContratForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        log_action(request.user, f"Nouveau contrat pour {obj.contractuel}", 'Contrat', obj.pk)
        messages.success(request, "Contrat créé avec succès.")
        return redirect('contrat_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contrats/form.html', {'form': form, 'titre': 'Nouveau Contrat'})


@login_required
def contrat_update(request, pk):
    obj = get_object_or_404(Contrat, pk=pk)
    form = ContratForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        log_action(request.user, f"Modification contrat {obj}", 'Contrat', obj.pk)
        messages.success(request, "Contrat mis à jour.")
        return redirect('contrat_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contrats/form.html', {'form': form, 'titre': 'Modifier le Contrat', 'obj': obj})


@login_required
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
            messages.success(request, "Contrat renouvelé avec succès.")
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


# ─────────────────────────────────────────────────────────────
# PRÉSENCES
# ─────────────────────────────────────────────────────────────

@login_required
def presence_list(request):
    today = date.today()
    date_filtre = request.GET.get('date', str(today))
    try:
        date_filtre = date.fromisoformat(date_filtre)
    except ValueError:
        date_filtre = today
    presences = Presence.objects.filter(date=date_filtre).select_related('contractuel')
    return render(request, 'SYGEPECO/presences/list.html', {
        'presences': presences, 'date_filtre': date_filtre,
    })


@login_required
def presence_create(request):
    form = PresenceForm(request.POST or None)
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Présence enregistrée pour {obj.contractuel}", 'Presence', obj.pk)
        messages.success(request, "Présence enregistrée.")
        return redirect('presence_list')
    return render(request, 'SYGEPECO/presences/form.html', {'form': form})


@login_required
def presence_rapport(request):
    today = date.today()
    form = RapportFiltreForm(request.GET or {'mois': today.month, 'annee': today.year})
    data = []
    if form.is_valid():
        mois = int(form.cleaned_data['mois'])
        annee = int(form.cleaned_data['annee'])
        dept = form.cleaned_data.get('departement')
        qs = Contractuel.objects.filter(statut='ACTIF')
        if dept:
            qs = qs.filter(departement=dept)
        for c in qs:
            presences = Presence.objects.filter(
                contractuel=c,
                date__month=mois,
                date__year=annee
            )
            data.append({
                'contractuel': c,
                'present': presences.filter(statut='PRESENT').count(),
                'absent': presences.filter(statut='ABSENT').count(),
                'retard': presences.filter(statut='RETARD').count(),
            })
    return render(request, 'SYGEPECO/presences/rapport.html', {'form': form, 'data': data})


# ─────────────────────────────────────────────────────────────
# CONGÉS
# ─────────────────────────────────────────────────────────────

@login_required
def conge_list(request):
    statut = request.GET.get('statut', '')
    qs = Conge.objects.select_related('contractuel', 'approuve_par').all()
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, 'SYGEPECO/conges/list.html', {'conges': qs, 'statut': statut})


@login_required
def conge_detail(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    return render(request, 'SYGEPECO/conges/detail.html', {'conge': conge})


@login_required
def conge_create(request):
    form = CongeForm(request.POST or None)
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Demande de congé pour {obj.contractuel}", 'Conge', obj.pk)
        messages.success(request, "Demande de congé soumise.")
        return redirect('conge_list')
    return render(request, 'SYGEPECO/conges/form.html', {'form': form})


@login_required
def conge_approuver(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    form = CongeDecisionForm(request.POST or None, instance=conge)
    if request.method == 'POST' and form.is_valid():
        conge.statut = 'APPROUVE'
        conge.approuve_par = request.user
        conge.commentaire_rh = form.cleaned_data.get('commentaire_rh', '')
        conge.save()
        log_action(request.user, f"Congé approuvé pour {conge.contractuel}", 'Conge', conge.pk)
        messages.success(request, "Congé approuvé.")
        return redirect('conge_detail', pk=pk)
    return render(request, 'SYGEPECO/conges/decision.html', {'conge': conge, 'form': form, 'action': 'approuver'})


@login_required
def conge_rejeter(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    form = CongeDecisionForm(request.POST or None, instance=conge)
    if request.method == 'POST' and form.is_valid():
        conge.statut = 'REJETE'
        conge.approuve_par = request.user
        conge.commentaire_rh = form.cleaned_data.get('commentaire_rh', '')
        conge.save()
        log_action(request.user, f"Congé rejeté pour {conge.contractuel}", 'Conge', conge.pk)
        messages.warning(request, "Congé rejeté.")
        return redirect('conge_detail', pk=pk)
    return render(request, 'SYGEPECO/conges/decision.html', {'conge': conge, 'form': form, 'action': 'rejeter'})


# ─────────────────────────────────────────────────────────────
# PERMISSIONS
# ─────────────────────────────────────────────────────────────

@login_required
def permission_list(request):
    statut = request.GET.get('statut', '')
    qs = Permission.objects.select_related('contractuel', 'approuve_par').all()
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, 'SYGEPECO/permissions/list.html', {'permissions': qs, 'statut': statut})


@login_required
def permission_detail(request, pk):
    perm = get_object_or_404(Permission, pk=pk)
    return render(request, 'SYGEPECO/permissions/detail.html', {'permission': perm})


@login_required
def permission_create(request):
    form = PermissionForm(request.POST or None)
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Demande de permission pour {obj.contractuel}", 'Permission', obj.pk)
        messages.success(request, "Demande de permission soumise.")
        return redirect('permission_list')
    return render(request, 'SYGEPECO/permissions/form.html', {'form': form})


@login_required
def permission_approuver(request, pk):
    perm = get_object_or_404(Permission, pk=pk)
    form = PermissionDecisionForm(request.POST or None, instance=perm)
    if request.method == 'POST' and form.is_valid():
        perm.statut = 'APPROUVE'
        perm.approuve_par = request.user
        perm.save()
        log_action(request.user, f"Permission approuvée pour {perm.contractuel}", 'Permission', perm.pk)
        messages.success(request, "Permission approuvée.")
        return redirect('permission_detail', pk=pk)
    return render(request, 'SYGEPECO/permissions/decision.html', {'permission': perm, 'form': form, 'action': 'approuver'})


@login_required
def permission_rejeter(request, pk):
    perm = get_object_or_404(Permission, pk=pk)
    form = PermissionDecisionForm(request.POST or None, instance=perm)
    if request.method == 'POST' and form.is_valid():
        perm.statut = 'REJETE'
        perm.approuve_par = request.user
        perm.save()
        log_action(request.user, f"Permission rejetée pour {perm.contractuel}", 'Permission', perm.pk)
        messages.warning(request, "Permission rejetée.")
        return redirect('permission_detail', pk=pk)
    return render(request, 'SYGEPECO/permissions/decision.html', {'permission': perm, 'form': form, 'action': 'rejeter'})


# ─────────────────────────────────────────────────────────────
# CALENDRIER
# ─────────────────────────────────────────────────────────────

@login_required
def calendrier(request):
    return render(request, 'SYGEPECO/calendrier/index.html')


# ─────────────────────────────────────────────────────────────
# RAPPORTS
# ─────────────────────────────────────────────────────────────

@login_required
def rapports(request):
    today = date.today()
    stats_dept = Contractuel.objects.filter(statut='ACTIF').values(
        'departement__nom'
    ).annotate(total=Count('id')).order_by('-total')

    contrats_par_type = Contrat.objects.filter(statut='EN_COURS').values(
        'type_contrat__nom'
    ).annotate(total=Count('id')).order_by('-total')

    context = {
        'stats_dept': list(stats_dept),
        'contrats_par_type': list(contrats_par_type),
        'total_actifs': Contractuel.objects.filter(statut='ACTIF').count(),
        'total_contrats': Contrat.objects.filter(statut='EN_COURS').count(),
        'total_presences_mois': Presence.objects.filter(
            date__month=today.month, date__year=today.year
        ).count(),
        'conges_mois': Conge.objects.filter(
            date_debut__month=today.month,
            date_debut__year=today.year
        ).count(),
        'conges_attente': Conge.objects.filter(statut='EN_ATTENTE').count(),
        'permissions_mois': Permission.objects.filter(
            date__month=today.month, date__year=today.year
        ).count(),
        'permissions_attente': Permission.objects.filter(statut='EN_ATTENTE').count(),
        'mois_courant': today.month,
        'annee_courante': today.year,
        'mois_nom': today.strftime('%B %Y'),
    }
    return render(request, 'SYGEPECO/rapports/index.html', context)


@login_required
def rapports_exporter(request):
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))
    return export_presences_excel(mois, annee)


@login_required
def rapports_exporter_conges(request):
    today = date.today()
    mois_param = request.GET.get('mois', '')
    annee_param = request.GET.get('annee', '')
    mois = int(mois_param) if mois_param else None
    annee = int(annee_param) if annee_param else None
    return export_conges_excel(mois, annee)


@login_required
def rapports_exporter_permissions(request):
    today = date.today()
    mois_param = request.GET.get('mois', '')
    annee_param = request.GET.get('annee', '')
    mois = int(mois_param) if mois_param else None
    annee = int(annee_param) if annee_param else None
    return export_permissions_excel(mois, annee)


@login_required
def rapports_exporter_contractuels(request):
    return export_contractuels_excel()


# ─────────────────────────────────────────────────────────────
# HISTORIQUE
# ─────────────────────────────────────────────────────────────

@login_required
def historique(request):
    logs = ActionLog.objects.select_related('utilisateur').all()[:100]
    return render(request, 'SYGEPECO/historique/index.html', {'logs': logs})


# ─────────────────────────────────────────────────────────────
# API JSON
# ─────────────────────────────────────────────────────────────

@login_required
def api_dashboard_stats(request):
    today = date.today()
    return JsonResponse({
        'total_actifs': Contractuel.objects.filter(statut='ACTIF').count(),
        'presences_today': Presence.objects.filter(date=today, statut='PRESENT').count(),
        'conges_attente': Conge.objects.filter(statut='EN_ATTENTE').count(),
        'permissions_attente': Permission.objects.filter(statut='EN_ATTENTE').count(),
    })


@login_required
def api_calendrier_events(request):
    events = []
    for c in Conge.objects.filter(statut='APPROUVE').select_related('contractuel'):
        events.append({
            'title': f"Congé — {c.contractuel.get_full_name()}",
            'start': str(c.date_debut),
            'end': str(c.date_fin + timedelta(days=1)),
            'color': '#22C55E',
            'type': 'conge',
        })
    for p in Permission.objects.filter(statut='APPROUVE').select_related('contractuel'):
        events.append({
            'title': f"Permission — {p.contractuel.get_full_name()}",
            'start': str(p.date),
            'end': str(p.date),
            'color': '#4A6CF7',
            'type': 'permission',
        })
    return JsonResponse({'events': events})


@login_required
def api_chart_presences(request):
    today = date.today()
    labels = []
    presents = []
    absents = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%d/%m'))
        presents.append(Presence.objects.filter(date=d, statut='PRESENT').count())
        absents.append(Presence.objects.filter(date=d, statut='ABSENT').count())
    return JsonResponse({'labels': labels, 'presents': presents, 'absents': absents})


# ═════════════════════════════════════════════════════════════
# ESPACE CONTRACTUEL — Vue personnelle du contractuel
# ═════════════════════════════════════════════════════════════

@contractuel_required
def espace_home(request):
    """Tableau de bord personnel du contractuel."""
    c = request.user.contractuel
    today = date.today()

    contrat_actif = c.get_contrat_actif()
    mes_conges = c.conges.all()
    mes_permissions = c.permissions.all()

    # Solde congés : quota 30j - jours approuvés cette année
    conges_approuves_annee = c.conges.filter(
        statut='APPROUVE',
        date_debut__year=today.year
    )
    jours_pris = sum(cg.nb_jours() for cg in conges_approuves_annee)
    solde_conges = max(0, 30 - jours_pris)

    # Présences du mois
    presences_mois = c.presences.filter(date__month=today.month, date__year=today.year)
    nb_present = presences_mois.filter(statut='PRESENT').count()
    nb_absent  = presences_mois.filter(statut='ABSENT').count()

    # Alerte contrat expirant
    alerte_contrat = None
    if contrat_actif and contrat_actif.date_fin:
        delta = (contrat_actif.date_fin - today).days
        if delta <= 30:
            alerte_contrat = delta

    context = {
        'contractuel': c,
        'contrat_actif': contrat_actif,
        'conges_en_attente': mes_conges.filter(statut='EN_ATTENTE').count(),
        'permissions_en_attente': mes_permissions.filter(statut='EN_ATTENTE').count(),
        'conges_approuves': mes_conges.filter(statut='APPROUVE').count(),
        'solde_conges': solde_conges,
        'jours_pris': jours_pris,
        'nb_present': nb_present,
        'nb_absent': nb_absent,
        'alerte_contrat': alerte_contrat,
        'today': today,
    }
    return render(request, 'SYGEPECO/espace/home.html', context)


@contractuel_required
def espace_profil(request):
    c = request.user.contractuel
    contrat_actif = c.get_contrat_actif()
    return render(request, 'SYGEPECO/espace/profil.html', {
        'contractuel': c,
        'contrat_actif': contrat_actif,
    })


@contractuel_required
def espace_profil_modifier(request):
    c = request.user.contractuel
    form = EspaceProfilForm(request.POST or None, request.FILES or None, instance=c)
    if form.is_valid():
        form.save()
        log_action(request.user, "Modification de son profil", 'Contractuel', c.pk)
        messages.success(request, "Votre profil a été mis à jour.")
        return redirect('espace_profil')
    return render(request, 'SYGEPECO/espace/profil_modifier.html', {'form': form, 'contractuel': c})


@contractuel_required
def espace_mes_conges(request):
    c = request.user.contractuel
    conges = c.conges.all().order_by('-created_at')
    return render(request, 'SYGEPECO/espace/mes_conges.html', {
        'conges': conges,
        'contractuel': c,
    })


@contractuel_required
def espace_demander_conge(request):
    c = request.user.contractuel
    form = EspaceCongeForm(request.POST or None)
    if form.is_valid():
        conge = form.save(commit=False)
        conge.contractuel = c
        conge.save()
        log_action(request.user, f"Demande de congé soumise ({conge.get_type_conge_display()})", 'Conge', conge.pk)
        messages.success(request, "Votre demande de congé a été soumise. Elle est en attente d'approbation.")
        return redirect('espace_mes_conges')
    return render(request, 'SYGEPECO/espace/demander_conge.html', {'form': form, 'contractuel': c})


@contractuel_required
def espace_mes_permissions(request):
    c = request.user.contractuel
    permissions = c.permissions.all().order_by('-created_at')
    return render(request, 'SYGEPECO/espace/mes_permissions.html', {
        'permissions': permissions,
        'contractuel': c,
    })


@contractuel_required
def espace_demander_permission(request):
    c = request.user.contractuel
    form = EspacePermissionForm(request.POST or None)
    if form.is_valid():
        perm = form.save(commit=False)
        perm.contractuel = c
        perm.save()
        log_action(request.user, f"Demande de permission soumise ({perm.date})", 'Permission', perm.pk)
        messages.success(request, "Votre demande de permission a été soumise.")
        return redirect('espace_mes_permissions')
    return render(request, 'SYGEPECO/espace/demander_permission.html', {'form': form, 'contractuel': c})


@contractuel_required
def espace_mon_contrat(request):
    c = request.user.contractuel
    contrat_actif  = c.get_contrat_actif()
    autres_contrats = c.contrats.exclude(pk=contrat_actif.pk).order_by('-created_at') if contrat_actif else c.contrats.all().order_by('-created_at')
    return render(request, 'SYGEPECO/espace/mon_contrat.html', {
        'contractuel':   c,
        'contrat_actif': contrat_actif,
        'autres_contrats': autres_contrats,
    })


@contractuel_required
def espace_mes_presences(request):
    from calendar import month_name
    c = request.user.contractuel
    today = date.today()
    mois  = int(request.GET.get('mois',  today.month))
    annee = int(request.GET.get('annee', today.year))

    # navigation mois précédent / suivant
    if mois == 1:
        mois_prev, annee_prev = 12, annee - 1
    else:
        mois_prev, annee_prev = mois - 1, annee
    if mois == 12:
        mois_next, annee_next = 1, annee + 1
    else:
        mois_next, annee_next = mois + 1, annee

    MOIS_FR = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
               'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    presences = c.presences.filter(date__month=mois, date__year=annee).order_by('date')
    return render(request, 'SYGEPECO/espace/mes_presences.html', {
        'presences':      presences,
        'contractuel':    c,
        'nb_presents':    presences.filter(statut='PRESENT').count(),
        'nb_absents':     presences.filter(statut='ABSENT').count(),
        'nb_retards':     presences.filter(statut='RETARD').count(),
        'nb_justifies':   presences.filter(statut='JUSTIFIE').count(),
        'mois':           mois,
        'annee':          annee,
        'mois_label':     f"{MOIS_FR[mois]} {annee}",
        'mois_prev':      mois_prev,
        'annee_prev':     annee_prev,
        'mois_next':      mois_next,
        'annee_next':     annee_next,
        'is_current_month': (mois == today.month and annee == today.year),
    })


# ─────────────────────────────────────────────────────────────
# ENTREPRISES
# ─────────────────────────────────────────────────────────────

@login_required
def entreprise_list(request):
    q = request.GET.get('q', '')
    entreprises = Entreprise.objects.all()
    if q:
        entreprises = entreprises.filter(nom__icontains=q)
    return render(request, 'SYGEPECO/entreprises/list.html', {
        'entreprises': entreprises,
        'q': q,
    })


@login_required
def entreprise_detail(request, pk):
    entreprise = get_object_or_404(Entreprise, pk=pk)
    contractuels = entreprise.contractuels.select_related('poste', 'departement').all()
    return render(request, 'SYGEPECO/entreprises/detail.html', {
        'entreprise': entreprise,
        'contractuels': contractuels,
    })


@login_required
def entreprise_create(request):
    from .forms import EntrepriseForm
    form = EntrepriseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        entreprise = form.save()
        log_action(request.user, f"Création entreprise : {entreprise.nom}", 'Entreprise', entreprise.pk)
        messages.success(request, f"Entreprise « {entreprise.nom} » créée.")
        return redirect('entreprise_detail', pk=entreprise.pk)
    return render(request, 'SYGEPECO/entreprises/form.html', {'form': form, 'titre': 'Nouvelle entreprise'})


@login_required
def entreprise_update(request, pk):
    from .forms import EntrepriseForm
    entreprise = get_object_or_404(Entreprise, pk=pk)
    form = EntrepriseForm(request.POST or None, request.FILES or None, instance=entreprise)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_action(request.user, f"Modification entreprise : {entreprise.nom}", 'Entreprise', entreprise.pk)
        messages.success(request, "Entreprise mise à jour.")
        return redirect('entreprise_detail', pk=entreprise.pk)
    return render(request, 'SYGEPECO/entreprises/form.html', {'form': form, 'titre': f'Modifier — {entreprise.nom}', 'entreprise': entreprise})


@login_required
def entreprise_delete(request, pk):
    entreprise = get_object_or_404(Entreprise, pk=pk)
    if request.method == 'POST':
        nom = entreprise.nom
        entreprise.delete()
        log_action(request.user, f"Suppression entreprise : {nom}", 'Entreprise')
        messages.success(request, f"Entreprise « {nom} » supprimée.")
        return redirect('entreprise_list')
    return render(request, 'SYGEPECO/entreprises/confirm_delete.html', {'entreprise': entreprise})


# ─────────────────────────────────────────────────────────────
# ESPACE ENTREPRISE  (vue filtrée pour les gestionnaires d'entreprise)
# ─────────────────────────────────────────────────────────────

def _get_entreprise_for_user(user):
    """Retourne l'entreprise liée au gestionnaire ou None si admin/DRH."""
    try:
        profile = user.profile
    except Exception:
        return None
    if profile.role in ('ADMINISTRATEUR', 'DRH'):
        return None          # accès total, pas de filtre
    return profile.entreprise


@login_required
def entreprise_espace_home(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role not in (
            'ENTREPRISE', 'ADMINISTRATEUR', 'DRH'):
        messages.error(request, "Accès non autorisé.")
        return redirect('login')

    entreprise = _get_entreprise_for_user(request.user)
    # Si admin sans entreprise liée → première entreprise
    entreprises = Entreprise.objects.filter(active=True)

    if entreprise:
        agents = Contractuel.objects.filter(entreprise=entreprise)
    else:
        agents = Contractuel.objects.all()

    today = date.today()
    total = agents.count()
    actifs = agents.filter(statut='ACTIF').count()
    conges_attente = Conge.objects.filter(contractuel__in=agents, statut='EN_ATTENTE').count()
    permissions_attente = Permission.objects.filter(contractuel__in=agents, statut='EN_ATTENTE').count()
    presences_today = Presence.objects.filter(contractuel__in=agents, date=today, statut='PRESENT').count()

    # Répartition par département
    dept_stats = (agents.values('departement__nom')
                  .annotate(total=Count('id'))
                  .order_by('-total')[:5])

    ctx = {
        'entreprise': entreprise,
        'entreprises': entreprises,
        'total': total,
        'actifs': actifs,
        'conges_attente': conges_attente,
        'permissions_attente': permissions_attente,
        'presences_today': presences_today,
        'dept_stats': dept_stats,
    }
    return render(request, 'SYGEPECO/entreprise_espace/home.html', ctx)


@login_required
def entreprise_espace_agents(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role not in (
            'ENTREPRISE', 'ADMINISTRATEUR', 'DRH'):
        messages.error(request, "Accès non autorisé.")
        return redirect('login')

    entreprise = _get_entreprise_for_user(request.user)
    agents = Contractuel.objects.select_related('poste', 'departement', 'entreprise')
    if entreprise:
        agents = agents.filter(entreprise=entreprise)

    q = request.GET.get('q', '')
    if q:
        agents = agents.filter(Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(matricule__icontains=q))

    statut = request.GET.get('statut', '')
    if statut:
        agents = agents.filter(statut=statut)

    ctx = {
        'entreprise': entreprise,
        'agents': agents,
        'q': q,
        'statut': statut,
        'total': agents.count(),
    }
    return render(request, 'SYGEPECO/entreprise_espace/agents.html', ctx)


@login_required
def entreprise_espace_conges(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role not in (
            'ENTREPRISE', 'ADMINISTRATEUR', 'DRH'):
        messages.error(request, "Accès non autorisé.")
        return redirect('login')

    entreprise = _get_entreprise_for_user(request.user)
    conges = Conge.objects.select_related('contractuel', 'approuve_par')
    if entreprise:
        conges = conges.filter(contractuel__entreprise=entreprise)

    statut = request.GET.get('statut', '')
    if statut:
        conges = conges.filter(statut=statut)

    ctx = {
        'entreprise': entreprise,
        'conges': conges.order_by('-created_at'),
        'statut': statut,
    }
    return render(request, 'SYGEPECO/entreprise_espace/conges.html', ctx)


@login_required
def entreprise_espace_permissions(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role not in (
            'ENTREPRISE', 'ADMINISTRATEUR', 'DRH'):
        messages.error(request, "Accès non autorisé.")
        return redirect('login')

    entreprise = _get_entreprise_for_user(request.user)
    perms = Permission.objects.select_related('contractuel', 'approuve_par')
    if entreprise:
        perms = perms.filter(contractuel__entreprise=entreprise)

    statut = request.GET.get('statut', '')
    if statut:
        perms = perms.filter(statut=statut)

    ctx = {
        'entreprise': entreprise,
        'permissions': perms.order_by('-created_at'),
        'statut': statut,
    }
    return render(request, 'SYGEPECO/entreprise_espace/permissions.html', ctx)


@login_required
def entreprise_espace_presences(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role not in (
            'ENTREPRISE', 'ADMINISTRATEUR', 'DRH'):
        messages.error(request, "Accès non autorisé.")
        return redirect('login')

    entreprise = _get_entreprise_for_user(request.user)
    today = date.today()
    mois = int(request.GET.get('mois', today.month))
    annee = int(request.GET.get('annee', today.year))

    presences = Presence.objects.select_related('contractuel').filter(
        date__month=mois, date__year=annee
    )
    if entreprise:
        presences = presences.filter(contractuel__entreprise=entreprise)

    ctx = {
        'entreprise': entreprise,
        'presences': presences.order_by('-date'),
        'mois': mois,
        'annee': annee,
        'mois_nom': ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'][mois],
    }
    return render(request, 'SYGEPECO/entreprise_espace/presences.html', ctx)
