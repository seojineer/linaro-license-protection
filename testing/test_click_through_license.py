#!/usr/bin/env python

import re
import os
import sys
import shutil
import shlex
import subprocess

from testtools import TestCase
from testtools.matchers import Mismatch
from testtools.matchers import MatchesAny
from filefetcher import LicenseProtectedFileFetcher

fetcher = LicenseProtectedFileFetcher()
cwd = os.getcwd()
docroot = cwd
srvroot = os.path.abspath(os.path.join(*([cwd] + ['testing'])))
local_rewrite = 'RewriteCond %{REMOTE_ADDR} 127.0.0.1 [OR]'

host = 'http://127.0.0.1'
port = '8080'
samsung_license_path = '/licenses/samsung-v2.html'
ste_license_path = '/licenses/ste.html'
samsung_test_file = '/android/~linaro-android/staging-origen/test.txt'
ste_test_file = '/android/~linaro-android/staging-snowball/test.txt'
not_protected_test_file = '/android/~linaro-android/staging-panda/test.txt'


class Contains(object):
    '''Match if a string contains substring'''
    def __init__(self, substr):
        self.substr = substr

    def __str__(self):
        return 'Contains(%s)' % (self.substr,)

    def match(self, actual):
        for line in actual.splitlines():
            res = re.search(self.substr, line)
            if res:
                return None
        return Mismatch("Initial string doesn't contain substring (%s)" %
                self.substr)

class CommandNotFoundException(Exception):
    ''' Unable to find command '''

class NonZeroReturnValueException(Exception):
    ''' Command exited with nonzero return value '''

