import os
from django.contrib import messages
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "widget_tweaks",
    "repuestocontrol.core",
    "repuestocontrol.inventario",
    "repuestocontrol.ventas",
    "repuestocontrol.dashboard",
    "repuestocontrol.catalogo_publico",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "repuestocontrol.core.middleware.RoleMiddleware",
]

ROOT_URLCONF = "repuestocontrol.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR.parent / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "repuestocontrol.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "repuestocontrol"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": os.getenv("DB_SSL_MODE", "prefer"),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = "/app/staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/app/media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "core.Usuario"

LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "core:login"

MESSAGE_TAGS = {
    messages.SUCCESS: "alert-success",
    messages.ERROR: "alert-danger",
    messages.WARNING: "alert-warning",
    messages.INFO: "alert-info",
}

# ============================================
# CONFIGURACIÓN DE EMAIL - FACTURACIÓN ELECTRÓNICA
# ============================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False") == "True"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "30"))
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", os.getenv("EMAIL_HOST_USER", "noreply@empresa.com")
)

# ============================================
# CONFIGURACIÓN DE SEGURIDAD - PRODUCCIÓN
# ============================================

# CSRF
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Session
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# SSL/HTTPS
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Content Security Policy
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# HSTS (solo en producción)
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

# Crear directorio de logs si no existe
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asmodule} {processctime} {:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "repuestocontrol": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ============================================
# CACHE
# ============================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# ============================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ============================================
# CONFIGURACIÓN DE FACTURACIÓN ELECTRÓNICA
# ============================================

# Ruta de certificados digitales
CERTIFICADOS_DIR = BASE_DIR / "certificados"

# Validación XSD
XSD_DIR = BASE_DIR / "xsd"

# Timeout para conexiones SRI (segundos)
SRI_TIMEOUT = int(os.getenv("SRI_TIMEOUT", "60"))

# Reintentos SRI
SRI_REINTENTOS = int(os.getenv("SRI_REINTENTOS", "3"))

# ============================================
# SEGURIDAD ADICIONAL
# ============================================

# Longitud mínima de contraseñas
AUTH_PASSWORD_MIN_LENGTH = 8

# Permite autenticación en múltiples dispositivos
AUTH_REMOTE_USER = False
