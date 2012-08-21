#!/usr/bin/env python
# Print the list of build directories with no license protection.

import sys
import os


class Validation():

    LICENSE_FILE_LIST = [
        "EULA.txt",
        "OPEN-EULA.txt",
        "BUILD-INFO.txt",
        ]

    def __init__(self):
        pass

    @classmethod
    def find_non_protected_dirs(cls, rootdir):

        non_handled_dirs = []

        for root, subFolders, files in os.walk(rootdir):

            for dir in subFolders:
                dir_path = os.path.join(root, dir)
                has_build = False
                for fname in os.listdir(dir_path):
                    if os.path.isfile(os.path.join(dir_path, fname)):
                        if "gz" in os.path.splitext(fname)[1] or \
                            "bz2" in os.path.splitext(fname)[1]:
                            has_build = True
                            break
                if has_build:
                    if not cls.has_license_handling(dir_path):
                        non_handled_dirs.append(dir_path)

        return non_handled_dirs

    @classmethod
    def has_license_handling(cls, dir_path):
        for fname in os.listdir(dir_path):
            if os.path.isfile(os.path.join(dir_path, fname)):
                for mode in cls.LICENSE_FILE_LIST:
                    if mode in fname:
                        return True
        return False

if __name__ == '__main__':

    result_dirs = Validation.find_non_protected_dirs(sys.argv[1])
    for dir in result_dirs:
        print dir
