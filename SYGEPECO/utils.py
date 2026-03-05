from django.http import HttpResponse
from .models import ActionLog, Contractuel, Presence, Conge, Permission


def log_action(user, action, modele='', objet_id=None, details=''):
    ActionLog.objects.create(
        utilisateur=user,
        action=action,
        modele_concerne=modele,
        objet_id=objet_id,
        details=details,
    )


def export_presences_excel(mois, annee):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return HttpResponse("openpyxl non installé.", status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Presences {mois:02d}-{annee}"

    # Styles
    header_fill = PatternFill("solid", fgColor="1A1A2E")
    header_font = Font(bold=True, color="D4A853", size=11)
    border = Border(
        left=Side(style='thin', color='333344'),
        right=Side(style='thin', color='333344'),
        top=Side(style='thin', color='333344'),
        bottom=Side(style='thin', color='333344'),
    )

    # En-têtes
    headers = ['Matricule', 'Nom', 'Prénom', 'Département', 'Présents', 'Absents', 'Retards', 'Taux (%)']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border

    ws.row_dimensions[1].height = 22

    # Données
    contractuels = Contractuel.objects.filter(statut='ACTIF').select_related('departement')
    for row, c in enumerate(contractuels, 2):
        presences = Presence.objects.filter(
            contractuel=c, date__month=mois, date__year=annee
        )
        nb_present = presences.filter(statut='PRESENT').count()
        nb_absent = presences.filter(statut='ABSENT').count()
        nb_retard = presences.filter(statut='RETARD').count()
        total = nb_present + nb_absent + nb_retard
        taux = round(nb_present / total * 100, 1) if total > 0 else 0

        data = [c.matricule, c.nom, c.prenom,
                c.departement.nom if c.departement else '—',
                nb_present, nb_absent, nb_retard, taux]
        for col, val in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = border
            cell.alignment = Alignment(horizontal='center' if col > 3 else 'left')

    # Largeurs colonnes
    col_widths = [14, 20, 20, 20, 12, 12, 12, 12]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="presences_{mois:02d}_{annee}.xlsx"'
    wb.save(response)
    return response


def export_conges_excel(mois=None, annee=None):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    label = f"{mois:02d}-{annee}" if mois and annee else "Tous"
    ws.title = f"Conges {label}"

    header_fill = PatternFill("solid", fgColor="1A1A2E")
    header_font = Font(bold=True, color="D4A853", size=11)
    thin = Side(style='thin', color='333344')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers = ['Matricule', 'Nom', 'Prénom', 'Entreprise', 'Type', 'Date début', 'Date fin', 'Jours', 'Statut', 'Approuvé par']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    ws.row_dimensions[1].height = 22

    qs = Conge.objects.select_related('contractuel', 'contractuel__entreprise', 'approuve_par')
    if mois and annee:
        qs = qs.filter(date_debut__month=mois, date_debut__year=annee)
    qs = qs.order_by('contractuel__nom')

    STATUS_LABELS = {'EN_ATTENTE': 'En attente', 'APPROUVE': 'Approuvé', 'REJETE': 'Rejeté'}

    for row, c in enumerate(qs, 2):
        nb_jours = (c.date_fin - c.date_debut).days + 1 if c.date_fin and c.date_debut else ''
        approuve = f"{c.approuve_par.get_full_name() or c.approuve_par.username}" if c.approuve_par else '—'
        data = [
            c.contractuel.matricule,
            c.contractuel.nom,
            c.contractuel.prenom,
            c.contractuel.entreprise.nom if c.contractuel.entreprise else '—',
            c.get_type_conge_display() if hasattr(c, 'get_type_conge_display') else c.type_conge,
            c.date_debut.strftime('%d/%m/%Y') if c.date_debut else '',
            c.date_fin.strftime('%d/%m/%Y') if c.date_fin else '',
            nb_jours,
            STATUS_LABELS.get(c.statut, c.statut),
            approuve,
        ]
        fill_color = "F0FFF4" if c.statut == 'APPROUVE' else ("FFF0F0" if c.statut == 'REJETE' else "FFFBF0")
        row_fill = PatternFill("solid", fgColor=fill_color)
        for col, val in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = border
            cell.fill = row_fill
            cell.alignment = Alignment(horizontal='center' if col > 3 else 'left', vertical='center')

    col_widths = [14, 20, 20, 22, 16, 14, 14, 8, 14, 22]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fname = f"conges_{mois:02d}_{annee}.xlsx" if mois and annee else "conges_tous.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    wb.save(response)
    return response


def export_permissions_excel(mois=None, annee=None):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    label = f"{mois:02d}-{annee}" if mois and annee else "Tous"
    ws.title = f"Permissions {label}"

    header_fill = PatternFill("solid", fgColor="1A1A2E")
    header_font = Font(bold=True, color="D4A853", size=11)
    thin = Side(style='thin', color='333344')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers = ['Matricule', 'Nom', 'Prénom', 'Entreprise', 'Date', 'Heure début', 'Heure fin', 'Motif', 'Statut', 'Approuvé par']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    ws.row_dimensions[1].height = 22

    qs = Permission.objects.select_related('contractuel', 'contractuel__entreprise', 'approuve_par')
    if mois and annee:
        qs = qs.filter(date__month=mois, date__year=annee)
    qs = qs.order_by('contractuel__nom')

    STATUS_LABELS = {'EN_ATTENTE': 'En attente', 'APPROUVE': 'Approuvé', 'REJETE': 'Rejeté'}

    for row, p in enumerate(qs, 2):
        approuve = f"{p.approuve_par.get_full_name() or p.approuve_par.username}" if p.approuve_par else '—'
        data = [
            p.contractuel.matricule,
            p.contractuel.nom,
            p.contractuel.prenom,
            p.contractuel.entreprise.nom if p.contractuel.entreprise else '—',
            p.date.strftime('%d/%m/%Y') if p.date else '',
            p.heure_debut.strftime('%H:%M') if p.heure_debut else '',
            p.heure_fin.strftime('%H:%M') if p.heure_fin else '',
            p.motif or '—',
            STATUS_LABELS.get(p.statut, p.statut),
            approuve,
        ]
        fill_color = "F0FFF4" if p.statut == 'APPROUVE' else ("FFF0F0" if p.statut == 'REJETE' else "FFFBF0")
        row_fill = PatternFill("solid", fgColor=fill_color)
        for col, val in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = border
            cell.fill = row_fill
            cell.alignment = Alignment(horizontal='center' if col > 3 else 'left', vertical='center')

    col_widths = [14, 20, 20, 22, 14, 12, 12, 30, 14, 22]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fname = f"permissions_{mois:02d}_{annee}.xlsx" if mois and annee else "permissions_tous.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    wb.save(response)
    return response


def export_contractuels_excel():
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Contractuels actifs"

    header_fill = PatternFill("solid", fgColor="1A1A2E")
    header_font = Font(bold=True, color="D4A853", size=11)
    thin = Side(style='thin', color='333344')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    headers = ['Matricule', 'Nom', 'Prénom', 'Genre', 'Entreprise', 'Département', 'Poste', 'Email', 'Téléphone', 'Date embauche', 'Statut']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    ws.row_dimensions[1].height = 22

    qs = Contractuel.objects.filter(statut='ACTIF').select_related(
        'entreprise', 'departement', 'poste'
    ).order_by('entreprise__nom', 'nom')

    for row, c in enumerate(qs, 2):
        fill_color = "F8F9FF" if row % 2 == 0 else "FFFFFF"
        row_fill = PatternFill("solid", fgColor=fill_color)
        data = [
            c.matricule,
            c.nom,
            c.prenom,
            'Homme' if c.genre == 'M' else 'Femme',
            c.entreprise.nom if c.entreprise else '—',
            c.departement.nom if c.departement else '—',
            c.poste.titre if c.poste else '—',
            c.email or '—',
            c.telephone or '—',
            c.date_embauche.strftime('%d/%m/%Y') if c.date_embauche else '',
            'Actif',
        ]
        for col, val in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = border
            cell.fill = row_fill
            cell.alignment = Alignment(horizontal='center' if col in (4, 10, 11) else 'left', vertical='center')

    col_widths = [14, 20, 20, 10, 22, 20, 20, 28, 16, 14, 10]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="contractuels_actifs.xlsx"'
    wb.save(response)
    return response
