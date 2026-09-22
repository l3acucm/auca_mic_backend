import os
from datetime import timedelta

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

from project.logging_config import configure_structlog, get_logging_config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_env_setting(setting, default=None):
    """Read an env var, falling back to `default`, raising if neither is set.

    Same convention used across the presale/cashway/vigil-bot backends — no
    django-environ, booleans are stored as 0/1 ints.
    """
    try:
        return os.environ[setting]
    except KeyError:
        if default is not None:
            return default
        raise ImproperlyConfigured("Set the %s env variable" % setting)


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
SECRET_KEY = get_env_setting('SECRET_KEY')
DEVELOPMENT = bool(int(get_env_setting('DEVELOPMENT', 0)))
TESTING = bool(int(get_env_setting('TESTING', 0)))
STAGING = bool(int(get_env_setting('STAGING', 0)))
PRODUCTION = bool(int(get_env_setting('PRODUCTION', 0)))
DEBUG = not (PRODUCTION or STAGING)

configure_structlog()
LOGGING = get_logging_config(debug=DEBUG)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_setting('POSTGRES_DATABASE_NAME'),
        'USER': get_env_setting('POSTGRES_USER'),
        'PASSWORD': get_env_setting('POSTGRES_PASSWORD'),
        'HOST': get_env_setting('POSTGRES_ENDPOINT'),
        'PORT': int(get_env_setting('POSTGRES_PORT', 5432)),
    }
}

DOMAIN = get_env_setting('DOMAIN')
URL_PREFIX = ('https' if STAGING or PRODUCTION else 'http') + '://' + DOMAIN
ALLOWED_HOSTS = list(set(
    get_env_setting('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') + [DOMAIN]
))

# The React SPA is served from its own origin (Cloudflare Pages). List every
# origin the browser will call the API from.
FRONTEND_ORIGINS = [o for o in get_env_setting('FRONTEND_ORIGINS', URL_PREFIX).split(',') if o]
CORS_ALLOWED_ORIGINS = list(set([URL_PREFIX] + FRONTEND_ORIGINS))
CSRF_TRUSTED_ORIGINS = list(set([URL_PREFIX] + FRONTEND_ORIGINS))
CORS_ALLOW_HEADERS = (*default_headers, "otp")

INSTALLED_APPS = [
    'moses',  # FIRST — provides the AUTH_USER_MODEL
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'project.experiments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'project.wsgi.application'

AUTH_USER_MODEL = 'moses.CustomUser'
# Single-tenant deploy (one Site == one experiment platform): the admin login
# form doesn't send `domain`, so the plain moses backend rejects every admin
# login. Default it to settings.DOMAIN instead — see moses.md.
AUTHENTICATION_BACKENDS = ['project.common.admin_auth.SingleTenantMFAModelBackend']
SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DATETIME_FORMAT': '%s',
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_AUTHENTICATION_CLASSES': ['moses.authentication.JWTAuthentication'],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_RENDERER_CLASSES': ['moses.common.renderers.CustomJSONRenderer'],
    'EXCEPTION_HANDLER': 'moses.common.exception_handlers.custom_exception_handler',
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# Researcher accounts only, created by the admin (no self-registration, no
# SMS/email — see BRD 4.1). Phone confirmation is fully disabled, so BOTH
# flags below must be off: REQUIRE_PHONE_NUMBER_CONFIRMATION_FOR_LOGIN
# defaults to True in moses and silently locks out every login otherwise.
MOSES = {
    "DEFAULT_LANGUAGE": "ru",
    "DOMAIN": DOMAIN,
    "URL_PREFIX": URL_PREFIX,
    "REQUIRE_EMAIL_CONFIRMATION": False,
    "REQUIRE_PHONE_NUMBER_CONFIRMATION": False,
    "REQUIRE_PHONE_NUMBER_CONFIRMATION_FOR_LOGIN": False,
    "EMAILS_DISABLED": True,
    "PHONE_NUMBER_VALIDATOR": "project.common.validators.validate_phone_number",
    "IP_HEADER": "HTTP_CF_CONNECTING_IP" if not DEBUG else None,
    "LANGUAGE_CHOICES": (('ru', 'Russian'), ('en', 'English')),
}

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Bishkek'
USE_I18N = True
USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Max upload accepted in memory before Django spills to a temp file — the ZIP
# stimulus archives (up to 500MB, see BRD 7.3) always go to disk either way.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
STIMULUS_ARCHIVE_MAX_BYTES = 500 * 1024 * 1024
STIMULUS_IMAGE_MAX_BYTES = 10 * 1024 * 1024

# Presigned download URL lifetime for result XLSX files (BRD 6.2).
RESULT_DOWNLOAD_URL_EXPIRY_SECONDS = 24 * 60 * 60

if STAGING or PRODUCTION:
    # Stimuli images + result XLSX files on the S3-compatible object storage,
    # exactly like presale_backend/cashway_backend. AWS_ACCESS_KEY/SECRET come
    # from the shared global.env; AWS_BUCKET_NAME/S3_ENDPOINT_URL per-app.
    AWS_ACCESS_KEY_ID = get_env_setting('AWS_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = get_env_setting('AWS_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = get_env_setting('AWS_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = get_env_setting('S3_ENDPOINT_URL')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_STATIC_LOCATION = 'static'
    AWS_MEDIA_LOCATION = 'media'
    STORAGES = {
        "staticfiles": {"BACKEND": "project.storages.StaticStorage"},
        # Stimulus images are the common case (loaded directly as <img src>);
        # result XLSX exports use PrivateMediaStorage explicitly (see
        # services/xlsx_export.py) so they need a signed URL to download.
        "default": {"BACKEND": "project.storages.PublicMediaStorage"},
    }
    CDN_DOMAIN = f'hel1.your-objectstorage.com/{AWS_STORAGE_BUCKET_NAME}/'
    STATIC_URL = f'https://{CDN_DOMAIN}/{AWS_STATIC_LOCATION}/'
    MEDIA_URL = f'https://{CDN_DOMAIN}/{AWS_MEDIA_LOCATION}/'
else:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
