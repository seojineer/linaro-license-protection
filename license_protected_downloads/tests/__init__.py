from license_protected_downloads.tests.test_models import *
from license_protected_downloads.tests.test_views import *
from license_protected_downloads.tests.test_buildinfo import *

#starts the test suite
__test__= {
    'LicenseTestCase': LicenseTestCase,
    'ViewTests': ViewTests,
    'BuildInfoTests': BuildInfoTests,
}
