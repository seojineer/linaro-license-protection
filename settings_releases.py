from settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/srv/releases.linaro.org/db/licenses.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, "templates_releases" ),)
SERVED_PATHS = ['/srv/releases.linaro.org/www']
