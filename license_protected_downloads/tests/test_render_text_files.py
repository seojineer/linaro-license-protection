import os
import unittest
import tempfile
import shutil
import re
from license_protected_downloads.render_text_files import RenderTextFiles
from license_protected_downloads.render_text_files import NoFilesException
from license_protected_downloads.render_text_files import \
    MultipleFilesException
from license_protected_downloads.render_text_files import ANDROID_FILES
from license_protected_downloads.render_text_files import UBUNTU_FILES


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

    def test_find_relevant_files_no_files(self):
        path = self.make_temp_dir()
        with self.assertRaises(NoFilesException):
            RenderTextFiles.find_relevant_files(path)

    def test_find_relevant_files_multiple_files(self):
        path = tempfile.mkdtemp()
        handle, fname = tempfile.mkstemp(dir=path)
        shutil.move(fname, os.path.join(path, 'README'))
        path1 = tempfile.mkdtemp(dir=path)
        handle, fname = tempfile.mkstemp(dir=path1)
        shutil.move(fname, os.path.join(path1, 'README'))
        with self.assertRaises(MultipleFilesException):
            RenderTextFiles.find_relevant_files(path)

    def test_find_relevant_files_android(self):
        path = self.make_temp_dir(empty=False, file_list=ANDROID_FILES)
        full_android_files = []
        for file in ANDROID_FILES:
            full_android_files.append(os.path.join(path, file))
        self.assertEqual(full_android_files,
            RenderTextFiles.find_relevant_files(path))

    def test_find_relevant_files_android_subdir(self):
        path = self.make_temp_dir()
        full_path = self.make_temp_dir(empty=False, file_list=ANDROID_FILES,
                                       dir=path)
        full_android_files = []
        for file in ANDROID_FILES:
            full_android_files.append(os.path.join(full_path, file))
        self.assertEqual(full_android_files,
            RenderTextFiles.find_relevant_files(path))
        self.assertEqual(full_android_files,
            RenderTextFiles.find_relevant_files(full_path))

    def test_find_relevant_files_android_several_subdirs(self):
        path = self.make_temp_dir()
        full_path1 = self.make_temp_dir(empty=False, file_list=ANDROID_FILES,
            dir=path)
        full_path2 = self.make_temp_dir(empty=False, file_list=ANDROID_FILES,
            dir=path)
        full_android_files1 = []
        full_android_files2 = []
        for file in ANDROID_FILES:
            full_android_files1.append(os.path.join(full_path1, file))
            full_android_files2.append(os.path.join(full_path2, file))
        with self.assertRaises(MultipleFilesException):
            RenderTextFiles.find_relevant_files(path)
        self.assertEqual(full_android_files1,
            RenderTextFiles.find_relevant_files(full_path1))
        self.assertEqual(full_android_files2,
            RenderTextFiles.find_relevant_files(full_path2))

    def test_find_relevant_files_android_and_ubuntu_samedir(self):
        flist = ANDROID_FILES + UBUNTU_FILES
        path = self.make_temp_dir(empty=False, file_list=flist)
        full_files = []
        for file in flist:
            full_files.append(os.path.join(path, file))
        self.assertListEqual(sorted(full_files),
            sorted(RenderTextFiles.find_relevant_files(path)))

    def test_find_relevant_files_android_and_ubuntu_different_subdirs(self):
        path = self.make_temp_dir()
        android_path = self.make_temp_dir(empty=False, file_list=ANDROID_FILES,
                                          dir=path)
        ubuntu_path = self.make_temp_dir(empty=False, file_list=UBUNTU_FILES,
                                         dir=path)
        full_android_files = []
        full_ubuntu_files = []
        for file in ANDROID_FILES:
            full_android_files.append(os.path.join(android_path, file))
        for file in UBUNTU_FILES:
            full_ubuntu_files.append(os.path.join(ubuntu_path, file))
        self.assertEqual(sorted(full_android_files + full_ubuntu_files),
            sorted(RenderTextFiles.find_relevant_files(path)))
        self.assertEqual(sorted(full_android_files),
            sorted(RenderTextFiles.find_relevant_files(android_path)))
        self.assertEqual(sorted(full_ubuntu_files),
            sorted(RenderTextFiles.find_relevant_files(ubuntu_path)))

    def test_sort_paths_list_by_files_list(self):
        path = self.make_temp_dir(empty=False, file_list=UBUNTU_FILES)
        full_ubuntu_files = []
        for file in UBUNTU_FILES:
            full_ubuntu_files.append(os.path.join(path, file))
        paths_list = RenderTextFiles.find_relevant_files(path)
        self.assertEqual(full_ubuntu_files,
                         sorted(paths_list,
                                cmp=RenderTextFiles.sort_paths_list_by_files_list))
        self.assertNotEqual(full_ubuntu_files, paths_list)
