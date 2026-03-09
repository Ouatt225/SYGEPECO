from ._base import *
from django.core.paginator import Paginator


@login_required
@rh_required
def conge_list(request):
    statut = request.GET.get('statut', '')
    qs = Conge.objects.select_related('contractuel', 'approuve_par').all()
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        qs = qs.filter(contractuel__direction=manager_dir)
    if statut:
        qs = qs.filter(statut=statut)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'SYGEPECO/conges/list.html', {'conges': page_obj, 'page_obj': page_obj, 'statut': statut})


@login_required
@rh_required
def conge_detail(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    return render(request, 'SYGEPECO/conges/detail.html', {'conge': conge})


@login_required
@rh_required
def conge_create(request):
    form = CongeForm(request.POST or None)
    manager_dir = get_manager_direction(request.user)
    if manager_dir:
        form.fields['contractuel'].queryset = Contractuel.objects.filter(
            direction=manager_dir, statut='ACTIF')
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Demande de conge pour {obj.contractuel}", 'Conge', obj.pk)
        messages.success(request, "Demande de conge soumise.")
        return redirect('conge_list')
    return render(request, 'SYGEPECO/conges/form.html', {'form': form})



def _conge_rh_decision(request, pk):
    """Charge le conge et verifie l'acces manager. Retourne (conge, None) ou (None, redirect)."""
    conge = get_object_or_404(Conge, pk=pk)
    manager_dir = get_manager_direction(request.user)
    if manager_dir and conge.contractuel.direction != manager_dir:
        messages.error(request, "Vous ne pouvez pas traiter ce conge : hors de votre direction.")
        return None, redirect('conge_detail', pk=pk)
    return conge, None

@login_required
@rh_required
def conge_approuver(request, pk):
    conge, err = _conge_rh_decision(request, pk)
    if err: return err
    form = CongeDecisionForm(request.POST or None, instance=conge)
    if request.method == 'POST' and form.is_valid():
        conge.statut = 'APPROUVE'
        conge.approuve_par = request.user
        conge.commentaire_rh = form.cleaned_data.get('commentaire_rh', '')
        conge.save()
        log_action(request.user, f"Conge approuve pour {conge.contractuel}", 'Conge', conge.pk)
        messages.success(request, "Conge approuve.")
        return redirect('conge_detail', pk=pk)
    return render(request, 'SYGEPECO/conges/decision.html',
                  {'conge': conge, 'form': form, 'action': 'approuver'})


@login_required
@rh_required
def conge_rejeter(request, pk):
    conge, err = _conge_rh_decision(request, pk)
    if err: return err
    form = CongeDecisionForm(request.POST or None, instance=conge)
    if request.method == 'POST' and form.is_valid():
        conge.statut = 'REJETE'
        conge.approuve_par = request.user
        conge.commentaire_rh = form.cleaned_data.get('commentaire_rh', '')
        conge.save()
        log_action(request.user, f"Conge rejete pour {conge.contractuel}", 'Conge', conge.pk)
        messages.warning(request, "Conge rejete.")
        return redirect('conge_detail', pk=pk)
    return render(request, 'SYGEPECO/conges/decision.html',
                  {'conge': conge, 'form': form, 'action': 'rejeter'})


@login_required
@rh_required
def conge_valider_manager(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    manager_dir = get_manager_direction(request.user)
    if manager_dir and conge.contractuel.direction != manager_dir:
        messages.error(request, "Vous ne pouvez pas valider ce conge : hors de votre direction.")
        return redirect('conge_detail', pk=pk)
    if conge.statut != 'EN_ATTENTE':
        messages.warning(request, "Ce conge n'est pas en attente de validation manager.")
        return redirect('conge_detail', pk=pk)
    if request.method == 'POST':
        conge.statut = 'VALIDE_MANAGER'
        conge.valide_par_manager = request.user
        conge.commentaire_manager = request.POST.get('commentaire_manager', '')
        conge.save()
        log_action(request.user, f"Conge valide (manager) pour {conge.contractuel}", 'Conge', conge.pk)
        messages.success(request, "Conge valide — en attente de validation entreprise.")
        return redirect('conge_detail', pk=pk)
    return render(request, 'SYGEPECO/conges/decision_manager.html',
                  {'conge': conge, 'action': 'valider'})


@login_required
@rh_required
def conge_rejeter_manager(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    manager_dir = get_manager_direction(request.user)
    if manager_dir and conge.contractuel.direction != manager_dir:
        messages.error(request, "Vous ne pouvez pas rejeter ce conge : hors de votre direction.")
        return redirect('conge_detail', pk=pk)
    if conge.statut != 'EN_ATTENTE':
        messages.warning(request, "Ce conge n'est pas en attente de validation manager.")
        return redirect('conge_detail', pk=pk)
    if request.method == 'POST':
        conge.statut = 'REJETE'
        conge.valide_par_manager = request.user
        conge.commentaire_manager = request.POST.get('commentaire_manager', '')
        conge.save()
        log_action(request.user, f"Conge rejete (manager) pour {conge.contractuel}", 'Conge', conge.pk)
        messages.warning(request, "Conge rejete par le manager.")
        return redirect('conge_detail', pk=pk)
    return render(request, 'SYGEPECO/conges/decision_manager.html',
                  {'conge': conge, 'action': 'rejeter'})


@login_required
def entreprise_conge_approuver(request, pk):
    ent, err = ent_check(request)
    if err: return err
    conge = get_object_or_404(Conge, pk=pk)
    if ent and conge.contractuel.entreprise != ent:
        messages.error(request, "Acces refuse : ce conge n'appartient pas a votre entreprise.")
        return redirect('entreprise_espace_conges')
    if conge.statut not in ('EN_ATTENTE', 'VALIDE_MANAGER'):
        messages.warning(request, "Ce conge ne peut pas etre approuve.")
        return redirect('entreprise_espace_conges')
    if request.method == 'POST':
        conge.statut = 'APPROUVE'
        conge.approuve_par = request.user
        conge.commentaire_rh = request.POST.get('commentaire_rh', '')
        conge.save()
        log_action(request.user, f"Conge approuve (entreprise) pour {conge.contractuel}", 'Conge', conge.pk)
        messages.success(request, "Conge approuve definitivement.")
        return redirect('entreprise_espace_conges')
    return render(request, 'SYGEPECO/entreprise_espace/conge_decision.html',
                  {'conge': conge, 'action': 'approuver'})


@login_required
def entreprise_conge_rejeter(request, pk):
    ent, err = ent_check(request)
    if err: return err
    conge = get_object_or_404(Conge, pk=pk)
    if ent and conge.contractuel.entreprise != ent:
        messages.error(request, "Acces refuse : ce conge n'appartient pas a votre entreprise.")
        return redirect('entreprise_espace_conges')
    if conge.statut not in ('EN_ATTENTE', 'VALIDE_MANAGER'):
        messages.warning(request, "Ce conge ne peut pas etre rejete.")
        return redirect('entreprise_espace_conges')
    if request.method == 'POST':
        conge.statut = 'REJETE'
        conge.approuve_par = request.user
        conge.commentaire_rh = request.POST.get('commentaire_rh', '')
        conge.save()
        log_action(request.user, f"Conge rejete (entreprise) pour {conge.contractuel}", 'Conge', conge.pk)
        messages.warning(request, "Conge rejete par l'entreprise.")
        return redirect('entreprise_espace_conges')
    return render(request, 'SYGEPECO/entreprise_espace/conge_decision.html',
                  {'conge': conge, 'action': 'rejeter'})


@login_required
def conge_document_medical(request, pk):
    """Téléchargement sécurisé du justificatif médical d'un congé.
    Accès : agent propriétaire, son entreprise, RH/DRH/Admin/Manager."""
    from pathlib import Path
    from django.http import FileResponse, Http404
    from django.conf import settings as _settings

    conge = get_object_or_404(
        Conge.objects.select_related('contractuel', 'contractuel__entreprise'),
        pk=pk,
    )

    if not conge.document_medical:
        raise Http404

    # ── Contrôle d'accès ─────────────────────────────────────────────────
    can_access = False

    # RH / Admin / Manager
    try:
        if request.user.profile.role in ("ADMINISTRATEUR", "DRH", "RH", "MANAGER"):
            can_access = True
    except Exception:
        pass

    # Agent lui-même
    if not can_access:
        if hasattr(request.user, "contractuel") and request.user.contractuel == conge.contractuel:
            can_access = True

    # Entreprise
    if not can_access:
        try:
            if request.user.profile.role == "ENTREPRISE":
                ent = request.user.profile.entreprise
                if ent is None or conge.contractuel.entreprise_id == ent.pk:
                    # ent is None → gestionnaire global (voit tout)
                    can_access = True
        except Exception:
            pass

    if not can_access:
        # Debug temporaire — affiche la raison exacte du refus
        try:
            role = request.user.profile.role if hasattr(request.user, 'profile') else 'NO_PROFILE'
            ent_id = request.user.profile.entreprise_id if hasattr(request.user, 'profile') else 'N/A'
            c_ent_id = conge.contractuel.entreprise_id if conge.contractuel else 'NO_CONTRACTUEL'
        except Exception as _dbg_e:
            role, ent_id, c_ent_id = f'ERR:{_dbg_e}', '?', '?'
        messages.error(request, f"Accès refusé — role={role} | profile.ent={ent_id} | conge.ctr.ent={c_ent_id}")
        if hasattr(request.user, "contractuel") and request.user.contractuel:
            return redirect("espace_home")
        try:
            if request.user.profile.role == "ENTREPRISE":
                return redirect("entreprise_espace_conges")
        except Exception:
            pass
        return redirect("dashboard")

    # ── Servir le fichier ─────────────────────────────────────────────────
    media_root = Path(_settings.MEDIA_ROOT).resolve()
    # Normaliser les séparateurs (Windows stocke parfois des backslashes)
    name = conge.document_medical.name.replace("\\", "/")
    target = (media_root / name).resolve()

    if not str(target).startswith(str(media_root)) or not target.exists():
        raise Http404

    import os
    filename = os.path.basename(str(target))
    return FileResponse(open(target, "rb"), as_attachment=True, filename=filename)
