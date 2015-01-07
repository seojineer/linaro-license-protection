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

ALLOWED_HOSTS = [os.environ.get('HOST_NAME', 'localhost')]

SERVED_PATHS = [os.path.join(DEPLOYMENT_DIR, 'www')]
UPLOAD_PATH = os.path.join(DEPLOYMENT_DIR, 'uploads')
FILE_UPLOAD_TEMP_DIR = '/mnt/django-uploads'

for p in SERVED_PATHS + [UPLOAD_PATH]:
    if not os.path.exists(p):
        os.mkdir(p)
