"""
Production settings for Serba 10 Ribu Group Web-GIS Application.
Following django-security best practices.
"""
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'serba10ribu.com,www.serba10ribu.com').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME', 'serba10ribu_prod'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# Security Headers & SSL
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
