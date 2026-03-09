from io import BytesIO
from ._base import *
from ..utils import solde_conges_annuel


@contractuel_required
def espace_home(request):
    c = request.user.contractuel
    today = date.today()
    contrat_actif = c.get_contrat_actif()
    mes_conges = c.conges.all()
    mes_permissions = c.permissions.all()

    conges_approuves_annee = c.conges.filter(
        type_conge='ANNUEL', statut='APPROUVE', date_debut__year=today.year)
    jours_pris = sum(cg.nb_jours() for cg in conges_approuves_annee)
    solde_conges = solde_conges_annuel(c)

    presences_mois = c.presences.filter(date__month=today.month, date__year=today.year)
    nb_present = presences_mois.filter(statut='PRESENT').count()
    nb_absent  = presences_mois.filter(statut='ABSENT').count()

    alerte_contrat = None
    if contrat_actif and contrat_actif.date_fin:
        delta = (contrat_actif.date_fin - today).days
        if delta <= 30:
            alerte_contrat = delta

    return render(request, 'SYGEPECO/espace/home.html', {
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
    })


@contractuel_required
def espace_profil(request):
    c = request.user.contractuel
    return render(request, 'SYGEPECO/espace/profil.html', {
        'contractuel': c,
        'contrat_actif': c.get_contrat_actif(),
    })


@contractuel_required
def espace_profil_modifier(request):
    c = request.user.contractuel
    form = EspaceProfilForm(request.POST or None, request.FILES or None, instance=c)
    if form.is_valid():
        form.save()
        salaire = form.cleaned_data.get('salaire')
        if salaire is not None:
            contrat = c.get_contrat_actif()
            if contrat:
                contrat.salaire = salaire
                contrat.save(update_fields=['salaire'])
        log_action(request.user, "Modification de son profil", 'Contractuel', c.pk)
        messages.success(request, "Votre profil a ete mis a jour.")
        return redirect('espace_profil')
    return render(request, 'SYGEPECO/espace/profil_modifier.html', {'form': form, 'contractuel': c})


@contractuel_required
def espace_mes_conges(request):
    c = request.user.contractuel
    return render(request, 'SYGEPECO/espace/mes_conges.html', {
        'conges': c.conges.all().order_by('-created_at'),
        'contractuel': c,
    })


@contractuel_required
def espace_demander_conge(request):
    c = request.user.contractuel
    annee = date.today().year
    jours_pris = sum(
        cg.nb_jours()
        for cg in c.conges.filter(
            type_conge='ANNUEL',
            statut__in=['APPROUVE', 'EN_ATTENTE'],
            date_debut__year=annee)
    )
    solde_annuel = max(0, 30 - jours_pris)
    form = EspaceCongeForm(request.POST or None, request.FILES or None, contractuel=c)
    if form.is_valid():
        conge = form.save(commit=False)
        conge.contractuel = c
        conge.save()
        log_action(request.user,
                   f"Demande de conge soumise ({conge.get_type_conge_display()})",
                   'Conge', conge.pk)
        messages.success(request, "Votre demande de conge a ete soumise.")
        return redirect('espace_mes_conges')
    return render(request, 'SYGEPECO/espace/demander_conge.html', {
        'form': form, 'contractuel': c,
        'solde_annuel': solde_annuel, 'jours_pris': jours_pris,
    })


@contractuel_required
def espace_mes_permissions(request):
    c = request.user.contractuel
    return render(request, 'SYGEPECO/espace/mes_permissions.html', {
        'permissions': c.permissions.all().order_by('-created_at'),
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
        log_action(request.user,
                   f"Demande de permission soumise ({perm.date_debut} -> {perm.date_fin})",
                   'Permission', perm.pk)
        messages.success(request, "Votre demande de permission a ete soumise.")
        return redirect('espace_mes_permissions')
    return render(request, 'SYGEPECO/espace/demander_permission.html',
                  {'form': form, 'contractuel': c})


@contractuel_required
def espace_mon_contrat(request):
    c = request.user.contractuel
    contrat_actif = c.get_contrat_actif()
    autres = (c.contrats.exclude(pk=contrat_actif.pk).order_by('-created_at')
              if contrat_actif else c.contrats.all().order_by('-created_at'))
    return render(request, 'SYGEPECO/espace/mon_contrat.html', {
        'contractuel': c,
        'contrat_actif': contrat_actif,
        'autres_contrats': autres,
    })


@contractuel_required
def espace_mes_presences(request):
    c = request.user.contractuel
    today = date.today()
    mois  = int(request.GET.get('mois',  today.month))
    annee = int(request.GET.get('annee', today.year))

    mois_prev = 12 if mois == 1 else mois - 1
    annee_prev = annee - 1 if mois == 1 else annee
    mois_next = 1 if mois == 12 else mois + 1
    annee_next = annee + 1 if mois == 12 else annee

    MOIS_FR = ['', 'Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin',
               'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre']

    presences = c.presences.filter(date__month=mois, date__year=annee).order_by('date')
    return render(request, 'SYGEPECO/espace/mes_presences.html', {
        'presences': presences, 'contractuel': c,
        'nb_presents':  presences.filter(statut='PRESENT').count(),
        'nb_absents':   presences.filter(statut='ABSENT').count(),
        'nb_retards':   presences.filter(statut='RETARD').count(),
        'nb_justifies': presences.filter(statut='JUSTIFIE').count(),
        'mois': mois, 'annee': annee,
        'mois_label': f"{MOIS_FR[mois]} {annee}",
        'mois_prev': mois_prev, 'annee_prev': annee_prev,
        'mois_next': mois_next, 'annee_next': annee_next,
        'is_current_month': (mois == today.month and annee == today.year),
    })


@contractuel_required
def espace_telecharger_profil(request):
    from ..utils import build_fiche_pdf
    c = request.user.contractuel
    buf = build_fiche_pdf(c)
    response = HttpResponse(buf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Fiche_{c.nom}_{c.prenom}.pdf"'
    return response
