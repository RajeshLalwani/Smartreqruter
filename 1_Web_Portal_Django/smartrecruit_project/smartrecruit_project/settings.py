import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR is '.../SmartRecruit/1_Web_Portal_Django'
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# 🔗 BRIDGE TO AI MODULES (CRITICAL STEP)
# This allows Django to "see" the 2_AI_Modules folder
# We go up one level from BASE_DIR to find 'SmartRecruit' root
# =========================================================
AI_MODULES_PATH = os.path.join(BASE_DIR.parent.parent, '2_AI_Modules')
sys.path.append(str(AI_MODULES_PATH))

from decouple import config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# GEMINI AI INTERFACE KEY
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# HUGGING FACE FALLBACK ENGINE KEY
HF_API_TOKEN = config('HF_API_TOKEN', default='')

# GROQ ULTRA-LOW LATENCY FALLBACK KEY
GROQ_API_KEY = config('GROQ_API_KEY', default='')



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG_RAW = config('DEBUG', default='False')
if isinstance(DEBUG_RAW, bool):
    DEBUG = DEBUG_RAW
else:
    DEBUG = str(DEBUG_RAW).lower() in ['true', '1', 't', 'y', 'yes']

ALLOWED_HOSTS = [
    host.strip() for host in config(
        'ALLOWED_HOSTS',
        default='localhost,127.0.0.1'
    ).split(',') if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in config(
        'CSRF_TRUSTED_ORIGINS',
        default=(
            'http://localhost:8000,http://127.0.0.1:8000,'
            'http://localhost:8003,http://127.0.0.1:8003'
        )
    ).split(',') if origin.strip()
]

# Application definition
INSTALLED_APPS = [
    'daphne', # Must be first
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.saml',
    
    # Third Party
    'bootstrap5',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'whitenoise.runserver_nostatic',
    'channels', # Add Channels

    # Custom Apps
    'core',
    'jobs',
    'interview',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS must be above CommonMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Phase 10: Multi-language Support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

ROOT_URLCONF = 'smartrecruit_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Global Templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartrecruit_project.wsgi.application'
ASGI_APPLICATION = 'smartrecruit_project.asgi.application'

# Channels Layer (Redis for Pro/Sync)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('hi', _('Hindi')),
    ('es', _('Spanish')),
    ('gu', _('Gujarati')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # For Production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (Resumes, Videos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Custom User Model (Must point to CORE app as verified)
AUTH_USER_MODEL = 'core.User'

# Redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------- SMART_RECRUIT PHASE 7 ADMIN SETTINGS -----------
AUTO_SEND_FEEDBACK_TO_CANDIDATE = False


SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Must be False so JS can read it for AJAX calls
# NOTE: CSRF_USE_SESSIONS was removed — it breaks form-based {% csrf_token %} tags
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =========================================================
# REST FRAMEWORK CONFIGURATION
# =========================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# =========================================================
# EMAIL CONFIGURATION (DUMMY SMTP FOR INITIAL SETUP)
# =========================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@gmail.com') 
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='') # RAJ: Generate an "App Password" in your Google Account for this.
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
HR_EMAIL = "hr@smartrecruit.ai" # Default fallback for proctoring alerts

# Site URL for email links
SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000')

# =========================================================
# LOGGING CONFIGURATION
# =========================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'pipeline': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'pipeline',
        },
    },
    'loggers': {
        'pipeline': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# =========================================================
# 🔐 ENTERPRISE SSO (SAML & OAuth2)
# =========================================================
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_ADAPTER = 'core.adapters.CustomSocialAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        'SCOPE': ['User.Read'],
        'APP': {
            'client_id': config('AZURE_CLIENT_ID', default='placeholder_id'),
            'secret': config('AZURE_CLIENT_SECRET', default='placeholder_secret'),
        }
    },
    'saml': {
        'APPS': [
            {
                'client_id': 'okta', # Added client_id as per instruction
                'id': 'okta',
                'name': 'Okta Enterprise',
                'sp_entity_id': config('SAML_SP_ENTITY_ID', default='http://127.0.0.1:8000/'),
                'idp': {
                    'entity_id': config('SAML_IDP_ENTITY_ID', default=''),
                    'sso_url': config('SAML_IDP_SSO_URL', default=''),
                    'x509cert': config('SAML_IDP_X509CERT', default=''),
                },
            },
        ]
    }
}

# Allauth Account Settings (allauth v0.63+ API)
ACCOUNT_LOGIN_METHODS = {'email'}          # replaces ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # replaces ACCOUNT_EMAIL_REQUIRED + ACCOUNT_USERNAME_REQUIRED
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_DOMAIN_WHITELIST = ['microsoft.com', 'google.com', 'tech-elecon.com'] # RAJ: Add your corporate domain here
