import os
import re
import textile
from collections import OrderedDict
from django.conf import settings

HOWTO_PATH = 'howto/'

UBUNTU_FILES = ('README',
                'INSTALL',
                'HACKING',
                'FIRMWARE',
                'RTSM')
ANDROID_FILES = ('HOWTO_releasenotes.txt',
                 'HOWTO_install.txt',
                 'HOWTO_getsourceandbuild.txt',
                 'HOWTO_flashfirmware.txt',
                 'HOWTO_rtsm.txt')

MANDATORY_ANDROID_FILES = ('HOWTO_install.txt',
                           'HOWTO_getsourceandbuild.txt',
                           'HOWTO_flashfirmware.txt')

FILES_MAP = {'HOWTO_releasenotes.txt': 'Release Notes',
             'HOWTO_install.txt': 'Binary Image Installation',
             'HOWTO_getsourceandbuild.txt': 'Building From Source',
             'HOWTO_flashfirmware.txt': 'Firmware Update',
             'HOWTO_rtsm.txt': 'RTSM',
             'README': 'Release Notes',
             'INSTALL': 'Binary Image Installation',
             'HACKING': 'Building From Source',
             'FIRMWARE': 'Firmware Update',
             'RTSM': 'RTSM'}

TAB_PRIORITY = ['Release Notes',
                'Binary Image Installation',
                'Building From Source',
                'Firmware Update',
                'RTSM']


class MultipleFilesException(Exception):
    pass


class RenderTextFiles:

    def __init__(self):
        pass

    @classmethod
    def sort_tabs_by_priority(cls, a, b):
        base_list = TAB_PRIORITY
        return base_list.index(a[0]) - base_list.index(b[0])

    @classmethod
    def find_and_render(cls, path):

        result = {}

        try:
            filepaths = cls.find_relevant_files(path)
        except:
            # This is ok, no tabs when multiple returned.
            return None

        if filepaths:
            for filepath in filepaths:
                title = FILES_MAP[os.path.basename(filepath)]
                result[title] = cls.render_file(filepath)

        # Switch to fallback data for mandatory files.
        if cls.check_for_manifest_or_tarballs(path):
            for filename in MANDATORY_ANDROID_FILES:
                if FILES_MAP[filename] not in result:
                    filepath = os.path.join(settings.TEXTILE_FALLBACK_PATH,
                                            filename)
                    title = FILES_MAP[filename]
                    result[title] = cls.render_file(filepath)

        if not filepaths and len(result) == 0:
            return None

        result_items = sorted(result.items(), cmp=cls.sort_tabs_by_priority)
        result = OrderedDict()
        for v, k in result_items:
            result[v] = k
        return result

    @classmethod
    def render_file(cls, filepath):
        try:
            file_obj = open(filepath, 'r')
            return textile.textile(file_obj.read())
        except:
            # Do nothing, parsing failed.
            pass

    @classmethod
    def find_relevant_files(cls, path):
        # Go recursively and find howto's, readme's, hackings, installs.
        # If there are more of the same type then one, throw custom error as
        # written above.
        multiple = 0
        howtopath = os.path.join(path, HOWTO_PATH)
        androidpaths = cls.dirEntries(howtopath, False, ANDROID_FILES)
        ubuntupaths = cls.dirEntries(path, False, UBUNTU_FILES)
        if len(androidpaths) > 0 and len(ubuntupaths) > 0:
            raise MultipleFilesException
        if len(androidpaths) > 0:
            for filepath in ANDROID_FILES:
                if len(cls.findall(androidpaths,
                                   lambda x: re.search(filepath, x))) > 1:
                    multiple += 1
            if multiple == 0:
                return androidpaths
            else:
                raise MultipleFilesException
        elif len(ubuntupaths) > 0:
            return ubuntupaths
        else:
            return []

    @classmethod
    def flatten(cls, l, ltypes=(list, tuple)):
        ltype = type(l)
        l = list(l)
        i = 0
        while i < len(l):
            while isinstance(l[i], ltypes):
                if not l[i]:
                    l.pop(i)
                    i -= 1
                    break
                else:
                    l[i:i + 1] = l[i]
            i += 1
        return ltype(l)

    @classmethod
    def dirEntries(cls, path, subdir, *args):
        ''' Return a list of file names found in directory 'dir_name'
            If 'subdir' is True, recursively access subdirectories under
            'dir_name'.
            Additional arguments, if any, are file names to match filenames.
            Matched file names are added to the list.
            If there are no additional arguments, all files found in the
            directory are added to the list.
        '''
        fileList = []
        if not os.path.exists(path):
            return fileList
        for file in os.listdir(path):
            dirfile = os.path.join(path, file)
            if os.path.isfile(dirfile):
                if not args:
                    fileList.append(dirfile)
                else:
                    if file in cls.flatten(args):
                        fileList.append(dirfile)
            # recursively access file names in subdirectories
            elif os.path.isdir(dirfile) and subdir:
                fileList.extend(cls.dirEntries(dirfile, subdir, *args))
        return fileList

    @classmethod
    def findall(cls, L, test):
        ''' Return indices of list items that pass the 'test'
        '''
        i = 0
        indices = []
        while(True):
            try:
                # next value in list passing the test
                nextvalue = filter(test, L[i:])[0]
                # add index of this value in the index list,
                # by searching the value in L[i:]
                indices.append(L.index(nextvalue, i))
                # iterate i, that is the next index from where to search
                i = indices[-1] + 1
            # when there is no further "good value", filter returns [],
            # hence there is an out of range exception
            except IndexError:
                return indices

    @classmethod
    def check_for_manifest_or_tarballs(cls, path):
        ''' Check if there is a MANIFEST file in current path or a tarball.
        Also check if we are currently somewhere in 'android' path.
        This hack is necessary for fallback wiki howto links.
        '''
        if 'android' in path:
            for filename in os.listdir(path):
                if "MANIFEST" in filename:
                    return True
                if "tar.bz2" in filename:
                    return True
                if ".img" in filename:
                    return True

        return False
