"""
Django settings for DaySafaris project.
"""

from pathlib import Path
from django.utils.translation import gettext_lazy as _
from decouple import config
import mimetypes
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ========== SECURITY SETTINGS ==========
SECRET_KEY = 'django-insecure-i9#fnbul=t8lgg$(zv1x^uq0y!+so2rq*&7*p4rph$iai!q&xl'

# SECURITY WARNING:
DEBUG = True

ALLOWED_HOSTS = [
    "daysafarisadventures.co.ke",
    "www.daysafarisadventures.co.ke",
    "localhost",
    "127.0.0.1",
]

# ========== APPLICATION DEFINITION ==========
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_daraja',
    'Home',
    'OurClients',
    'Places',
    'ClientRequests',
    'Accomodations',
    'Office',
    'Invoices',
    'ChatBot',
    'EmailSetup',
    'FinanceManagement',
    'Payments',
    'MpesaPayment',
    'StripePayment',
    'CryptoTransfer',
    'BankTransfer',
    'SuperMode',
    'django_ckeditor_5',
]

# ========== MIDDLEWARE ==========
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Keep this for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DaySafaris.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Home.context_processors.ads_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'DaySafaris.wsgi.application'

# ========== DATABASE ==========
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ========== PASSWORD VALIDATION ==========
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ========== INTERNATIONALIZATION ==========
LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _('English')),
    ('sw', _('Swahili')),
    ('fr', _('French')),
    ('de', _('German')),
    ('es', _('Spanish')),
    ('it', _('Italian')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ========== STATIC FILES CONFIGURATION ==========
# THIS IS THE IMPORTANT PART FOR YOUR VIDEOS

# URL to use when referring to static files
STATIC_URL = '/static/'

# Directory where static files will be collected for production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directories where Django will look for static files
STATICFILES_DIRS = [
    BASE_DIR / 'Home' / 'static',  # Your app's static folder with videos
]

# Storage for static files (using WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ========== WHITENOISE CONFIGURATION ==========
# These settings help serve video files properly

# Allow WhiteNoise to find files in STATICFILES_DIRS
WHITENOISE_USE_FINDERS = True

# Don't auto-refresh in production (set to False for performance)
WHITENOISE_AUTOREFRESH = False

# Allow missing files without breaking
WHITENOISE_MANIFEST_STRICT = False

# Allow video files from any origin
WHITENOISE_ALLOW_ALL_ORIGINS = True

# Cache static files for 1 year
WHITENOISE_MAX_AGE = 31536000

# ========== MIME TYPES FOR VIDEOS ==========
# This ensures video files are recognized correctly

mimetypes.add_type("video/mp4", ".mp4", True)
mimetypes.add_type("video/webm", ".webm", True)
mimetypes.add_type("video/ogg", ".ogv", True)
mimetypes.add_type("video/quicktime", ".mov", True)
mimetypes.add_type("video/x-msvideo", ".avi", True)

# ========== MEDIA FILES ==========
# For user-uploaded files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========== CKEDITOR 5 (rich text for Blog/Package/Destination content) ==========
# Using CKEditor 5 (django-ckeditor-5) instead of the legacy CKEditor 4 bundled
# with django-ckeditor, which is end-of-life and has unfixed security issues.
CKEDITOR_5_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
CKEDITOR_5_UPLOAD_PATH = 'ckeditor_uploads/'
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'bulletedList', 'numberedList', 'blockQuote', '|',
            'alignment', '|',
            'link', 'insertImage', 'insertTable', 'horizontalLine', '|',
            'undo', 'redo', '|',
            'sourceEditing',
        ],
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
                {'model': 'heading4', 'view': 'h4', 'title': 'Heading 4', 'class': 'ck-heading_heading4'},
            ]
        },
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft', 'imageStyle:full', 'imageStyle:alignRight'],
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells'],
        },
    },
}


# ========== AUTHENTICATION ==========
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'

# ========== DEFAULT FIELD ==========
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========== CSRF CONFIGURATION ==========
CSRF_TRUSTED_ORIGINS = [
    'https://daysafarisadventures.co.ke',
    'http://daysafarisadventures.co.ke',
    'https://www.daysafarisadventures.co.ke',
    'http://www.daysafarisadventures.co.ke',
]

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# ========== EMAIL CONFIGURATION (Brevo) ==========
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@daysafarisadventures.co.ke')
EMAIL_FROM_NAME = config('EMAIL_FROM_NAME', default='Day Safaris Adventures')
BREVO_API_KEY = config('BREVO_API_KEY', default='')

# ========== M-PESA CONFIGURATION ==========
MPESA_ENVIRONMENT = config("MPESA_ENVIRONMENT", default='sandbox')
MPESA_CONSUMER_KEY = config("MPESA_CONSUMER_KEY", default='')
MPESA_CONSUMER_SECRET = config("MPESA_CONSUMER_SECRET", default='')
MPESA_SHORTCODE = config("MPESA_SHORTCODE", default='')
MPESA_EXPRESS_SHORTCODE = config("MPESA_EXPRESS_SHORTCODE", default='')
MPESA_SHORTCODE_TYPE = config("MPESA_SHORTCODE_TYPE", default='paybill')
MPESA_PASSKEY = config("MPESA_PASSKEY", default='')
MPESA_INITIATOR_USERNAME = config("MPESA_INITIATOR_USERNAME", default='')
MPESA_INITIATOR_SECURITY_CREDENTIAL = config("MPESA_INITIATOR_SECURITY_CREDENTIAL", default='')