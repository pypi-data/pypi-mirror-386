#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import unittest
from fastutils import nameutils



class TestNameUtils(unittest.TestCase):

    def test01(self):
        name = nameutils.get_random_name()
        assert 2 <= len(name) <= 4

    def test02(self):
        assert nameutils.guess_surname("黄某某") == "黄"
        assert nameutils.guess_surname("张某某") == "张"
        assert nameutils.guess_surname("John Smith") == "Smith"
        assert nameutils.guess_surname("Tom") == "Tom"

if __name__ == "__main__":
    unittest.main()
