# views/__init__.py — Re-exporte tout pour que urls.py reste inchange
from .auth import login_view, logout_view, changer_mot_de_passe
from .dashboard import dashboard
from .contractuels import (
    contractuel_list, contractuel_detail, contractuel_create,
    contractuel_update, contractuel_delete, telecharger_profil_agent,
)
from .contrats import (
    contrat_list, contrat_detail, contrat_create, contrat_update, contrat_renouveler,
)
from .presences import presence_list, presence_create, presence_rapport
from .conges import (
    conge_list, conge_detail, conge_create, conge_approuver, conge_rejeter,
    conge_valider_manager, conge_rejeter_manager,
    entreprise_conge_approuver, entreprise_conge_rejeter,
    conge_document_medical,
)
from .permissions import (
    permission_list, permission_detail, permission_create,
    permission_approuver, permission_rejeter,
    entreprise_permission_approuver, entreprise_permission_rejeter,
)
from .rapports import (
    calendrier, rapports, rapports_exporter,
    rapports_exporter_conges, rapports_exporter_permissions,
    rapports_exporter_contractuels, historique,
)
from .api import (
    api_dashboard_stats, api_calendrier_events,
    api_chart_presences, api_postes_entreprise,
    api_conges_notifs,
)
from .espace import (
    espace_home, espace_profil, espace_profil_modifier,
    espace_mes_conges, espace_demander_conge,
    espace_mes_permissions, espace_demander_permission,
    espace_mon_contrat, espace_mes_presences,
    espace_telecharger_profil,
)
from .entreprise import (
    entreprise_list, entreprise_detail, entreprise_create,
    entreprise_update, entreprise_delete,
    entreprise_espace_home, entreprise_espace_agents,
    entreprise_espace_conges, entreprise_espace_permissions,
    entreprise_espace_presences, entreprise_espace_presence_create,
    entreprise_espace_contrats, entreprise_espace_rapports,
    entreprise_export_presences, entreprise_export_conges,
    entreprise_export_permissions, entreprise_export_agents,
)

from .media_serve import protected_media