class TestLicense(TestCase):
    '''Tests for accessing files and directories with license protection'''

    @classmethod
    def setUpClass(cls):
        global host
        if port != '80':
            host = host + ':' + port
        shutil.copy("%s/apache2.conf.tmpl" % srvroot, "%s/apache2.conf" %
                srvroot)
        shutil.copy("%s/.htaccess" % docroot, "%s/dothtaccess" % docroot)
        subprocess.Popen(['sed', '-i' , 's/ServerRoot \"\"/ServerRoot \"%s\"/' % srvroot.replace('/', '\/'),
            '%s/apache2.conf' % srvroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        subprocess.Popen(['sed', '-i' , 's/DocumentRoot \"\"/DocumentRoot \"%s\"/' % docroot.replace('/', '\/'),
            '%s/apache2.conf' % srvroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        subprocess.Popen(['sed', '-i' , 's/Directory \"\"/Directory \"%s\"/' % docroot.replace('/', '\/'),
            '%s/apache2.conf' % srvroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        subprocess.Popen(['sed', '-i' , 's/Listen/Listen %s/' % port,
            '%s/apache2.conf' % srvroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        if subprocess.Popen(['which', 'apache2'], stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait():
            raise CommandNotFoundException("apache2 command not found. Please install apache2 web server "
                    "and rerun tests.")
        args = shlex.split('apache2 -d %s -f apache2.conf -k start' % srvroot)
        rc = subprocess.Popen(args, stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait()
        if rc:
            raise NonZeroReturnValueException("apache2 server exited with error"
                    " %s" % rc)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("%s/cookies.txt" % docroot):
            os.unlink("%s/cookies.txt" % docroot)
        args = shlex.split('apache2 -d %s -f apache2.conf -k stop' % srvroot)
        subprocess.Popen(args, stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait()
        if os.path.exists("%s/apache2.conf" % srvroot):
            os.unlink("%s/apache2.conf" % srvroot)
        if os.path.exists("%s/click_through_license_access.log" % srvroot):
            os.unlink("%s/click_through_license_access.log" % srvroot)
        if os.path.exists("%s/click_through_license_error.log" % srvroot):
            os.unlink("%s/click_through_license_error.log" % srvroot)
        os.rename("%s/dothtaccess" % docroot, "%s/.htaccess" % docroot)

    def setUp(self):
        super(TestLicense, self).setUp()
        global fetcher
        fetcher = LicenseProtectedFileFetcher()
 
    def tearDown(self):
        super(TestLicense, self).tearDown()
        if isinstance(fetcher, LicenseProtectedFileFetcher):
            fetcher.close()
        if os.path.exists("%s/cookies.txt" % docroot):
            os.unlink("%s/cookies.txt" % docroot)

    def test_licensefile_directly_samsung(self):
        search = "Index of /"
        testfile = fetcher.get(host + samsung_license_path)
        self.assertThat(testfile, Contains(search))

    def test_licensefile_directly_ste(self):
        search = "Index of /"
        testfile = fetcher.get(host + ste_license_path)
        self.assertThat(testfile, Contains(search))

    def test_redirect_to_license_samsung(self):
        search = "SAMSUNG DEVELOPMENT TOOL KIT END-USER LICENSE AGREEMENT"
        testfile = fetcher.get(host + samsung_test_file, ignore_license=True)
        self.assertThat(testfile, Contains(search))

    def test_redirect_to_license_ste(self):
        search = "LIMITED LICENSE AGREEMENT FOR APPLICATION DEVELOPERS"
        testfile = fetcher.get(host + ste_test_file, ignore_license=True)
        self.assertThat(testfile, Contains(search))

    def test_decline_license_samsung(self):
        search = "License has not been accepted"
        testfile = fetcher.get(host + samsung_test_file, accept_license=False)
        self.assertThat(testfile, Contains(search))

    def test_decline_license_ste(self):
        search = "License has not been accepted"
        testfile = fetcher.get(host + ste_test_file, accept_license=False)
        self.assertThat(testfile, Contains(search))

    def test_non_protected_dirs(self):
        search = "This is always available."
        testfile = fetcher.get(host + not_protected_test_file)
        self.assertThat(testfile, Contains(search))

    def test_accept_license_samsung_file(self):
        search = "This is a protected with click-through Samsung license."
        testfile = fetcher.get(host + samsung_test_file)
        fetcher.close()
        if os.path.exists("%s/cookies.txt" % docroot):
            os.rename("%s/cookies.txt" % docroot, "%s/cookies.samsung" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_accept_license_samsung_dir(self):
        search = "Index of /android/~linaro-android/staging-origen"
        testfile = fetcher.get(host + os.path.dirname(samsung_test_file))
        self.assertThat(testfile, Contains(search))

    def test_accept_license_ste_file(self):
        search = "This is a protected with click-through ST-E license."
        testfile = fetcher.get(host + ste_test_file)
        fetcher.close()
        if os.path.exists("%s/cookies.txt" % docroot):
            os.rename("%s/cookies.txt" % docroot, "%s/cookies.ste" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_accept_license_ste_dir(self):
        search = "Index of /android/~linaro-android/staging-snowball"
        testfile = fetcher.get(host + os.path.dirname(ste_test_file))
        self.assertThat(testfile, Contains(search))

    def test_license_accepted_samsung(self):
        search = "This is a protected with click-through Samsung license."
        os.rename("%s/cookies.samsung" % docroot, "%s/cookies.txt" % docroot)
        testfile = fetcher.get(host + samsung_test_file, ignore_license=True)
        self.assertThat(testfile, Contains(search))

    def test_license_accepted_ste(self):
        search = "This is a protected with click-through ST-E license."
        os.rename("%s/cookies.ste" % docroot, "%s/cookies.txt" % docroot)
        testfile = fetcher.get(host + ste_test_file, ignore_license=True)
        self.assertThat(testfile, Contains(search))

    def test_internal_host_samsung(self):
        search = "This is a protected with click-through Samsung license."
        subprocess.Popen(['sed', '-i' , '/## Let internal hosts through always./ a %s' % local_rewrite,
            '%s/.htaccess' % docroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        testfile = fetcher.get(host + samsung_test_file, ignore_license=True)
        shutil.copy("%s/dothtaccess" % docroot, "%s/.htaccess" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_internal_host_ste(self):
        search = "This is a protected with click-through ST-E license."
        subprocess.Popen(['sed', '-i' , '/## Let internal hosts through always./ a %s' % local_rewrite,
            '%s/.htaccess' % docroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        testfile = fetcher.get(host + ste_test_file, ignore_license=True)
        shutil.copy("%s/dothtaccess" % docroot, "%s/.htaccess" % docroot)
        self.assertThat(testfile, Contains(search))
