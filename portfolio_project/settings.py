"""
Django settings for portfolio_project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-me')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
VERCEL_ENV = os.getenv('VERCEL_ENV', '')
VERCEL_URL = os.getenv('VERCEL_URL', '')
IS_VERCEL = bool(VERCEL_ENV or VERCEL_URL)
ADMIN_URL = os.getenv('ADMIN_URL', 'admin').strip('/') + '/'
SITE_DOMAIN = os.getenv('SITE_DOMAIN', '').strip()
SITE_NAME = os.getenv('SITE_NAME', 'Open Portfolio').strip()


def csv_env(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


ALLOWED_HOSTS = csv_env('ALLOWED_HOSTS', 'localhost,127.0.0.1')
if VERCEL_URL:
    ALLOWED_HOSTS.append(VERCEL_URL)
if IS_VERCEL:
    ALLOWED_HOSTS.append('.vercel.app')
if SITE_DOMAIN:
    ALLOWED_HOSTS.extend([SITE_DOMAIN, f'www.{SITE_DOMAIN}'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

if os.getenv('CLOUDINARY_URL'):
    INSTALLED_APPS.insert(6, 'cloudinary_storage')
    INSTALLED_APPS.insert(7, 'cloudinary')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AdminIPRestrictMiddleware',
]

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'portfolio_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'portfolio_project.wsgi.application'

# Database fallback: Use Postgres URL if present, otherwise SQLite
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    try:
        import dj_database_url

        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
    except ImportError:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_SOURCE_DIR = BASE_DIR / 'static'
STATICFILES_DIRS = [STATIC_SOURCE_DIR]
STATIC_ROOT = STATIC_SOURCE_DIR if IS_VERCEL else BASE_DIR / 'staticfiles'
# Previous non-Vercel setting kept for reference:
# 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Django 4.2+ storage configuration used by the current Vercel Django flow.
STORAGES = {
    'default': {
        'BACKEND': (
            'cloudinary_storage.storage.MediaCloudinaryStorage'
            if os.getenv('CLOUDINARY_URL')
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_KEEP_ONLY_HASHED_FILES = False
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_USE_FINDERS = True

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Messages
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# CSRF Security for production
CSRF_TRUSTED_ORIGINS = csv_env('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000')
if VERCEL_URL:
    CSRF_TRUSTED_ORIGINS.append(f'https://{VERCEL_URL}')
if not DEBUG:
    CSRF_TRUSTED_ORIGINS.append('https://*.vercel.app')
if SITE_DOMAIN:
    CSRF_TRUSTED_ORIGINS.extend([f'https://{SITE_DOMAIN}', f'https://www.{SITE_DOMAIN}'])

# Administrative Access Restriction
ALLOWED_ADMIN_IPS = os.getenv('ALLOWED_ADMIN_IPS', '').split(',')
if '' in ALLOWED_ADMIN_IPS:
    ALLOWED_ADMIN_IPS.remove('')

# Master Key for session-based bypass
ADMIN_MASTER_KEY = os.getenv('ADMIN_MASTER_KEY', '')

# Production hardening
if not DEBUG:
    # Legacy note: older Render deploys kept this off to avoid proxy loops.
    SECURE_SSL_REDIRECT = os.getenv(
        'SECURE_SSL_REDIRECT',
        'True' if IS_VERCEL else 'False',
    ) == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
