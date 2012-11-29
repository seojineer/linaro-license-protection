import os
import textile
import OrderedDict
from django.conf import settings


HOWTO_PATH = "howto"
HOWTO_PRODUCT_PATH = "target/product"


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
        # Raise MultipleFilesException if files from ANDROID_FILES and
        # LINUX_FILES exist in the same dir.

        androidpaths = cls.dirEntries(path, files_list=settings.ANDROID_FILES)

        howto_path = os.path.join(path, HOWTO_PATH)
        howto_product_path = cls.getHowtoProductPath(path)
        androidpaths += cls.dirEntries(howto_path,
                                       files_list=settings.ANDROID_FILES)
        androidpaths += cls.dirEntries(howto_product_path,
                                       files_list=settings.ANDROID_FILES)

        ubuntupaths = cls.dirEntries(path, files_list=settings.LINUX_FILES)
        if len(androidpaths) > 0 and len(ubuntupaths) > 0:
            # Files from ANDROID_FILES and LINUX_FILES exist in the same dir
            raise MultipleFilesException(
                "Both Android and Ubuntu HOWTO files "
                "are found, which is unsupported.")
        else:
            if len(androidpaths) > 0:
                return androidpaths
            else:
                return ubuntupaths

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
    def dirEntries(cls, path, files_list=None):
        ''' Return a list of file names found in directory 'path'
            'files_list' are file names to match filenames. Matched file names
            are added to the list.
            If there are no additional arguments, all files found in the
            directory are added to the list.
        '''
        fileList = []
        if os.path.exists(path):
            for file in os.listdir(path):
                dirfile = os.path.join(path, file)
                if os.path.isfile(dirfile):
                    if not files_list:
                        fileList.append(dirfile)
                    else:
                        if file in cls.flatten(files_list):
                            fileList.append(dirfile)
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
    def getHowtoProductPath(cls, path):
        """ Return the 'target/product/*/howto/ path.

        In case there is no such folder, return empty string.
        """
        howto_path = ""
        path = os.path.join(path, HOWTO_PRODUCT_PATH)
        if os.path.exists(path):
            for file in os.listdir(path):
                product_path = os.path.join(path, file)
                if os.path.isdir(product_path):
                    howto_path = os.path.join(product_path, HOWTO_PATH)
                    break

        return howto_path
