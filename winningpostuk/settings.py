
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-^9h#ekcpo@k2g3affh9^8q2+mgigp_o4hmrhq=_v6k4^g7tow#'
DEBUG = False


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "winningpostuk.onrender.com",
    "winningpostuk.com",
    "www.winningpostuk.com",
]



# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',
    'members.templatetags',

    # Your apps
    'members',
    'tips',

    # PayPal
    'paypal.standard.ipn',
]


# -----------------------------------------------------
# 🔐 MIDDLEWARE (Subscription middleware inserted here)
# -----------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # <-- REQUIRED FOR STATIC FILES
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'members.middleware.no_admin_for_users.BlockNormalUsersFromAdmin',
    'members.middleware.subscription.SubscriptionRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'winningpostuk.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Global templates folder
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


WSGI_APPLICATION = 'winningpostuk.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
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


# Internationalisation
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ✅ Django 4.2+/6.0 static storage (recommended way)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}


# -------------------------
# 💳 PayPal Settings
# -------------------------
PAYPAL_RECEIVER_EMAIL = 'sb-ydm9q48339253@business.example.com'
PAYPAL_TEST = True  # Sandbox mode

# PayPal REST API credentials (for subscription cancellation etc.)
PAYPAL_CLIENT_ID = "ASpbJvuCNOkwYbbyk0K6q-aBLEFqbV9LxdnVknQTO1AdiRs-w1EM11FGZxqL1O8f10mxJfxGczeJgyTU"
PAYPAL_CLIENT_SECRET = "EMqkro-fhrkFPvQeamJnA9ZCuTOBChDxvjLCIT766us-cDB3a7CBu2DTeliQz2_KvDervZ5wEAu2PgRK"


# -------------------------
# 🔐 Authentication Redirects
# -------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'


# -------------------------
# 📧 Email (console for dev)
# -------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


EMAIL_HOST = 'smtp.gmail.com'       # or your provider
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'wpostuk@gmail.com'
EMAIL_HOST_PASSWORD = 'djvh vrlz sdat aeaj'  # NEVER your real Gmail password
DEFAULT_FROM_EMAIL = "WinningPostUK <wpostuk@gmail.com>"
EMAIL_TIMEOUT = 15  # ✅ so sockets don't hang and kill the worker


# 📩 Email CTA URLs (used by the notification sender)
SITE_BASE_URL = "https://winningpostuk.com"  # used to build absolute logo URL in emails
TIPS_TODAY_URL = "https://winningpostuk.com/dashboard/"   # your tips are on the dashboard
LOGIN_URL_ABSOLUTE = "https://winningpostuk.com/login/"
ACCOUNT_MANAGE_URL = "https://winningpostuk.com/membership/"


RECAPTCHA_PUBLIC_KEY = "6LfjRHIsAAAAADkgfyXszaF1_Y569L1OycQKcyST"
RECAPTCHA_PRIVATE_KEY = "6LfjRHIsAAAAAK0PBrh7vXcJ_9Q3nUK2qUTw7H1_"
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]


# ✅ Behind Render/Cloudflare, trust the proxy for HTTPS detection
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Recommended production flags (enable once everything is confirmed working over HTTPS)
CSRF_TRUSTED_ORIGINS = [
    "https://winningpostuk.com",
    "https://www.winningpostuk.com",
    "https://*.onrender.com",
]

# Optional hardening once domain is fully live and login works over HTTPS:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 3600
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
