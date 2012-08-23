#!/usr/bin/env python
# Print the list of build directories with no license protection.

import sys
import os
import fnmatch


class Validation():

    LICENSE_FILE_LIST = [
        "EULA.txt",
        "OPEN-EULA.txt",
        "BUILD-INFO.txt",
        ]

    def __init__(self):
        pass

    @classmethod
    def has_license_handling(cls, dir_path):
        """Check if there is any form of license handling in directory."""
        for fname in os.listdir(dir_path):
            if os.path.isfile(os.path.join(dir_path, fname)):
                for mode in cls.LICENSE_FILE_LIST:
                    if mode in fname:
                        return True
        return False

    @classmethod
    def has_open_eula(cls, dir_path):
        """Check if there is OPEN-EULA file in a directory."""
        for fname in os.listdir(dir_path):
            if os.path.isfile(os.path.join(dir_path, fname)):
                if "OPEN-EULA" in fname:
                    return True
        return False

    @classmethod
    def has_build_info(cls, dir_path):
        """Check if there is BUILD-INFO file in a directory."""
        for fname in os.listdir(dir_path):
            if os.path.isfile(os.path.join(dir_path, fname)):
                if "BUILD-INFO.txt" in fname:
                    return True
        return False

    @classmethod
    def get_regular_files(cls, dir_path):
        """Returns all non-meta files in a directory."""
        result_files = []

        for fname in os.listdir(dir_path):
            is_meta = False
            file_path = os.path.join(dir_path, fname)
            if os.path.isfile(file_path):
                for mode in cls.LICENSE_FILE_LIST:
                    if mode in fname:
                        is_meta = True
                if not is_meta:
                    result_files.append(fname)

        return result_files

    @classmethod
    def get_build_info_patterns(cls, build_info_path):
        """Get all patterns from BUILD-INFO file."""
        patterns = []

        with open(build_info_path, "r") as infile:
            lines = infile.readlines()

        for line in lines:
            line = line.strip()
            if line != '' and "Files-Pattern" in line:
                values = line.split(":", 1)
                patterns.append(values[1].strip())

        return patterns

    @classmethod
    def get_dirs_with_build(cls, rootdir):
        """Get only bottom level directories which contain builds."""

        result_paths = []

        for root, subFolders, files in os.walk(rootdir):

            for dir in subFolders:
                dir_path = os.path.join(root, dir)
                for fname in os.listdir(dir_path):
                    if os.path.isfile(os.path.join(dir_path, fname)):
                        if "gz" in os.path.splitext(fname)[1] or \
                            "bz2" in os.path.splitext(fname)[1]:
                            result_paths.append(dir_path)
                            break
        return result_paths

    @classmethod
    def get_dirs_with_build_info(cls, rootdir):
        """Get only bottom level directories which contain builds."""

        build_info_dirs = []
        dirs_with_build = cls.get_dirs_with_build(rootdir)

        for dir_path in dirs_with_build:
            if cls.has_build_info(dir_path):
                build_info_dirs.append(dir_path)

        return build_info_dirs

    @classmethod
    def find_non_protected_dirs(cls, rootdir):

        non_handled_dirs = []
        dirs_with_build = cls.get_dirs_with_build(rootdir)

        for dir_path in dirs_with_build:
            if not cls.has_license_handling(dir_path):
                non_handled_dirs.append(dir_path)

        return non_handled_dirs

    @classmethod
    def find_licensed_with_open_eula(cls, rootdir):

        result_dirs = []
        dirs_with_build = cls.get_dirs_with_build(rootdir)

        for dir_path in dirs_with_build:
            if "origen" in dir_path or "snowball" in dir_path:
                if cls.has_open_eula(dir_path):
                    result_dirs.append(dir_path)

        return result_dirs

    @classmethod
    def find_non_matched_build_info_files(cls, rootdir):

        result_files = []
        dirs_with_build_info = cls.get_dirs_with_build_info(rootdir)

        for dir_path in dirs_with_build_info:
            buildinfo_path = os.path.join(dir_path, "BUILD-INFO.txt")

            if os.path.isfile(buildinfo_path):
                patterns = cls.get_build_info_patterns(buildinfo_path)
                for fname in cls.get_regular_files(dir_path):
                    file_matched = False

                    for pattern in patterns:
                        if fnmatch.fnmatch(fname, pattern):
                            file_matched = True
                            continue

                    if not file_matched:
                        result_files.append(os.path.join(dir_path, fname))

        return result_files

if __name__ == '__main__':

    print "-" * 31
    print "Non protected paths with builds"
    print "-" * 31
    result_dirs = Validation.find_non_protected_dirs(sys.argv[1])
    for dir in result_dirs:
        print dir

    print "-" * 50
    print "Origen and snowball builds licensed with Open EULA"
    print "-" * 50
    result_dirs = Validation.find_licensed_with_open_eula(sys.argv[1])
    for dir in result_dirs:
        print dir

    print "-" * 62
    print "Builds with BUILD INFO file not covered by build info patterns"
    print "-" * 62
    result_files = Validation.find_non_matched_build_info_files(sys.argv[1])
    for file in result_files:
        print file
