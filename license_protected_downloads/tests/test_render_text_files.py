import os
import unittest
import tempfile
import shutil
import re
from django.conf import settings
from license_protected_downloads.render_text_files import RenderTextFiles
from license_protected_downloads.render_text_files \
 import MultipleFilesException

THIS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class RenderTextFilesTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_flatten_list(self):
        l = ['1', ['2', '3']]
        self.assertEqual(['1', '2', '3'], RenderTextFiles.flatten(l))

    def test_flatten_tuple(self):
        l = ('1', ('2', '3'))
        self.assertEqual(('1', '2', '3'), RenderTextFiles.flatten(l))

    def test_findall(self):
        l = ['1test', 'test2', '3', 'test', '1']
        self.assertEqual([0, 1, 3],
            RenderTextFiles.findall(l, lambda x: re.search(r'test', x)))

    def test_findall_empty(self):
        l = []
        self.assertEqual([],
            RenderTextFiles.findall(l, lambda x: re.search(r'1', x)))

    def make_temp_dir(self, empty=True, file_list=None, dir=None):
        path = tempfile.mkdtemp(dir=dir)
        if not empty:
            if file_list:
                for file in file_list:
                    handle, fname = tempfile.mkstemp(dir=path)
                    shutil.move(fname, os.path.join(path, file))
        return path

    def test_find_relevant_files_android(self):
        path = self.make_temp_dir(empty=False,
                                  file_list=settings.ANDROID_FILES)
        full_android_files = []
        for file in settings.ANDROID_FILES:
            full_android_files.append(os.path.join(path, file))
        self.assertEqual(sorted(full_android_files),
            sorted(RenderTextFiles.find_relevant_files(path)))

    def test_find_relevant_files_android_subdir(self):
        path = self.make_temp_dir()
        full_path = self.make_temp_dir(empty=False,
                                       file_list=settings.ANDROID_FILES,
                                       dir=path)
        full_android_files = []
        for file in settings.ANDROID_FILES:
            full_android_files.append(os.path.join(full_path, file))
        self.assertEqual([],
            sorted(RenderTextFiles.find_relevant_files(path)))
        self.assertEqual(sorted(full_android_files),
            sorted(RenderTextFiles.find_relevant_files(full_path)))

    def test_find_relevant_files_android_and_ubuntu_samedir(self):
        path = self.make_temp_dir(empty=False,
                    file_list=settings.LINUX_FILES + settings.ANDROID_FILES)
        full_files = []
        for file in settings.ANDROID_FILES:
            full_files.append(os.path.join(path, file))
            open(os.path.join(path, file), 'w').close()
        for file in settings.LINUX_FILES:
            full_files.append(os.path.join(path, file))
        with self.assertRaises(MultipleFilesException):
            RenderTextFiles.find_relevant_files(path)
