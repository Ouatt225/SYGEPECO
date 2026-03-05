from django.urls import path
from . import views

urlpatterns = [
    # ─── Dashboard ──────────────────────────────────────────────
    path('', views.dashboard, name='dashboard'),

    # ─── Authentification ───────────────────────────────────────
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),

    # ─── Contractuels ───────────────────────────────────────────
    path('contractuels/', views.contractuel_list, name='contractuel_list'),
    path('contractuels/ajouter/', views.contractuel_create, name='contractuel_create'),
    path('contractuels/<int:pk>/', views.contractuel_detail, name='contractuel_detail'),
    path('contractuels/<int:pk>/modifier/', views.contractuel_update, name='contractuel_update'),
    path('contractuels/<int:pk>/supprimer/', views.contractuel_delete, name='contractuel_delete'),

    # ─── Contrats ───────────────────────────────────────────────
    path('contrats/', views.contrat_list, name='contrat_list'),
    path('contrats/ajouter/', views.contrat_create, name='contrat_create'),
    path('contrats/<int:pk>/', views.contrat_detail, name='contrat_detail'),
    path('contrats/<int:pk>/modifier/', views.contrat_update, name='contrat_update'),
    path('contrats/<int:pk>/renouveler/', views.contrat_renouveler, name='contrat_renouveler'),

    # ─── Présences ──────────────────────────────────────────────
    path('presences/', views.presence_list, name='presence_list'),
    path('presences/enregistrer/', views.presence_create, name='presence_create'),
    path('presences/rapport/', views.presence_rapport, name='presence_rapport'),

    # ─── Congés ─────────────────────────────────────────────────
    path('conges/', views.conge_list, name='conge_list'),
    path('conges/demander/', views.conge_create, name='conge_create'),
    path('conges/<int:pk>/', views.conge_detail, name='conge_detail'),
    path('conges/<int:pk>/approuver/', views.conge_approuver, name='conge_approuver'),
    path('conges/<int:pk>/rejeter/', views.conge_rejeter, name='conge_rejeter'),

    # ─── Permissions ────────────────────────────────────────────
    path('permissions/', views.permission_list, name='permission_list'),
    path('permissions/demander/', views.permission_create, name='permission_create'),
    path('permissions/<int:pk>/', views.permission_detail, name='permission_detail'),
    path('permissions/<int:pk>/approuver/', views.permission_approuver, name='permission_approuver'),
    path('permissions/<int:pk>/rejeter/', views.permission_rejeter, name='permission_rejeter'),

    # ─── Calendrier ─────────────────────────────────────────────
    path('calendrier/', views.calendrier, name='calendrier'),

    # ─── Rapports ───────────────────────────────────────────────
    path('rapports/', views.rapports, name='rapports'),
    path('rapports/exporter/', views.rapports_exporter, name='rapports_exporter'),
    path('rapports/exporter/conges/', views.rapports_exporter_conges, name='rapports_exporter_conges'),
    path('rapports/exporter/permissions/', views.rapports_exporter_permissions, name='rapports_exporter_permissions'),
    path('rapports/exporter/contractuels/', views.rapports_exporter_contractuels, name='rapports_exporter_contractuels'),

    # ─── Historique ─────────────────────────────────────────────
    path('historique/', views.historique, name='historique'),

    # ─── API JSON ───────────────────────────────────────────────
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/calendrier-events/', views.api_calendrier_events, name='api_calendrier_events'),
    path('api/chart-presences/', views.api_chart_presences, name='api_chart_presences'),

    # ─── Entreprises ────────────────────────────────────────────
    path('entreprises/', views.entreprise_list, name='entreprise_list'),
    path('entreprises/ajouter/', views.entreprise_create, name='entreprise_create'),
    path('entreprises/<int:pk>/', views.entreprise_detail, name='entreprise_detail'),
    path('entreprises/<int:pk>/modifier/', views.entreprise_update, name='entreprise_update'),
    path('entreprises/<int:pk>/supprimer/', views.entreprise_delete, name='entreprise_delete'),

    # ─── Espace Entreprise ───────────────────────────────────────
    path('entreprise-espace/', views.entreprise_espace_home, name='entreprise_espace_home'),
    path('entreprise-espace/agents/', views.entreprise_espace_agents, name='entreprise_espace_agents'),
    path('entreprise-espace/conges/', views.entreprise_espace_conges, name='entreprise_espace_conges'),
    path('entreprise-espace/permissions/', views.entreprise_espace_permissions, name='entreprise_espace_permissions'),
    path('entreprise-espace/presences/', views.entreprise_espace_presences, name='entreprise_espace_presences'),

    # ─── Espace Contractuel ──────────────────────────────────────
    path('espace/', views.espace_home, name='espace_home'),
    path('espace/profil/', views.espace_profil, name='espace_profil'),
    path('espace/profil/modifier/', views.espace_profil_modifier, name='espace_profil_modifier'),
    path('espace/mes-conges/', views.espace_mes_conges, name='espace_mes_conges'),
    path('espace/mes-conges/demander/', views.espace_demander_conge, name='espace_demander_conge'),
    path('espace/mes-permissions/', views.espace_mes_permissions, name='espace_mes_permissions'),
    path('espace/mes-permissions/demander/', views.espace_demander_permission, name='espace_demander_permission'),
    path('espace/mon-contrat/', views.espace_mon_contrat, name='espace_mon_contrat'),
    path('espace/mes-presences/', views.espace_mes_presences, name='espace_mes_presences'),
]
