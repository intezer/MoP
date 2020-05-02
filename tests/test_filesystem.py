#!/usr/bin/env python3
import unittest
import os
import shutil

from stage_props import utils
import stage_props.filesystem

TEST_ARTIFACTS_STORE = 'artifacts'


class TestVirtualFileSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            os.makedirs(TEST_ARTIFACTS_STORE)
        except OSError:
            pass
        cls.virtual_filesystem = stage_props.filesystem.VirtualFileSystem(TEST_ARTIFACTS_STORE, 'omrib')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_ARTIFACTS_STORE)

    def test_users_directory(self):
        for name in ['All Users', 'omrib', 'Public']:
            full_path = stage_props.filesystem.win_path_join('c:\\users', name)
            r = TestVirtualFileSystem.virtual_filesystem.is_dir(full_path)
            self.assertTrue(r)

    def test_mkdir(self):
        TestVirtualFileSystem.virtual_filesystem.mkdir('c:\\my_dir')
        self.assertTrue('my_dir' in TestVirtualFileSystem.virtual_filesystem.listdir('c:\\')[0])

    def test_open(self):
        TestVirtualFileSystem.virtual_filesystem.open('c:\\users\\omrib\\desktop\\test.sample')
        _, files = TestVirtualFileSystem.virtual_filesystem.listdir('c:\\users\\omrib\\desktop')
        self.assertTrue(any([fname == 'test.sample' for fname, size in files]))

    def test_read_write(self):
        file_ = TestVirtualFileSystem.virtual_filesystem.open('c:\\calc.exe')
        file_.write(b'hello world!')
        self.assertEqual(file_.read(), b'hello world!')

    def test_flush(self):
        file_ = TestVirtualFileSystem.virtual_filesystem.open('C:\\Users\\omrib\\Desktop\\test.exe')
        file_.write(b'hello world!')
        file_.close()
        with open(file_.physical_path, 'rb') as fh:
            self.assertEqual(fh.read(), b'hello world!')

    def test_open_case_insensitive(self):
        file_ = TestVirtualFileSystem.virtual_filesystem.open('C:\\wInDoWs\\sYsTeM32\\CaLc.eXe')
        self.assertIsInstance(file_, stage_props.filesystem.VirtualFile)
