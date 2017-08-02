# Settings for our production instances
from settings import *

DEPLOYMENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, '..'))

DEBUG = False

ROOT_URLCONF = 'urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DEPLOYMENT_DIR, 'db/licenses.db'),
    }
}

ALLOWED_HOSTS_FILE = os.path.join(DEPLOYMENT_DIR, "allowed_hosts.txt")
SERVED_PATHS = [os.path.join(DEPLOYMENT_DIR, 'www')]
UPLOAD_PATH = os.path.join(DEPLOYMENT_DIR, 'uploads')
IP2LOCATION_FILE = os.path.join(
    DEPLOYMENT_DIR, 'IP-COUNTRY-REGION-CITY-ISP.BIN')

for p in SERVED_PATHS + [UPLOAD_PATH]:
    if not os.path.exists(p):
        os.mkdir(p)

# allow local override of default page styling
if os.path.exists(os.path.join(DEPLOYMENT_DIR, 'header_override.html')):
    BASE_PAGE = 'header_override.html'
    TEMPLATE_DIRS += (DEPLOYMENT_DIR,)

# allow site specific overrides for secrets
if os.path.exists(os.path.join(DEPLOYMENT_DIR, 'secrets.py')):
    execfile(os.path.join(DEPLOYMENT_DIR, 'secrets.py'))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/releases-django-cache',
        'TIMEOUT': 5 * 60,  # 5 minute cache
    }
}
