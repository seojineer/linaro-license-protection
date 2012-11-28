# Copyright (c)2012 Linaro.
# Test helpers.

import os
import shutil
import tempfile


class temporary_directory(object):
    """Creates a context manager for a temporary directory."""

    def __enter__(self):
        self.root = tempfile.mkdtemp()
        return self

    def __exit__(self, *args):
        shutil.rmtree(self.root)

    def make_file(self, name, data=None, with_buildinfo=False):
        """Creates a file in this temporary directory."""
        full_path = os.path.join(self.root, name)
        dir_name = os.path.dirname(full_path)
        try:
            os.makedirs(dir_name)
        except os.error:
            pass
        if with_buildinfo:
            buildinfo_name = os.path.join(dir_name, 'BUILD-INFO.txt')
            base_name = os.path.basename(full_path)
            with open(buildinfo_name, 'w') as buildinfo_file:
                buildinfo_file.write(
                    'Format-Version: 0.1\n\n'
                    'Files-Pattern: %s\n'
                    'License-Type: open\n' % base_name)
        target = open(full_path, "w")
        if data is None:
            return target
        else:
            target.write(data)
            target.close()
            return full_path

