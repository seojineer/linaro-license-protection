from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/srv/snapshots.linaro.org/db/licenses.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, "templates_snapshots" ),)
SERVED_PATHS = ['/srv/snapshots.linaro.org/www']
