import os
import re
from textile.textilefactory import TextileFactory


UBUNTU_FILES = ('README',
                'INSTALL',
                'HACKING')
ANDROID_FILES = ('HOWTO_install.txt',
                 'HOWTO_getsourceandbuild.txt',
                 'HOWTO_flashuboot.txt')


class MultipleFilesException(Exception):
    pass


class NoFilesException(Exception):
    pass


class RenderTextFiles:

    def __init__(self):
        pass

    @classmethod
    def find_and_render(cls, path):

        result = {}

        try:
            filepaths = cls.find_relevant_files(path)
        except:
            # This is ok, no tabs when none is returned.
            return None

        if filepaths:
            for filepath in filepaths:
                try:
                    file_obj = open(filepath, 'r')
                    title, formatted = cls.render_file(file_obj)
                    result[title] = formatted
                except:
                    # TODO: log error or something.
                    continue
        else:
            return None

        return result

    @classmethod
    def render_file(cls, file_obj):
        # TODO: introduce special options to textile factory if necessary.
        textile_factory = TextileFactory()
        title = file_obj.readline()
        file_obj.seek(0)
        return title, textile_factory.process(file_obj.read())

    @classmethod
    def find_relevant_files(cls, path):
        # Go recursively and find howto's, readme's, hackings, installs.
        # If there are more of the same type then one, throw custom error as
        # written above.
        multiple = 0
        filepaths = cls.dirEntries(path, True, UBUNTU_FILES, ANDROID_FILES)
        if len(filepaths)>0:
            for filepath in UBUNTU_FILES:
                if len(cls.findall(filepaths, lambda x: re.search(filepath, x)))>1:
                    multiple += 1
            for filepath in ANDROID_FILES:
                if len(cls.findall(filepaths, lambda x: re.search(filepath, x)))>1:
                    multiple += 1
            if multiple == 0:
                return filepaths
            else:
                raise MultipleFilesException
        else:
            raise NoFilesException

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
        i=0
        indices = []
        while(True):
            try:
                # next value in list passing the test
                nextvalue = filter(test, L[i:])[0]
                # add index of this value in the index list,
                # by searching the value in L[i:]
                indices.append(L.index(nextvalue, i))
                # iterate i, that is the next index from where to search
                i=indices[-1]+1
            # when there is no further "good value", filter returns [],
            # hence there is an out of range exception
            except IndexError:
                return indices
