#!/bin/sh -e

HERE=$(dirname $(readlink -f $0))
cd $HERE

# python-ldap 3.3.1 is going to trigger
# a build, so need to support it
sudo apt install -y -f libpython-dev libldap2-dev libsasl2-dev 

SKIP_LINT="${SKIP_LINT-1}"
VENV_DIR="${VENV_DIR-$HERE/.venv}"

if [ ! -f /usr/bin/virtualenv ] ; then
	echo "installing python-virutalenv"
	sudo apt-get install -y -f python-virtualenv
fi


if [ -z $VIRTUAL_ENV ] ; then
	echo "creating venv: $VENV_DIR ..."
	virtualenv --python=`which python2` $VENV_DIR
	. $VENV_DIR/bin/activate
	pip install -r requirements.txt
fi

rm -rf staticroot/*
if [ ! -f "linaro_ldap.py" ];
then
    wget -O linaro_ldap.py https://git.linaro.org/infrastructure/linaro-git-tools.git/plain/linaro_ldap.py
fi

DJANGO_SETTINGS_MODULE=settings SKIP_LINT=$SKIP_LINT ./manage.py collectstatic --no-input
DJANGO_SETTINGS_MODULE=settings SKIP_LINT=$SKIP_LINT ./manage.py test license_protected_downloads
