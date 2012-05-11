#!/usr/bin/env python

import re
import os
import shutil
import shlex
import subprocess
import socket

from testtools import TestCase
from testtools.matchers import Mismatch
from license_protected_file_downloader import LicenseProtectedFileFetcher

fetcher = LicenseProtectedFileFetcher()
cwd = os.getcwd()
docroot = cwd
srvroot = os.path.abspath(os.path.join(*([cwd] + ['testing'])))
local_rewrite = 'RewriteCond %{REMOTE_ADDR} 127.0.0.1 [OR]'

host = 'http://127.0.0.1'
port = '0'  # 0 == Pick a free port.
samsung_license_path = '/licenses/samsung.html'
ste_license_path = '/licenses/ste.html'
linaro_license_path = '/licenses/linaro.html'
samsung_test_file = '/android/~linaro-android/staging-origen/test.txt'
ste_test_file = '/android/~linaro-android/staging-snowball/173/target/product/snowball/test.txt'
ste_open_test_file = '/android/~linaro-android/staging-snowball/173/test.txt'
never_available = '/android/~linaro-android/staging-imx53/test.txt'
linaro_test_file = '/android/~linaro-android/staging-panda/test.txt'
not_protected_test_file = '/android/~linaro-android/staging-vexpress-a9/test.txt'
not_found_test_file = '/android/~linaro-android/staging-vexpress-a9/notfound.txt'
per_file_samsung_test_file = '/android/images/origen-blob.txt'
per_file_ste_test_file = '/android/images/snowball-blob.txt'
per_file_not_protected_test_file = '/android/images/MANIFEST'
dirs_only_dir = '/android/~linaro-android/'


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
        global port
        if port == '0':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', 0))
            port = str(s.getsockname()[1])
            s.close()
            host = host + ':' + port
        shutil.copy("%s/apache2.conf.tmpl" % srvroot, "%s/apache2.conf" %
                srvroot)
        shutil.copy("%s/.htaccess" % docroot, "%s/dothtaccess" % docroot)
        subprocess.Popen(['sed', '-i', 's/ServerRoot \"\"/ServerRoot \"%s\"/'
            % srvroot.replace('/', '\/'), '%s/apache2.conf' % srvroot],
            stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT).wait()
        subprocess.Popen(['sed', '-i', 's/DocumentRoot \"\"/DocumentRoot '
            '\"%s\"/' % docroot.replace('/', '\/'), '%s/apache2.conf'
            % srvroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        subprocess.Popen(['sed', '-i', 's/Directory \"\"/Directory \"%s\"/'
            % docroot.replace('/', '\/'), '%s/apache2.conf' % srvroot],
            stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT).wait()
        subprocess.Popen(['sed', '-i', 's/Listen/Listen %s/' % port,
            '%s/apache2.conf' % srvroot], stdout=open('/dev/null', 'w'),
            stderr=subprocess.STDOUT).wait()
        if subprocess.Popen(['which', 'apache2'],
                stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait():
            raise CommandNotFoundException("apache2 command not found. Please "
                "install apache2 web server and rerun tests.")
        args = shlex.split('apache2 -d %s -f apache2.conf -k start' % srvroot)
        rc = subprocess.Popen(args, stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT).wait()
        if rc:
            raise NonZeroReturnValueException("apache2 server exited with "
                "error %s" % rc)

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
        if os.path.exists("%s/rewrite.log" % srvroot):
            os.unlink("%s/rewrite.log" % srvroot)
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

    def test_licensefile_directly_linaro(self):
        search = "Index of /"
        testfile = fetcher.get(host + linaro_license_path)
        self.assertThat(testfile, Contains(search))

    def test_redirect_to_license_samsung(self):
        search = "PLEASE READ THE FOLLOWING AGREEMENT CAREFULLY"
        testfile = fetcher.get_or_return_license(host + samsung_test_file)
        self.assertThat(testfile[0], Contains(search))

    def test_redirect_to_license_ste(self):
        search = "PLEASE READ THE FOLLOWING AGREEMENT CAREFULLY"
        testfile = fetcher.get_or_return_license(host + ste_test_file)
        self.assertThat(testfile[0], Contains(search))

    def test_redirect_to_license_linaro(self):
        search = "Linaro license."
        testfile = fetcher.get_or_return_license(host + linaro_test_file)
        self.assertThat(testfile[0], Contains(search))

    def test_decline_license_samsung(self):
        search = "License has not been accepted"
        testfile = fetcher.get(host + samsung_test_file, accept_license=False)
        self.assertThat(testfile, Contains(search))

    def test_decline_license_ste(self):
        search = "License has not been accepted"
        testfile = fetcher.get(host + ste_test_file, accept_license=False)
        self.assertThat(testfile, Contains(search))

    def test_decline_license_linaro(self):
        search = "License has not been accepted"
        testfile = fetcher.get(host + linaro_test_file, accept_license=False)
        self.assertThat(testfile, Contains(search))

    def test_non_protected_dirs(self):
        search = "This is always available."
        testfile = fetcher.get(host + not_protected_test_file)
        self.assertThat(testfile, Contains(search))

    def test_never_available_dirs(self):
        search = "Forbidden"
        testfile = fetcher.get(host + never_available)
        self.assertThat(testfile, Contains(search))

    def test_accept_license_samsung_file(self):
        search = "This is protected with click-through Samsung license."
        testfile = fetcher.get(host + samsung_test_file)
        fetcher.close()
        if os.path.exists("%s/cookies.txt" % docroot):
            os.rename("%s/cookies.txt" % docroot,
                    "%s/cookies.samsung" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_accept_license_samsung_dir(self):
        search = "Index of /android/~linaro-android/staging-origen"
        testfile = fetcher.get(host + os.path.dirname(samsung_test_file))
        self.assertThat(testfile, Contains(search))

    def test_accept_license_ste_file(self):
        search = "This is protected with click-through ST-E license."
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
        search = "This is protected with click-through Samsung license."
        os.rename("%s/cookies.samsung" % docroot, "%s/cookies.txt" % docroot)
        testfile = fetcher.get(host + samsung_test_file)
        self.assertThat(testfile, Contains(search))

    def test_license_accepted_ste(self):
        search = "This is protected with click-through ST-E license."
        os.rename("%s/cookies.ste" % docroot, "%s/cookies.txt" % docroot)
        testfile = fetcher.get(host + ste_test_file)
        self.assertThat(testfile, Contains(search))

    def test_internal_host_samsung(self):
        search = "This is protected with click-through Samsung license."
        subprocess.Popen(['sed', '-i', '/## Let internal hosts through '
            'always./ a %s' % local_rewrite, '%s/.htaccess' % docroot],
            stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT).wait()
        testfile = fetcher.get(host + samsung_test_file, ignore_license=True)
        shutil.copy("%s/dothtaccess" % docroot, "%s/.htaccess" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_internal_host_ste(self):
        search = "This is protected with click-through ST-E license."
        subprocess.Popen(['sed', '-i', '/## Let internal hosts through '
            'always./ a %s' % local_rewrite, '%s/.htaccess' % docroot],
            stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT).wait()
        testfile = fetcher.get(host + ste_test_file, ignore_license=True)
        shutil.copy("%s/dothtaccess" % docroot, "%s/.htaccess" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_ste_open_file(self):
        search = "This is always available."
        testfile = fetcher.get(host + ste_open_test_file)
        self.assertThat(testfile, Contains(search))

    def test_per_file_accept_license_samsung_file(self):
        search = "This is protected with click-through Samsung license."
        testfile = fetcher.get(host + per_file_samsung_test_file)
        fetcher.close()
        if os.path.exists("%s/cookies.txt" % docroot):
            os.rename("%s/cookies.txt" % docroot,
                    "%s/cookies.samsung" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_per_file_accept_license_ste_file(self):
        search = "This is protected with click-through ST-E license."
        testfile = fetcher.get(host + per_file_ste_test_file)
        fetcher.close()
        if os.path.exists("%s/cookies.txt" % docroot):
            os.rename("%s/cookies.txt" % docroot, "%s/cookies.ste" % docroot)
        self.assertThat(testfile, Contains(search))

    def test_per_file_license_accepted_samsung(self):
        search = "This is protected with click-through Samsung license."
        os.rename("%s/cookies.samsung" % docroot, "%s/cookies.txt" % docroot)
        testfile = fetcher.get(host + per_file_samsung_test_file, ignore_license=True)
        self.assertThat(testfile, Contains(search))

    def test_per_file_license_accepted_ste(self):
        search = "This is protected with click-through ST-E license."
        os.rename("%s/cookies.ste" % docroot, "%s/cookies.txt" % docroot)
        testfile = fetcher.get(host + per_file_ste_test_file, ignore_license=True)
        self.assertThat(testfile, Contains(search))

    def test_per_file_non_protected_dirs(self):
        search = "MANIFEST"
        testfile = fetcher.get(host + per_file_not_protected_test_file)
        self.assertThat(testfile, Contains(search))

    def test_dir_containing_only_dirs(self):
        search = "Index of /android/~linaro-android"
        testfile = fetcher.get(host + dirs_only_dir)
        self.assertThat(testfile, Contains(search))

    def test_not_found_file(self):
        search = "Not Found"
        testfile = fetcher.get(host + not_found_test_file)
        self.assertThat(testfile, Contains(search))
