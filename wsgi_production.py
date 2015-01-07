import os
import sys

from django.core.handlers.wsgi import WSGIHandler

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(here)

os.environ["DJANGO_SETTINGS_MODULE"] = 'settings_production'
APP_ENVS = ['SITE_NAME', 'HOST_NAME']

_app = WSGIHandler()


def application(environ, start_response):
    # pass the WSGI environment variables on through to os.environ
    for var in APP_ENVS:
        os.environ[var] = environ.get(var, '')
    return _app(environ, start_response)
