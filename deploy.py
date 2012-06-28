#!/usr/bin/python
import os
import re
from subprocess import check_call, call
import sys

# This script takes care of downloading the linaro-license-protection code and
# installing it onto a server using the configuration dictionary below for
# commonly changed settings.

config = {
    # Where to check the django app out to
    "django_root": "/home/dooferlad/linaro-license-protection",

    # Used in apache configuration...
    "virtual_host_ip_address_and_port": "_default_",
    "server_admin_email_address": "admin@linaro.org",

    # Base path that will get searched for files to serve
    # In theory there can be more than one XSendFilePath in an apache
    # config and mod_xsendfile will search all of them. This isn't something
    # that has been tested, but in theory will work and should allow serving
    # files from an expanding number of mount points as disk space requirements
    # grow.
    "x_send_file_path": "/home/dooferlad/linaro-license-protection/android",

    # Apache config file name
    "apache2_site_config": "/etc/apache2/sites-available/linaro-license-protection",

    # Postgresql database name
    "database_name": "linaro-license-protection-2",
}

# Derived variables
config["deploy_root"] = os.path.dirname(config["django_root"])
config["django_directory_name"] = os.path.basename(config["django_root"])

def main():
    print "Installing Bazaar"
    run("sudo apt-get -y install bzr")

    print "Fetching linaro-license-protection code from bzr"
    if os.path.isdir(config["django_root"]):
        os.chdir(config["django_root"])
        run("bzr update")
    else:
        run("bzr branch lp:~linaro-infrastructure/linaro-license-protection/merge-django-into-trunk " + config["django_root"])

    print "Installing python modules"
    run("sudo apt-get -y install python-django python-django-openid-auth python-mock python-psycopg2 testrepository")

    print "Running unit tests (sqlite database)"
    os.chdir(config["django_root"])
    run("python manage.py test")
    #if not os.path.isdir(".testrepository"):
    #    run("testr init")
    #run("testr run")

    print "Installing required apache modules"
    run("sudo apt-get -y install apache2 libapache2-mod-xsendfile libapache2-mod-wsgi")

    print "Installing database"
    run("sudo apt-get -y install postgresql")
    run_allow_fail("sudo -u postgres createuser -dSR linaro")
    run_allow_fail("sudo -u postgres createdb " + config["database_name"])

    print "Creating configuration files..."
    generated_apache_config = os.path.join(config["django_root"],
                                           "deployment_templates",
                                           "linaro-license-protection.apache2.conf.gen")

    create_config_file(os.path.join(config["django_root"],
                                    "deployment_templates",
                                    "linaro-license-protection.apache2.conf"),
                       generated_apache_config)

    run("sudo mv " + generated_apache_config + " " + config["apache2_site_config"])

    create_config_file(os.path.join(config["django_root"],
                                    "deployment_templates",
                                    "wsgi.py"),
                       os.path.join(config["django_root"],
                                    "license_protected_downloads",
                                    "wsgi.py"))

    create_config_file(os.path.join(config["django_root"],
                                    "deployment_templates",
                                    "settings.py"),
                       os.path.join(config["django_root"],
                                    "settings.py"))

    print "Deploying files to static root for serving"
    run("python manage.py collectstatic --noinput")

    print "Reloading Apache"
    run("sudo service apache2 reload")

    print "Set up database"
    os.chdir(config["django_root"])
    run("python manage.py syncdb --noinput")

    print "Running unit tests (django database)"
    os.chdir(config["django_root"])
    run("python manage.py test")
    #run("testr run")

    print "Running deployment tests"
    os.chdir(config["django_root"])
    #run("testr run testplans.test_suite")


def run(cmd):
    print "-" * 80
    print cmd
    check_call(cmd, shell=True)

def run_allow_fail(cmd):
    print "-" * 80
    print cmd
    call(cmd, shell=True)

def template_lookup(match):
    if match.group(1) in config:
        return config[match.group(1)]
    else:
        print >> sys.stderr, "Template used undefined variable %s" % match.group(1)
        exit(1)

def create_config_file(in_file_name, out_file_name):
    print "Processing %s to create %s" % (in_file_name, out_file_name)
    with open(in_file_name) as in_file:
        with open(out_file_name, "w") as out_file:
            for line in in_file:
                line = re.sub(r"\{% (\w+) %\}", template_lookup, line)
                out_file.write(line)

if __name__ == "__main__":
    main()
