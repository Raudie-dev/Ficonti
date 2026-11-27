"""
Configuración de Django para el proyecto FICONTI.

Sistema de control tributario para contadores en Venezuela.
Cada módulo del sistema es una aplicación independiente dentro de ``apps/``.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _cargar_env_fallback(ruta_env):
    """Carga variables de un archivo .env si python-dotenv no está instalado."""
    if not ruta_env.is_file():
        return
    with ruta_env.open(encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith('#'):
                continue
            if linea.startswith('export '):
                linea = linea[7:].strip()
            if '=' not in linea:
                continue
            clave, valor = linea.split('=', 1)
            clave = clave.strip()
            valor = valor.strip()
            if not clave:
                continue
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ("'", '"'):
                valor = valor[1:-1]
            else:
                for idx, ch in enumerate(valor):
                    if ch == '#' and (idx == 0 or valor[idx - 1].isspace()):
                        valor = valor[:idx].rstrip()
                        break
            os.environ.setdefault(clave, valor)


try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    _cargar_env_fallback(BASE_DIR / '.env')


def env_bool(nombre, defecto=False):
    valor = os.environ.get(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in ('1', 'true', 'si', 'sí', 'yes', 'on')


# Entorno de ejecución: 'development' (desarrollo) o 'production' (producción)
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development').strip().lower()
IS_PRODUCTION = DJANGO_ENV in ('production', 'produccion', 'producción', 'prod')

# ADVERTENCIA: en producción defina DJANGO_SECRET_KEY y DJANGO_ENV=production.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-6a#e6xlrlj)g)@8n(ozv6+q#oj*vkanb^ry01x$b$ekhc@c1qo',
)
# En producción DEBUG siempre permanece desactivado.
DEBUG = False if IS_PRODUCTION else env_bool('DJANGO_DEBUG', False)

DEFAULT_ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'testserver',
    'ficonti.net',
    'www.ficonti.net',
    '.ficonti.net',
    'demos.raudie.net',
    '.demos.raudie.net',
]
_env_hosts = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
ALLOWED_HOSTS = list(dict.fromkeys(DEFAULT_ALLOWED_HOSTS + _env_hosts))

DEFAULT_CSRF_TRUSTED_ORIGINS = [
    'https://ficonti.net',
    'https://www.ficonti.net',
    'http://ficonti.net',
    'http://www.ficonti.net',
    'https://*.ficonti.net',
    'http://*.ficonti.net',
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
# - En desarrollo (DJANGO_ENV=development): usa SQLite local (db.sqlite3).
# - En producción (DJANGO_ENV=production): usa la base de datos SQL configurada
#   mediante DB_* (o DATABASE_URL si se define).
if IS_PRODUCTION:
    _database_url = os.environ.get('DATABASE_URL', '').strip()
    if _database_url:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                _database_url,
                conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', '60')),
                conn_health_checks=True,
            )
        }
    else:
        _db_engine = os.environ.get('DB_ENGINE', 'django.db.backends.mysql').strip()
        _db_config = {
            'ENGINE': _db_engine,
            'NAME': os.environ.get('DB_NAME', '').strip(),
            'USER': os.environ.get('DB_USER', '').strip(),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost').strip(),
            'PORT': os.environ.get('DB_PORT', '3306').strip(),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
        }
        if 'mysql' in _db_engine:
            _db_config['OPTIONS'] = {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            }
        DATABASES = {'default': _db_config}
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

PASSWORD_HASHERS = [
    'tributove.hashers.FicontiPBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
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

# ---------------------------------------------------------------------------
# Correo electrónico (SMTP SSL/TLS para notificaciones y recuperación de clave)
# ---------------------------------------------------------------------------
EMAIL_HOST = os.environ.get('EMAIL_HOST', '').strip()
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', EMAIL_PORT == 465)
EMAIL_USE_TLS = False if EMAIL_USE_SSL else env_bool('EMAIL_USE_TLS', EMAIL_PORT == 587)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '15'))
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'FICONTI <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else 'notificaciones@ficonti.net',
).strip()
SERVER_EMAIL = DEFAULT_FROM_EMAIL

_default_email_backend = (
    'django.core.mail.backends.smtp.EmailBackend'
    if (EMAIL_HOST and EMAIL_HOST_USER)
    else 'django.core.mail.backends.console.EmailBackend'
)
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', _default_email_backend).strip()

# Vigencia de enlaces de recuperación de clave (24 horas por defecto)
PASSWORD_RESET_TIMEOUT = int(os.environ.get('PASSWORD_RESET_TIMEOUT', str(60 * 60 * 24)))

# Datos del sistema
TRIBUTOVE = {
    'NOMBRE': 'FICONTI',
    'LEMA': 'Gestión fiscal · Venezuela',
    'MAX_EMPRESAS': 200,
    'DIAS_POR_PAGO': 30,
}
