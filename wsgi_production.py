import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(here)

os.environ["DJANGO_SETTINGS_MODULE"] = 'settings_production'
APP_ENVS = ['SITE_NAME']

from django.core.wsgi import get_wsgi_application
_app = get_wsgi_application()


def application(environ, start_response):
    from django.conf import settings
    try:
        with open(settings.ALLOWED_HOSTS_FILE, 'r') as f:
            settings.ALLOWED_HOSTS = [x.strip() for x in f]
    except IOError as e:
        if e.errno != os.errno.ENOENT:
            settings.ALLOWED_HOSTS = [environ['HOST_NAME']]


    # pass the WSGI environment variables on through to os.environ
    for var in APP_ENVS:
        os.environ[var] = environ.get(var, '')
    return _app(environ, start_response)
