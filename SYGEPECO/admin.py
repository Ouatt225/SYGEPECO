from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import (
    UserProfile, Direction, Poste, TypeContrat,
    Contractuel, Contrat, Presence, Conge, Permission, ActionLog, Entreprise
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display         = ('user', 'role_badge', 'direction_display', 'entreprise', 'telephone')
    list_filter          = ('role',)
    search_fields        = ('user__username', 'user__first_name', 'user__last_name')
    # Charge user + direction + entreprise en 1 requête (évite N+1 sur direction_display)
    list_select_related  = ('user', 'direction', 'entreprise')
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'telephone', 'photo')
        }),
        ('Affectation', {
            'fields': ('direction', 'entreprise'),
            'description': (
                "Pour un Manager : choisir la Direction qu'il supervise. "
                "Pour une Entreprise : choisir l'Entreprise geree."
            ),
        }),
    )

    class Media:
        js = ('admin/js/userprofile_role.js',)

    BADGE_COLORS = {
        'ADMINISTRATEUR': ('#DC2626', '#FEF2F2'),
        'ENTREPRISE':     ('#7C3AED', '#F5F3FF'),
        'MANAGER':        ('#D97706', '#FFFBEB'),
        'EMPLOYE':        ('#059669', '#ECFDF5'),
        'DRH':            ('#DC2626', '#FEF2F2'),
        'RH':             ('#2563EB', '#EFF6FF'),
    }

    @admin.display(description='Rôle')
    def role_badge(self, obj):
        color, bg = self.BADGE_COLORS.get(obj.role, ('#6B7280', '#F9FAFB'))
        return format_html(
            '<span style="padding:3px 10px;border-radius:12px;font-size:12px;'
            'font-weight:600;background:{};color:{};">{}</span>',
            bg, color, obj.get_role_display()
        )

    @admin.display(description='Direction')
    def direction_display(self, obj):
        if obj.role == 'MANAGER' and obj.direction:
            return obj.direction.nom
        return '—'


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'sigle', 'secteur', 'telephone', 'nb_contractuels', 'active')
    list_filter   = ('secteur', 'active')
    search_fields = ('nom', 'sigle')
    list_editable = ('active',)

    def get_queryset(self, request):
        # Annote le nombre de contractuels en 1 seule requête (COUNT groupé)
        return super().get_queryset(request).annotate(
            _nb_contractuels=Count('contractuels', distinct=True),
        )

    @admin.display(description='Agents', ordering='_nb_contractuels')
    def nb_contractuels(self, obj):
        return obj._nb_contractuels


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display         = ('nom', 'responsable', 'nb_contractuels', 'nb_postes', 'created_at')
    search_fields        = ('nom',)
    actions              = ['fusionner_directions']
    # Charge le responsable (FK User) en 1 requête
    list_select_related  = ('responsable',)

    def get_queryset(self, request):
        # Annote les 2 compteurs en 1 seule requête (au lieu de 2N requêtes)
        return super().get_queryset(request).annotate(
            _nb_contractuels=Count('contractuels', distinct=True),
            _nb_postes=Count('postes', distinct=True),
        )

    @admin.display(description='Agents', ordering='_nb_contractuels')
    def nb_contractuels(self, obj):
        return obj._nb_contractuels

    @admin.display(description='Postes', ordering='_nb_postes')
    def nb_postes(self, obj):
        return obj._nb_postes

    @admin.action(description='Fusionner les directions sélectionnées (garder la 1re, supprimer les autres)')
    def fusionner_directions(self, request, queryset):
        dirs = list(queryset.order_by('pk'))
        if len(dirs) < 2:
            self.message_user(request, "Sélectionnez au moins 2 directions.", level='warning')
            return
        target = dirs[0]
        sources = dirs[1:]
        total_c = total_p = total_u = 0
        for src_dir in sources:
            c = Contractuel.objects.filter(direction=src_dir).update(direction=target)
            p = Poste.objects.filter(direction=src_dir).update(direction=target)
            u = UserProfile.objects.filter(direction=src_dir).update(direction=target)
            total_c += c; total_p += p; total_u += u
            src_dir.delete()
        self.message_user(
            request,
            f"Fusion terminée dans « {target.nom} » : "
            f"{total_c} contractuel(s), {total_p} poste(s), {total_u} profil(s) réaffectés. "
            f"{len(sources)} direction(s) supprimée(s).",
            level='success',
        )


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display        = ('titre', 'direction')
    list_filter         = ('direction',)
    search_fields       = ('titre',)
    list_select_related = ('direction',)


@admin.register(TypeContrat)
class TypeContratAdmin(admin.ModelAdmin):
    list_display = ('nom', 'duree_max_jours')


@admin.register(Contractuel)
class ContractuelAdmin(admin.ModelAdmin):
    list_display        = ('matricule', 'nom', 'prenom', 'entreprise', 'direction', 'poste', 'statut', 'date_embauche', 'user')
    list_filter         = ('statut', 'entreprise', 'direction', 'genre')
    search_fields       = ('matricule', 'nom', 'prenom', 'email')
    readonly_fields     = ('created_at', 'updated_at')
    autocomplete_fields = ['user']
    # Évite N+1 sur entreprise, direction, poste, user dans list_display
    list_select_related = ('entreprise', 'direction', 'poste', 'user')

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%"/>', obj.photo.url)
        return "—"
    photo_preview.short_description = "Photo"


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display        = ('contractuel', 'type_contrat', 'date_debut', 'date_fin', 'salaire', 'statut')
    list_filter         = ('statut', 'type_contrat')
    search_fields       = ('contractuel__nom', 'contractuel__prenom', 'contractuel__matricule')
    readonly_fields     = ('created_at',)
    list_select_related = ('contractuel', 'type_contrat')


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display        = ('contractuel', 'date', 'heure_arrivee', 'heure_depart', 'statut')
    list_filter         = ('statut', 'date')
    search_fields       = ('contractuel__nom', 'contractuel__prenom')
    date_hierarchy      = 'date'
    list_select_related = ('contractuel',)


@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display        = ('contractuel', 'type_conge', 'date_debut', 'date_fin', 'statut', 'approuve_par')
    list_filter         = ('statut', 'type_conge')
    search_fields       = ('contractuel__nom', 'contractuel__prenom')
    readonly_fields     = ('created_at', 'updated_at')
    list_select_related = ('contractuel', 'approuve_par')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display        = ('contractuel', 'date_debut', 'date_fin', 'statut', 'approuve_par')
    list_filter         = ('statut', 'date_debut')
    search_fields       = ('contractuel__nom', 'contractuel__prenom')
    readonly_fields     = ('created_at',)
    list_select_related = ('contractuel', 'approuve_par')


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display        = ('utilisateur', 'action', 'modele_concerne', 'created_at')
    list_filter         = ('modele_concerne',)
    search_fields       = ('action', 'utilisateur__username')
    readonly_fields     = ('created_at',)
    list_select_related = ('utilisateur',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Personnalisation de l'interface admin
admin.site.site_header = "SYGEPECO — Administration"
admin.site.site_title = "SYGEPECO"
admin.site.index_title = "Gestion du Personnel Contractuel"
