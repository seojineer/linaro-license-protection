#!/usr/bin/env python

import re
import os, sys
import shutil
import shlex, subprocess

from filefetcher import LicenseProtectedFileFetcher

cwd = os.getcwd()
docroot = os.path.abspath(os.path.join(*([cwd] + ['..'])))
local_rewrite = 'RewriteCond %{REMOTE_ADDR} 127.0.0.1 [OR]'

# Now not all tests pass in usermode, .htaccess file needs to be fixed
# To successfully run all tests use 
#host = 'http://127.0.0.1'
# and run tests with 'sudo'.

host = 'http://127.0.0.1'
port = '80'
samsung_license_path = '/licenses/samsung-v2.html'
ste_license_path = '/licenses/ste.html'
samsung_test_file = '/android/~linaro-android/staging-origen/test.txt'
ste_test_file = '/android/~linaro-android/staging-snowball/test.txt'
not_protected_test_file = '/android/~linaro-android/staging-panda/test.txt'

def test_internal_host_samsung(url, fetcher):
    testfile = fetcher.get(url, ignore_license=True)
    for line in testfile.splitlines():
        res = re.search("This is a protected with click-through Samsung "
                        "license.", line)
        res1 = re.search("Index of /android/~linaro-android/staging-origen",
                        line)
        if res or res1:
            return 0

    return 1

def test_internal_host_ste(url, fetcher):
    testfile = fetcher.get(url, ignore_license=True)
    for line in testfile.splitlines():
        res = re.search("This is a protected with click-through ST-E license.",
                        line)
        res1 = re.search("Index of /android/~linaro-android/staging-snowball",
                        line)
        if res or res1:
            return 0

    return 1

def test_licensefile_directly(url, fetcher):

    testfile = fetcher.get(url)
    for line in testfile.splitlines():
        res = re.search("Index of /", line)
        if res:
            return 0

    return 1

def test_license_accepted_samsung(url, fetcher):

    testfile = fetcher.get(url, ignore_license=True)
    for line in testfile.splitlines():
        res = re.search("This is a protected with click-through Samsung "
                        "license.", line)
        res1 = re.search("Index of /android/~linaro-android/staging-origen",
                        line)
        if res or res1:
            return 0

    return 1

def test_license_accepted_ste(url, fetcher):

    testfile = fetcher.get(url, ignore_license=True)
    for line in testfile.splitlines():
        res = re.search("This is a protected with click-through ST-E license.",
                        line)
        res1 = re.search("Index of /android/~linaro-android/staging-snowball",
                        line)
        if res or res1:
            return 0

    return 1

def test_accept_license_samsung(url, fetcher):

    testfile = fetcher.get(url)
    for line in testfile.splitlines():
        res = re.search("This is a protected with click-through Samsung "
                        "license.", line)
        res1 = re.search("Index of /android/~linaro-android/staging-origen",
                        line)
        if res or res1:
            return 0

    return 1

def test_accept_license_ste(url, fetcher):

    testfile = fetcher.get(url)
    for line in testfile.splitlines():
        res = re.search("This is a protected with click-through ST-E license.",
                        line)
        res1 = re.search("Index of /android/~linaro-android/staging-snowball",
                        line)
        if res or res1:
            return 0

    return 1

def test_decline_license(url, fetcher):

    testfile = fetcher.get(url, accept_license=False)
    for line in testfile.splitlines():
        res = re.search("The requested URL /licenses/nolicense.html was not "
                        "found on this server", line)
        res1 = re.search("License has not been accepted", line)
        if res or res1:
            return 0

    return 1

def test_non_protected_dirs(url, fetcher):

    testfile = fetcher.get(url)
    for line in testfile.splitlines():
        res = re.search("This is always available.", line)
        if res:
            return 0

    return 1

def test_redirect_to_license_samsung(url, fetcher):

    testfile = fetcher.get(url, ignore_license=True)
    for line in testfile.splitlines():
        res = re.search("SAMSUNG DEVELOPMENT TOOL KIT END-USER LICENSE "
                        "AGREEMENT", line)
        if res:
            return 0

    return 1

def test_redirect_to_license_ste(url, fetcher):

    testfile = fetcher.get(url, ignore_license=True)
    for line in testfile.splitlines():
        res = re.search("LIMITED LICENSE AGREEMENT FOR APPLICATION DEVELOPERS",
                        line)
        if res:
            return 0

    return 1

