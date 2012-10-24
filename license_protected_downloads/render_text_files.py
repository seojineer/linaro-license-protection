import os
import re
import textile
import OrderedDict
from django.conf import settings


class MultipleFilesException(Exception):
    pass


class RenderTextFiles:

    def __init__(self):
        pass

    @classmethod
    def sort_tabs_by_priority(cls, a, b):
        base_list = settings.TAB_PRIORITY
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
                title = settings.FILES_MAP[os.path.basename(filepath)]
                result[title] = cls.render_file(filepath)

        if not filepaths and len(result) == 0:
            return None

        result_items = sorted(result.items(), cmp=cls.sort_tabs_by_priority)
        result = OrderedDict.OrderedDict()
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
        howtopath = os.path.join(path, settings.HOWTO_PATH)
        androidpaths = cls.dirEntries(howtopath, False,
                                      settings.ANDROID_FILES)
        ubuntupaths = cls.dirEntries(path, False, settings.LINUX_FILES)
        if len(androidpaths) > 0 and len(ubuntupaths) > 0:
            raise MultipleFilesException
        if len(androidpaths) > 0:
            for filepath in settings.ANDROID_FILES:
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
