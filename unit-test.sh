#!/bin/sh -e

HERE=$(dirname $(readlink -f $0))
cd $HERE

SKIP_LINT="${SKIP_LINT-1}"
VENV_DIR="${VENV_DIR-$HERE/.venv}"

if [ -z $VIRTUAL_ENV ] ; then
	echo "creating venv: $VENV_DIR ..."
	virtualenv $VENV_DIR
	. $VENV_DIR/bin/activate
	pip install -r requirements.txt
fi

SKIP_LINT=$SKIP_LINT ./manage.py test license_protected_downloads
