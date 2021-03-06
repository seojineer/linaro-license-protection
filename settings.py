# Django settings for linaro_license_protection_2 project.

# suppress BeautifulSoup warning
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os

from version import VERSION

DEBUG = True

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.split(PROJECT_ROOT)[-1]
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DEPLOYMENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '..'))
JS_PATH = os.path.join(ROOT_PATH, "js")
CSS_PATH = os.path.join(ROOT_PATH, "css")
TEMPLATES_PATH = os.path.join(ROOT_PATH, "templates")
TEXTILE_FALLBACK_PATH = os.path.join(TEMPLATES_PATH, "textile_fallbacks")
REPORT_CSV = os.path.join(DEPLOYMENT_DIR, "download_report.csv")
S3_PURGE_EXCLUDES = []
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ADMINS = (
    ('linaro-infrastructure', 'linaro-infrastructure-errors@linaro.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'licenses.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

FILE_UPLOAD_PERMISSIONS = 0644

TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
SITE_NAME = 'Linaro License Protection'

USE_I18N = True
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded
# files. Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "staticroot")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # Also:
    # - for some reason, django doesn't like this to be "STATIC_ROOT"
    # - this must be a tuple, so even if only 1 entry leave a trailing comma
    os.path.join(PROJECT_ROOT, "license_protected_downloads/static"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #   'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, "templates"),
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                'license_protected_downloads.context_processors.llp_common',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'license_protected_downloads',
)

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Name of "plugin" modules to use for group authentication
# Plugins will be queried in specified order until first positive match
# Available plugins:
#   license_protected_downloads.group_auth_ldap - uses Linaro ldap groups
GROUP_AUTH_MODULES = ['license_protected_downloads.group_auth_ldap']

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # Root logger
        '': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'llp': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    }
}

# disable caches by default for testing (enabled in production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

import django
if django.VERSION < (1, 6):
    # old django needs a hack to not send emails for ALLOWED_HOSTS violations
    from django.core.exceptions import SuspiciousOperation

    class SuspiciousFilter(object):
        def filter(self, record):
            if record.exc_info:
                exc_type, exc_value = record.exc_info[:2]
                if isinstance(exc_value, SuspiciousOperation):
                    return False
            return True

    LOGGING['handlers']['mail_admins']['filters'] = ['skip_suspicious']
    LOGGING['filters'] = {
        'skip_suspicious': {'()': SuspiciousFilter}
    }
else:
    # don't send email for ALLOWED_HOSTS violations
    LOGGING['loggers']['django.security.DisallowedHost'] = {
        'handlers': ['mail_admins'],
        'level': 'CRITICAL',
        'propagate': False,
    }

SERVED_PATHS = [os.path.join(PROJECT_ROOT, "sampleroot")]
UPLOAD_PATH = os.path.join(PROJECT_ROOT, "sample_upload_root")

# Render TEXTILE files settings.
LINUX_FILES = ('README.textile',
               'INSTALL.textile',
               'HACKING.textile',
               'FIRMWARE.textile',
               'FASTMODELS.textile',
               'RTSM.textile',
               'OPENJDK.textile',
               'GETTINGSTARTED.textile',
               'EULA.txt',
               'testplan.textile',
               'testreport.textile')

ANDROID_FILES = ('HOWTO_releasenotes.txt',
                 'HOWTO_install.txt',
                 'HOWTO_getsourceandbuild.txt',
                 'HOWTO_flashfirmware.txt',
                 'HOWTO_rtsm.txt',
                 'HOWTO_eula.txt',
                 'HOWTO_gettingstarted.txt')

FILES_MAP = {'HOWTO_releasenotes.txt': 'Release Notes',
             'HOWTO_install.txt': 'Binary Image Installation',
             'HOWTO_getsourceandbuild.txt': 'Building From Source',
             'HOWTO_flashfirmware.txt': 'Firmware',
             'HOWTO_rtsm.txt': 'RTSM',
             'README.textile': 'Release Notes',
             'INSTALL.textile': 'Binary Image Installation',
             'HACKING.textile': 'Building From Source',
             'FIRMWARE.textile': 'Firmware',
             'FASTMODELS.textile': 'Fast Models',
             'RTSM.textile': 'RTSM',
             'OPENJDK.textile': 'OpenJDK',
             'GETTINGSTARTED.textile': 'Getting Started',
             'HOWTO_gettingstarted.txt': 'Getting Started',
             'HOWTO_eula.txt': 'EULA',
             'EULA.txt': 'EULA',
             'testplan.textile': 'Test Plan',
             'testreport.textile': 'Test Project'}

TAB_PRIORITY = ['Release Notes',
                'Binary Image Installation',
                'Building From Source',
                'Getting Started',
                'Firmware',
                'Fast Models',
                'EULA',
                'RTSM',
                'OpenJDK']

BASE_PAGE = 'header.html'
BOT_USER_AGENTS = [
    'Googlebot/2', 'bingbot/2', 'Yahoo! Slurp', 'Baiduspider/2',
    'YandexBot/3.0', 'MJ12bot',
]

MASTER_API_KEY = ""
TRACK_DOWNLOAD_STATS = False

# Import proxy_settings if file exists
try:
    from proxy_settings import *
except ImportError:
    pass

# Try to import local_settings. If it doesn't exist, generate it. It contains
# SECRET_KEY (to keep it secret).
try:
    from local_settings import *
    if SECRET_KEY is None:
        raise ValueError
except (ImportError,NameError,ValueError):
    import random

    # Create local_settings with random SECRET_KEY and MASTER_API_KEY
    char_selection = '0123456789abcdefghijklmnopqrstuvwxyz' \
                     'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    char_selection_with_punctuation = char_selection + '!@#$%^&*(-_=+)'

    # SECRET_KEY contains anything but whitespace
    secret_key = ''.join(random.sample(char_selection_with_punctuation, 50))
    local_settings_content = "SECRET_KEY = '%s'\n" % secret_key

    # At the moment the publishing API is still in development so it is
    # disabled...
    if False:
        # MASTER_API_KEY contains characters that don't have to be % encoded
        # in an HTTP URL.
        master_api_key = ''.join(random.sample(char_selection, 50))
        local_settings_content += "MASTER_API_KEY = '%s'\n" % master_api_key

    with open(os.path.join(PROJECT_ROOT, "local_settings.py"), "w") as f:
        f.write(local_settings_content)

    from local_settings import *

ANNOTATED_XML = 'source-manifest-ann.xml'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['*']
