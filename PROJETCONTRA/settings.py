"""
Django settings for PROJETCONTRA project — SYGEPECO
Gestion du Personnel Contractuel
"""

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=lambda v: [h.strip() for h in v.split(',')]
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'SYGEPECO',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'SYGEPECO.middleware.RoleRoutingMiddleware',
]

ROOT_URLCONF = 'PROJETCONTRA.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'SYGEPECO' / 'templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'SYGEPECO.context_processors.global_context',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'PROJETCONTRA.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     config('DB_NAME',     default='sygepeco_db'),
        'USER':     config('DB_USER',     default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'SYGEPECO' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# ─── Cache ──────────────────────────────────────────────────────────────────
# LocMemCache en développement. En production, remplacer par Redis :
#   BACKEND: 'django.core.cache.backends.redis.RedisCache'
#   LOCATION: config('REDIS_URL', default='redis://127.0.0.1:6379/1')
CACHES = {
    'default': {
        # DatabaseCache : utilise PostgreSQL (pas de service supplementaire).
        # Shared entre tous les workers -> compteurs rate-limit coherents.
        # Initialisation : python manage.py createcachetable
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'sygepeco_cache',
    }
}


# ─── Media proteges ──────────────────────────────────────────────────────────
# Les fichiers /media/ sont servis par SYGEPECO/views/media_serve.py
# qui applique @login_required + controle de role sur les dossiers sensibles.
#
# Production (Nginx) : activer X-Accel-Redirect pour efficacite maximale.
#   SYGEPECO_USE_XACCEL = True   # decommenter en production
#
# Configurer Nginx :
#   location /protected-media/ {
#       internal;
#       alias /chemin/vers/media/;
#   }
#   location /media/ {
#       proxy_pass http://django;   # passe par Django (auth verifiee)
#   }
# ─── Rate limiting ───────────────────────────────────────────────────────────
# Implementation manuelle dans SYGEPECO/views/auth.py (_rl_is_blocked / _rl_record).
# Cles cache : 'rl:login:ip:<ip>' et 'rl:login:user:<username>' (TTL 300s).
# Pour passer a Redis en production, seul le backend CACHES doit changer.

# ─── Sécurité production ────────────────────────────────────────────────────
# Ces paramètres s'activent automatiquement hors mode DEBUG.
# En développement (DEBUG=True) ils sont désactivés pour ne pas bloquer HTTP.
if not DEBUG:
    # HTTPS obligatoire
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cookies sécurisés (transmis uniquement via HTTPS)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS : forcer HTTPS pendant 1 an (31 536 000 s), inclure sous-domaines
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Empêcher le sniffing de type MIME
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Empêcher le rendu dans un iframe (clickjacking)
    X_FRAME_OPTIONS = 'DENY'


# ─── Email ──────────────────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='SYGEPECO <noreply@sygepeco.ci>',
)
PASSWORD_RESET_TIMEOUT = 3600  # 1 heure

# Auth
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# ─── Logging ───────────────────────────────────────────────────────────────
import os as _os
_LOG_DIR = BASE_DIR / 'logs'
_LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'WARNING',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(_LOG_DIR / 'sygepeco.log'),
            'maxBytes': 5 * 1024 * 1024,   # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'DEBUG',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'SYGEPECO': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

