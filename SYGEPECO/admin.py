from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Direction, Poste, TypeContrat,
    Contractuel, Contrat, Presence, Conge, Permission, ActionLog, Entreprise
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'role_badge', 'direction_display', 'entreprise', 'telephone')
    list_filter   = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
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

    @admin.display(description='Agents actifs')
    def nb_contractuels(self, obj):
        return obj.nb_contractuels()


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'responsable', 'created_at')
    search_fields = ('nom',)


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'direction')
    list_filter = ('direction',)
    search_fields = ('titre',)


@admin.register(TypeContrat)
class TypeContratAdmin(admin.ModelAdmin):
    list_display = ('nom', 'duree_max_jours')


@admin.register(Contractuel)
class ContractuelAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom', 'entreprise', 'direction', 'poste', 'statut', 'date_embauche', 'user')
    list_filter = ('statut', 'entreprise', 'direction', 'genre')
    search_fields = ('matricule', 'nom', 'prenom', 'email')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['user']

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%"/>', obj.photo.url)
        return "—"
    photo_preview.short_description = "Photo"


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ('contractuel', 'type_contrat', 'date_debut', 'date_fin', 'salaire', 'statut')
    list_filter = ('statut', 'type_contrat')
    search_fields = ('contractuel__nom', 'contractuel__prenom', 'contractuel__matricule')
    readonly_fields = ('created_at',)


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('contractuel', 'date', 'heure_arrivee', 'heure_depart', 'statut')
    list_filter = ('statut', 'date')
    search_fields = ('contractuel__nom', 'contractuel__prenom')
    date_hierarchy = 'date'


@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display = ('contractuel', 'type_conge', 'date_debut', 'date_fin', 'statut', 'approuve_par')
    list_filter = ('statut', 'type_conge')
    search_fields = ('contractuel__nom', 'contractuel__prenom')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('contractuel', 'date_debut', 'date_fin', 'statut', 'approuve_par')
    list_filter = ('statut', 'date_debut')
    search_fields = ('contractuel__nom', 'contractuel__prenom')
    readonly_fields = ('created_at',)


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'modele_concerne', 'created_at')
    list_filter = ('modele_concerne',)
    search_fields = ('action', 'utilisateur__username')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Personnalisation de l'interface admin
admin.site.site_header = "SYGEPECO — Administration"
admin.site.site_title = "SYGEPECO"
admin.site.index_title = "Gestion du Personnel Contractuel"
