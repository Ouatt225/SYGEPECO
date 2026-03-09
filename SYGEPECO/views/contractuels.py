import os as _os
from io import BytesIO
from ._base import *
from django.core.paginator import Paginator
from ..utils import build_fiche_pdf


@login_required
@rh_required
def contractuel_list(request):
    q = request.GET.get('q', '')
    dept = request.GET.get('direction', '')
    statut = request.GET.get('statut', '')
    qs = Contractuel.objects.select_related('poste', 'direction').all()
    manager_direction = get_manager_direction(request.user)
    is_manager = manager_direction is not None
    if manager_direction:
        qs = qs.filter(direction=manager_direction)
    if q:
        qs = qs.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(matricule__icontains=q))
    if dept and not is_manager:
        qs = qs.filter(direction__id=dept)
    if statut:
        qs = qs.filter(statut=statut)
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'SYGEPECO/contractuels/list.html', {
        'contractuels': page_obj, 'page_obj': page_obj,
        'directions': Direction.objects.all(),
        'q': q, 'dept': dept, 'statut': statut,
        'is_manager': is_manager, 'manager_direction': manager_direction,
    })


@login_required
@rh_required
def contractuel_detail(request, pk):
    c = get_object_or_404(Contractuel, pk=pk)
    return render(request, 'SYGEPECO/contractuels/detail.html', {
        'contractuel': c,
        'contrats': c.contrats.all(),
        'presences': c.presences.all()[:10],
        'conges': c.conges.all()[:5],
        'permissions': c.permissions.all()[:5],
    })


@login_required
@rh_required
def contractuel_create(request):
    form = ContractuelForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj = form.save()
        log_action(request.user, f"Creation du contractuel {obj}", 'Contractuel', obj.pk)
        messages.success(request, f"Contractuel {obj.get_full_name()} cree.")
        return redirect('contractuel_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contractuels/form.html',
                  {'form': form, 'titre': 'Nouveau Contractuel'})


@login_required
@rh_required
def contractuel_update(request, pk):
    obj = get_object_or_404(Contractuel, pk=pk)
    form = ContractuelForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        log_action(request.user, f"Modification du contractuel {obj}", 'Contractuel', obj.pk)
        messages.success(request, "Contractuel mis a jour.")
        return redirect('contractuel_detail', pk=obj.pk)
    return render(request, 'SYGEPECO/contractuels/form.html',
                  {'form': form, 'titre': 'Modifier le Contractuel', 'obj': obj})


@login_required
@rh_required
def contractuel_delete(request, pk):
    obj = get_object_or_404(Contractuel, pk=pk)
    if request.method == 'POST':
        nom = obj.get_full_name()
        log_action(request.user, f"Suppression du contractuel {obj}", 'Contractuel', obj.pk)
        obj.delete()
        messages.success(request, f"Contractuel {nom} supprime.")
        return redirect('contractuel_list')
    return render(request, 'SYGEPECO/contractuels/confirm_delete.html', {'obj': obj})


@login_required
@rh_required
def telecharger_profil_agent(request, pk):
    from django.http import Http404
    c = get_object_or_404(Contractuel, pk=pk)
    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else 'ADMINISTRATEUR'
    if role == 'MANAGER':
        direction = getattr(profile, 'direction', None)
        if not direction or c.direction != direction:
            raise Http404
    elif role == 'ENTREPRISE':
        ent = get_entreprise_for_user(request.user)
        if not ent or c.entreprise != ent:
            raise Http404
    buf = build_fiche_pdf(c)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="Fiche_{c.nom}_{c.prenom}.pdf"'
    return resp
