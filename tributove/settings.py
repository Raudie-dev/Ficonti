"""
Configuración de Django para el proyecto FICONTI.

Sistema de control tributario para contadores en Venezuela.
Cada módulo del sistema es una aplicación independiente dentro de ``apps/``.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


def env_bool(nombre, defecto=False):
    valor = os.environ.get(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in ('1', 'true', 'si', 'sí', 'yes', 'on')


# ADVERTENCIA: en producción defina DJANGO_SECRET_KEY y DJANGO_DEBUG=0.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-6a#e6xlrlj)g)@8n(ozv6+q#oj*vkanb^ry01x$b$ekhc@c1qo',
)
DEBUG = env_bool('DJANGO_DEBUG', True)

DEFAULT_ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'testserver',
    'demos.raudie.net',
    '.demos.raudie.net',
]
_env_hosts = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
ALLOWED_HOSTS = list(dict.fromkeys(DEFAULT_ALLOWED_HOSTS + _env_hosts))

DEFAULT_CSRF_TRUSTED_ORIGINS = [
    'http://0.0.0.0:5555',
    'http://127.0.0.1:5555',
    'http://localhost:5555',
    'http://0.0.0.0:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://demos.raudie.net',
    'http://demos.raudie.net',
    'https://demos.raudie.net:5555',
    'http://demos.raudie.net:5555',
    'https://*.raudie.net',
    'http://*.raudie.net',
]
_env_csrf = [o.strip() for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(DEFAULT_CSRF_TRUSTED_ORIGINS + _env_csrf))

# Configuración de proxy inverso para validar CSRF y HTTPS adecuadamente
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Compatibilidad de cookies CSRF y sesión entre navegadores y proxies
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Vista personalizada para manejo resiliente de errores CSRF
CSRF_FAILURE_VIEW = 'apps.core.views.csrf_failure_view'


# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

# Aplicaciones base del sistema
SISTEMA_APPS = [
    'apps.core',
    'apps.usuarios',
    'apps.superadmin',
    'apps.suscripciones',
    'apps.empresas',
]

# Un módulo fiscal = una aplicación
MODULOS_APPS = [
    'apps.planificacion',
    'apps.calculo_ari',
    'apps.estimada_islr',
    'apps.retenciones_islr',
    'apps.retenciones_iva',
    'apps.calendario',
    'apps.sanciones_cot',
    'apps.impuesto_diferido',
    'apps.grandes_patrimonios',
    'apps.conciliacion',
    'apps.auditoria_ingresos',
    'apps.control_bancario',
    'apps.ajuste_inicial',
    'apps.cedula_fiscal',
    'apps.conciliacion_islr',
    'apps.precios_transferencia',
]

INSTALLED_APPS = DJANGO_APPS + SISTEMA_APPS + MODULOS_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.superadmin.middleware.SuperAdminMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tributove.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.sistema',
                'apps.empresas.context_processors.empresa_activa',
                'apps.superadmin.context_processors.superadmin',
            ],
        },
    },
]

WSGI_APPLICATION = 'tributove.wsgi.application'


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
_database_url = os.environ.get('DATABASE_URL', '').strip()
if _database_url:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(_database_url, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------
# Tabla propia de usuarios normales (contadores).
AUTH_USER_MODEL = 'usuarios.Usuario'
# Los super administradores viven en otra tabla (apps.superadmin.SuperAdmin)
# y usan su propia sesión (ver apps/superadmin/middleware.py).

LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'core:inicio'
LOGOUT_REDIRECT_URL = 'usuarios:login'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'apps.core.validators.LetrasYNumerosValidator'},
]

# Bloqueo temporal tras intentos fallidos de ingreso
LOGIN_MAX_INTENTOS = 5
LOGIN_BLOQUEO_SEGUNDOS = 30

SESSION_COOKIE_AGE = 60 * 60 * 10  # 10 horas


# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'es-ve'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Archivos estáticos
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Los módulos guardan su información en el servidor; algunos (p. ej. la
# conciliación bancaria) pueden enviar documentos grandes.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Mensajes -> notificaciones tipo toast de Bootstrap
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: 'secondary',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

# Datos del sistema
TRIBUTOVE = {
    'NOMBRE': 'FICONTI',
    'LEMA': 'Gestión fiscal · Venezuela',
    'MAX_EMPRESAS': 200,
    'DIAS_POR_PAGO': 30,
}
