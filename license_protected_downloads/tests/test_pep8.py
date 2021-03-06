# Copyright (C) 2012 Linaro Ltd.
#
# Author: Loic Minier <loic.minier@linaro.org>
#
# This file is part of Linaro Image Tools.
#
# Linaro Image Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linaro Image Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import unittest


@unittest.skipIf(os.environ.get('SKIP_LINT'), 'Skipping lint tests')
class TestPep8(unittest.TestCase):
    def test_pep8(self):
        # Errors we have to ignore for now: use pep8 error codes like 'E202'.
        ignore = []
        # Ignore return code.
        args = [
            'pep8',
            '--repeat',
            '--ignore=%s' % ','.join(ignore),
            '--exclude=static',
            '.'
        ]
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        self.assertEquals('', stdout)
        self.assertEquals('', stderr)
