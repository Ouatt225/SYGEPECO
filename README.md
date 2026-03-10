# SYGEPECO — Système de Gestion du Personnel Contractuel

> Application web Django de gestion RH multi-entreprises, multi-rôles.
> Développée pour le suivi des contractuels, congés, présences et permissions.

---

## Fonctionnalités principales

| Module | Description |
|--------|-------------|
| **Contractuels** | Fiche complète (matricule, poste, direction, photo, historique) |
| **Contrats** | Suivi CDI/CDD/Stage avec renouvellement et alertes expiration |
| **Présences** | Pointage quotidien, rapport mensuel par direction |
| **Congés** | Workflow EN_ATTENTE → Manager → DRH/RH → APPROUVÉ/REJETÉ |
| **Permissions** | Demandes horaires avec validation hiérarchique |
| **Rapports** | Export Excel (contractuels, congés, présences, permissions) |
| **Calendrier** | Vue FullCalendar des absences et événements RH |
| **Historique** | Journal d'audit de toutes les actions RH |

## Rôles et accès

| Rôle | Accès |
|------|-------|
| `ADMINISTRATEUR` | Accès total — `/dashboard/` |
| `DRH` | Accès total + approbation finale congés |
| `RH` | Accès total sans suppression |
| `MANAGER` | Voit uniquement sa direction — pré-validation congés |
| `ENTREPRISE` | Espace dédié `/entreprise-espace/` — ses agents uniquement |
| `EMPLOYE` | Espace personnel `/espace/` — ses propres données uniquement |

---

## Prérequis

- Python 3.11+
- pip

## Installation (développement)

```bash
# 1. Cloner le dépôt
git clone <URL_DU_REPO>
cd PROJETCONTRA

# 2. Environnement virtuel
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Dépendances
pip install -r requirements.txt

# 4. Variables d'environnement
copy .env.example .env
# Éditer .env avec vos valeurs réelles

# 5. Base de données
python manage.py migrate

# 6. Super-utilisateur
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
```

Accès : http://127.0.0.1:8000/auth/login/

---

## Structure du projet

```
PROJETCONTRA/
├── PROJETCONTRA/
│   ├── settings.py          # Configuration Django (via .env)
│   ├── urls.py              # URL racine
│   ├── wsgi.py
│   └── asgi.py
├── SYGEPECO/
│   ├── models.py            # 10 modèles Django
│   ├── admin.py             # Interface admin personnalisée
│   ├── urls.py              # Toutes les URLs de l'app
│   ├── forms.py             # Formulaires ModelForm
│   ├── decorators.py        # @rh_required, @contractuel_required, etc.
│   ├── middleware.py        # RoleRoutingMiddleware
│   ├── context_processors.py # Compteurs de notifications (avec cache)
│   ├── constants.py         # Constantes partagées (rôles, statuts)
│   ├── utils.py             # Helpers : export Excel, calculs stats
│   ├── views/
│   │   ├── _base.py         # Helpers partagés entre vues
│   │   ├── auth.py          # Login / logout / mot de passe
│   │   ├── dashboard.py     # KPIs et tableau de bord
│   │   ├── contractuels.py  # CRUD contractuels
│   │   ├── contrats.py      # CRUD contrats
│   │   ├── presences.py     # Pointage et rapports
│   │   ├── conges.py        # Demandes et workflow congés
│   │   ├── permissions.py   # Demandes et workflow permissions
│   │   ├── rapports.py      # Exports Excel
│   │   ├── entreprise.py    # Espace entreprise
│   │   ├── espace.py        # Espace contractuel (self-service)
│   │   ├── api.py           # Endpoints JSON (dashboard, calendrier, notifs)
│   │   └── media_serve.py   # Médias protégés (justificatifs médicaux)
│   ├── migrations/          # Migrations Django
│   ├── static/SYGEPECO/
│   │   ├── css/             # main.css, dashboard.css, components.css
│   │   └── js/              # main.js, notifications.js, charts.js
│   └── templates/SYGEPECO/
│       ├── base.html        # Layout RH/Admin
│       ├── espace/          # Layout espace contractuel
│       ├── entreprise_espace/ # Layout espace entreprise
│       └── ...              # Templates par module
├── logs/                    # Logs rotatifs (créé automatiquement)
├── media/                   # Fichiers uploadés (photos, justificatifs)
├── manage.py
├── requirements.txt
└── .env                     # Variables d'environnement (NON commité)
```

---

## Variables d'environnement (`.env`)

Voir `.env.example` pour la liste complète.

| Variable | Exemple | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-...` | Clé secrète Django |
| `DEBUG` | `False` | Toujours `False` en production |
| `ALLOWED_HOSTS` | `monsite.com,www.monsite.com` | Domaines autorisés |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | URL de connexion DB |

---

## API JSON interne

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/dashboard-stats/` | GET | KPIs du dashboard (contractuels, congés, présences) |
| `/api/calendrier-events/` | GET | Événements pour FullCalendar |
| `/api/chart-presences/` | GET | Données graphique présences (12 derniers mois) |
| `/api/conges/notifs/` | GET | Notifications congés imminents (J-7, J-1) |
| `/api/postes-entreprise/` | GET | Postes filtrés par entreprise (AJAX formulaire) |

Toutes les routes requièrent une session authentifiée (`@login_required`).

---

## Déploiement (production)

**Prérequis supplémentaires :**
- PostgreSQL (remplacer SQLite)
- Nginx (servir les fichiers statiques et médias)
- Gunicorn (serveur WSGI)

```bash
# Collecte des fichiers statiques
python manage.py collectstatic --no-input

# Lancer avec Gunicorn
gunicorn PROJETCONTRA.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

**Checklist production :**
- [ ] `DEBUG=False` dans `.env`
- [ ] `SECRET_KEY` unique et complexe (50+ caractères)
- [ ] `ALLOWED_HOSTS` configuré avec le vrai domaine
- [ ] PostgreSQL configuré
- [ ] Nginx configuré pour `/static/` et `/media/`
- [ ] HTTPS activé (Let's Encrypt)
- [ ] `logs/` avec rotation configurée

---

## Logs

Les logs applicatifs sont écrits dans `logs/sygepeco.log` (rotation automatique, max 5 Mo × 5 fichiers).

```bash
# Suivre les logs en temps réel
tail -f logs/sygepeco.log
```

Niveaux : `DEBUG` en développement, `INFO` en production.

---

## Licence

Usage interne — Tous droits réservés.
