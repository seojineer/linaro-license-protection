#!/bin/sh
#
# This script is example/reminder how to run manage.py on production
# installs which have site django config well outside the main codebase.
#
# If this looks complicated, that's because it is.
#

if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    echo "DJANGO_SETTINGS_MODULE envvar should be set"
    echo "e.g.: DJANGO_SETTINGS_MODULE=settings_staging_snapshots"
    echo "Available configs:"
    ls -1 ../configs/django/
    exit 1
fi

cd ..
PYTHONPATH=configs/django/:linaro-license-protection:. django-admin "$@"
