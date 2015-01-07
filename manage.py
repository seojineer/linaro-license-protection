#!/usr/bin/env python
import imp
import sys

import django.core.management

try:
    imp.find_module('settings')
except ImportError:
    sys.stderr.write(
        "Error: Can't find the file 'settings.py' in the directory "
        "containing %r. It appears you've customized things.\n"
        "You'll have to run django-admin.py, passing it your "
        "settings module.\n" % __file__)
    sys.exit(1)

import settings

if __name__ == "__main__":
    if getattr(django.core.management, 'execute_manager', None):
        # django < 1.4
        django.core.management.execute_manager(settings)
    else:
        # django >= 1.4
        django.core.management.execute_from_command_line(sys.argv)
