#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import unittest
from fastutils.cacheutils import get_cached_value

_test_cacheutils_counter = 0

class Object(object):
    pass

class TestCacheUtils(unittest.TestCase):

    def test01(self):
        a = Object()
        def hi():
            return "hi"
        assert get_cached_value(a, "hi", hi) == "hi"

    def test02(self):
        global _test_cacheutils_counter
        _test_cacheutils_counter = 0
        a = Object()
        def counter():
            global _test_cacheutils_counter
            _test_cacheutils_counter += 1
            return _test_cacheutils_counter
        assert get_cached_value(a, "counter", counter) == 1
        assert get_cached_value(a, "counter", counter) == 1

if __name__ == "__main__":
    unittest.main()
