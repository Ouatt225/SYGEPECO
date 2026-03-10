"""
Gestion du workflow congés : EN_ATTENTE → VALIDE_MANAGER → APPROUVE/REJETE.
Téléchargement sécurisé des justificatifs médicaux avec contrôle d'accès IDOR.
"""
import logging

logger = logging.getLogger('SYGEPECO')

from ._base import *
from django.core.paginator import Paginator


@login_required
@rh_required
def conge_list(request):
    """Liste des congés filtrée selon le rôle de l'utilisateur.

    - Admin/DRH/RH : tous les congés
    - Manager : sa direction uniquement
    - Entreprise : ses agents uniquement

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : template conges/list.html.
"""
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
    """Détail d'une demande de congé.

    Args:
        request: HttpRequest Django.
        pk (int): Clé primaire du congé.

    Returns:
        HttpResponse : template conges/detail.html.
"""
    conge = get_object_or_404(Conge, pk=pk)
    return render(request, 'SYGEPECO/conges/detail.html', {'conge': conge})


@login_required
@rh_required
def conge_create(request):
    """Crée une demande de congé (par le RH pour un agent).

    Args:
        request: HttpRequest Django.

    Returns:
        HttpResponse : formulaire ou redirection.
"""
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
    """Approuve une demande de congé (étape RH/DRH).

    Requiert que le congé soit au statut VALIDE_MANAGER.
    Enregistre l'approbateur et la date. Log l'action.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire du congé.

    Returns:
        HttpResponseRedirect vers la liste.
"""
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
    """Rejette une demande de congé (étape RH/DRH).

    Enregistre le motif de refus via CongeDecisionForm.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire du congé.

    Returns:
        HttpResponseRedirect vers la liste.
"""
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
    """Pré-validation Manager (1re étape du workflow congé).

    Passe le statut de EN_ATTENTE → VALIDE_MANAGER.
    Vérifie que le congé appartient à la direction du Manager.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire du congé.

    Returns:
        HttpResponseRedirect vers la liste.
"""
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
    """Rejet Manager (1re étape du workflow congé).

    Passe le statut à REJETE sans passer par RH.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Clé primaire du congé.

    Returns:
        HttpResponseRedirect vers la liste.
"""
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
    """Approuve un conge depuis l espace Entreprise.

    Verifie que le conge appartient a un agent de l entreprise connectee.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Cle primaire du conge.

    Returns:
        HttpResponseRedirect vers la liste des conges entreprise.
"""
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
    """Rejette un conge depuis l espace Entreprise.

    Args:
        request: HttpRequest Django (POST).
        pk (int): Cle primaire du conge.

    Returns:
        HttpResponseRedirect vers la liste des conges entreprise.
"""
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
    except Exception:  # Superuser ou compte sans UserProfile
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
        logger.warning(
            'conge_document_medical: accès refusé user=%s conge_pk=%s',
            request.user.username, pk,
        )
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à consulter ce document.")
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