def setup():
    global host
    host = host + ':' + port 
    shutil.copy("apache2.conf.tmpl", "apache2.conf")
    shutil.copy("%s/.htaccess" % docroot, "%s/dothtaccess" % docroot)
    subprocess.Popen(['sed', '-i' , 's/ServerRoot \"\"/ServerRoot \"%s\"/' % cwd.replace('/', '\/'),
                    'apache2.conf'], stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT).wait()
    subprocess.Popen(['sed', '-i' , 's/DocumentRoot \"\"/DocumentRoot \"%s\"/' % docroot.replace('/', '\/'),
                    'apache2.conf'], stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT).wait()
    subprocess.Popen(['sed', '-i' , 's/Directory \"\"/Directory \"%s\"/' % docroot.replace('/', '\/'),
                    'apache2.conf'], stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT).wait()
    subprocess.Popen(['sed', '-i' , 's/Listen/Listen %s/' % port,
                    'apache2.conf'], stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT).wait()
 
    if subprocess.Popen(['which', 'apache2'], stdout=open('/dev/null', 'w'),
                        stderr=subprocess.STDOUT).wait():
        print "apache2 command not found. Please install apache2 web server " \
                "and rerun tests."
        sys.exit(1)

    args = shlex.split('apache2 -d ./ -f apache2.conf -k start')
    rc = subprocess.Popen(args, stdout=open('/dev/null', 'w'),
                        stderr=subprocess.STDOUT).wait()
    if rc:
        print "apache2 server exited with error %s" % rc
        sys.exit(rc)

def cleanup():
    if os.path.exists("cookies.txt"):
        os.unlink("cookies.txt")
    args = shlex.split('apache2 -d ./ -f apache2.conf -k stop')
    subprocess.Popen(args, stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT).wait()
    os.unlink("apache2.conf")
    os.unlink("click_through_license_access.log")
    os.unlink("click_through_license_error.log")
    os.rename("%s/dothtaccess" % docroot, "%s/.htaccess" % docroot)

def run():

    passed = 0
    failed = 0

    setup()
    fetcher = LicenseProtectedFileFetcher()

    rc = test_licensefile_directly(host + samsung_license_path, fetcher)
    if rc:
        failed += 1
        print "FAIL: Samsung license file was accessed directly"
    else:
        passed += 1

    rc = test_licensefile_directly(host + ste_license_path, fetcher)
    if rc:
        failed += 1
        print "FAIL: ST-E license file was accessed directly"
    else:
        passed += 1

    rc = test_redirect_to_license_samsung(host + samsung_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Redirection to Samsung license didn't happen"
    else:
        passed += 1

    rc = test_redirect_to_license_ste(host + ste_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Redirection to ST-E license didn't happen"
    else:
        passed += 1

    rc = test_decline_license(host + samsung_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Samsung license was not declined properly"
    else:
        passed += 1

    rc = test_decline_license(host + ste_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: ST-E license was not declined properly"
    else:
        passed += 1

    rc = test_non_protected_dirs(host + not_protected_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Non-protected file was not retrieved"
    else:
        passed += 1

    rc = test_accept_license_samsung(host + samsung_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected Samsung file was not retrieved"
    else:
        passed += 1

    fetcher.close()
    if os.path.exists("cookies.txt"):
        os.unlink("cookies.txt")

    fetcher = LicenseProtectedFileFetcher()
    rc = test_accept_license_samsung(host + os.path.dirname(samsung_test_file), fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected Samsung dir listing was not retrieved"
    else:
        passed += 1

    fetcher.close()
    if os.path.exists("cookies.txt"):
        os.rename("cookies.txt", "cookies.samsung")

    fetcher = LicenseProtectedFileFetcher()
    url = "http://127.0.0.1:8080/android/~linaro-android/staging-snowball/test.txt"
    rc = test_accept_license_ste(host + ste_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected ST-E file was not retrieved"
    else:
        passed += 1

    fetcher.close()
    if os.path.exists("cookies.txt"):
        os.unlink("cookies.txt")

    fetcher = LicenseProtectedFileFetcher()
    rc = test_accept_license_ste(host + os.path.dirname(ste_test_file), fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected ST-E dir listing not retrieved"
    else:
        passed += 1

    fetcher.close()
    if os.path.exists("cookies.txt"):
        os.rename("cookies.txt", "cookies.ste")

    fetcher = LicenseProtectedFileFetcher()
    os.rename("cookies.samsung", "cookies.txt")
    rc = test_license_accepted_samsung(host + samsung_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected Samsung file was not retrieved with cookie"
    else:
        passed += 1

    fetcher.close()
    if os.path.exists("cookies.txt"):
        os.unlink("cookies.txt")

    fetcher = LicenseProtectedFileFetcher()
    os.rename("cookies.ste", "cookies.txt")
    rc = test_license_accepted_ste(host + ste_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected ST-E file was not retrieved with cookie"
    else:
        passed += 1

    fetcher.close()
    if os.path.exists("cookies.txt"):
        os.unlink("cookies.txt")

    fetcher = LicenseProtectedFileFetcher()
    subprocess.Popen(['sed', '-i' , '/RewriteEngine On/ a %s' % local_rewrite,
                    '%s/.htaccess' % docroot], stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT).wait()
    rc = test_internal_host_samsung(host + samsung_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected Samsung file was not retrieved by internal host"
    else:
        passed += 1

    fetcher = LicenseProtectedFileFetcher()
    rc = test_internal_host_ste(host + ste_test_file, fetcher)
    if rc:
        failed += 1
        print "FAIL: Protected ST-E file was not retrieved by internal host"
    else:
        passed += 1

    print "PASSED = %s, FAILED = %s" % (passed, failed)

    fetcher.close()
    cleanup()

if __name__ == '__main__':
    run()
