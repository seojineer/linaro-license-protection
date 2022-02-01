# Settings for our production instances
from settings import *

import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType


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
    [t["DIRS"].append(DEPLOYMENT_DIR) for t in TEMPLATES if t.has_key("DIRS")]

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

# django_auth_ldap settings
AUTH_LDAP_SERVER_URI = 'ldaps://login.linaro.org'
AUTH_LDAP_BIND_DN = 'cn=systems-bind,ou=binders,dc=linaro,dc=org'
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    'ou=accounts,dc=linaro,dc=org',
    ldap.SCOPE_SUBTREE,
    '(mail=%(user)s)',
)
AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}

AUTH_LDAP_ALWAYS_UPDATE_USER = False
AUTH_LDAP_FIND_GROUP_PERMS = False
