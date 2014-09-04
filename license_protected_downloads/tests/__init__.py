from license_protected_downloads.tests.test_buildinfo import (
    BuildInfoTests,
    FileNameMatchingTests,
)
from license_protected_downloads.tests.test_splicebuildinfos import (
    SpliceBuildInfosTests
)
from license_protected_downloads.tests.test_models import (
    LicenseTestCase,
    APITokenTests,
)
from license_protected_downloads.tests.test_pep8 import TestPep8
from license_protected_downloads.tests.test_pyflakes import TestPyflakes
from license_protected_downloads.tests.test_common import (
    CommonTests,
)
from license_protected_downloads.tests.test_views import (
    FileViewTests,
    HowtoViewTests,
    ViewTests,
    ViewHelpersTests,
)
from license_protected_downloads.tests.test_api_v1 import (
    APITests,
)
from license_protected_downloads.tests.test_api_v2 import (
    APIv2Tests,
)
from license_protected_downloads.tests.test_openid_auth import TestOpenIDAuth
from license_protected_downloads.tests.test_custom_commands import (
    SetsuperuserCommandTest
)
from license_protected_downloads.tests.test_render_text_files import (
    RenderTextFilesTests
)

#starts the test suite
__test__ = {
    'CommonTests': CommonTests,
    'APITests': APITests,
    'APIv2Tests': APIv2Tests,
    'APITokenTests': APITokenTests,
    'BuildInfoTests': BuildInfoTests,
    'SpliceBuildInfosTests': SpliceBuildInfosTests,
    'FileNameMatchingTests': FileNameMatchingTests,
    'FileViewTests': FileViewTests,
    'HowtoViewTests': HowtoViewTests,
    'LicenseTestCase': LicenseTestCase,
    'RenderTextFilesTests': RenderTextFilesTests,
    'SetsuperuserCommandTest': SetsuperuserCommandTest,
    'TestOpenIDAuth': TestOpenIDAuth,
    'TestPep8': TestPep8,
    'TestPyflakes': TestPyflakes,
    'ViewTests': ViewTests,
    'ViewHelpersTests': ViewHelpersTests,
}
