#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement


import time
import json
import uuid
import os

import unittest

from fastutils import fsutils

class TestFsUtils(unittest.TestCase):

    def test01(self):
        folder_name = str(uuid.uuid4())
        assert fsutils.mkdir(folder_name)
        assert fsutils.mkdir(folder_name)
        assert fsutils.rm(folder_name)
        assert fsutils.rm(folder_name)

    def test02(self):
        filename = str(uuid.uuid4())
        content = str(uuid.uuid4())
        fsutils.write(filename, content)
        assert fsutils.readfile(filename) == content
        assert fsutils.rm(filename)

    def test03(self):
        filename1 = str(uuid.uuid4())
        content1 = str(uuid.uuid4())
        content2 = str(uuid.uuid4())
        fsutils.write(filename1, content1)
        file_replaced, file_failed = fsutils.file_content_replace(filename1, content1, content2)
        assert os.path.abspath(file_replaced[0]) == os.path.abspath(filename1)
        assert fsutils.readfile(filename1) == content2
        assert fsutils.rm(filename1)

    def test04(self):
        filename = str(uuid.uuid4())
        info1 = fsutils.touch(filename)
        time.sleep(1)
        info2 = fsutils.touch(filename)
        fsutils.rm(filename)
        time.sleep(1)

        assert not os.path.exists(filename)
        assert info1
        assert info2
        assert info2.st_mtime > info1.st_mtime

    def test05(self):
        for i in range(5):
            filenames = []
            for j in range(5):
                filenames.append(str(uuid.uuid4()))
            fsutils.touch(filenames[i])
            filename = fsutils.first_exists_file(*filenames)
            assert filename == os.path.abspath(filenames[i])
            for j in range(5):
                fsutils.rm(filenames[j])

    def test06(self):
        filepath = None
        workspace = None
        with fsutils.TemporaryFile() as fileinstance:
            filepath = fileinstance.filepath
            workspace = fileinstance.workspace
            assert os.path.exists(filepath)
            assert os.path.exists(workspace)
        assert os.path.exists(filepath) == False

    def test07(self):
        default = "file not exists..."
        filename = str(uuid.uuid4())
        result = fsutils.readfile(filename, default=default)
        assert result == default

    def test08(self):
        content = os.urandom(1024)
        with fsutils.TemporaryFile(content=content) as tmpfile:
            tmpfile.open("rb")
            assert tmpfile.read() == content

if __name__ == "__main__":
    unittest.main()

