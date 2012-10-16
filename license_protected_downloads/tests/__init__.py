from license_protected_downloads.tests.test_buildinfo import BuildInfoTests
from license_protected_downloads.tests.test_models import LicenseTestCase
from license_protected_downloads.tests.test_pep8 import TestPep8
from license_protected_downloads.tests.test_pyflakes import TestPyflakes
from license_protected_downloads.tests.test_views import ViewTests
from license_protected_downloads.tests.test_openid_auth import TestOpenIDAuth
from license_protected_downloads.tests.test_custom_commands \
 import SetsuperuserCommandTest
from license_protected_downloads.tests.test_render_text_files \
 import RenderTextFilesTests

#starts the test suite
__test__ = {
    'LicenseTestCase': LicenseTestCase,
    'ViewTests': ViewTests,
    'BuildInfoTests': BuildInfoTests,
    'TestPep8': TestPep8,
    'TestPyflakes': TestPyflakes,
    'TestOpenIDAuth': TestOpenIDAuth,
    'SetsuperuserCommandTest': SetsuperuserCommandTest,
    'RenderTextFilesTests': RenderTextFilesTests,
}
