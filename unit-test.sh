#!/bin/sh -e

HERE=$(dirname $(readlink -f $0))
cd $HERE

SKIP_LINT="${SKIP_LINT-1}"
VENV_DIR="${VENV_DIR-$HERE/.venv}"

if [ ! -f /usr/bin/virtualenv ] ; then
	echo "installing python-virutalenv"
	sudo apt-get install -f python-virtualenv
fi

if [ -z $VIRTUAL_ENV ] ; then
	echo "creating venv: $VENV_DIR ..."
	virtualenv --python=`which python2` $VENV_DIR
	. $VENV_DIR/bin/activate
	pip install -r requirements.txt
fi

DJANGO_SETTINGS_MODULE=settings SKIP_LINT=$SKIP_LINT ./manage.py test license_protected_downloads
