#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import (
    absolute_import,
    division,
    generators,
    nested_scopes,
    print_function,
    unicode_literals,
    with_statement,
)
import sys

if sys.version_info.major == 3 and sys.version_info.minor == 2:
    import unittest

    class TestPinyinUtils(unittest.TestCase):
        pass

else:
    import string
    import unittest
    from fastutils.pinyinutils import to_pinyin

    class TestPinyinUtils(unittest.TestCase):
        def test01(self):
            assert to_pinyin("测试") == "CeShi"
            assert to_pinyin("测（试）") == "CeShi"
            assert to_pinyin("测 （试）") == "CeShi"
            assert to_pinyin("｛测｝ （试）") == "CeShi"

        def test02(self):
            assert to_pinyin("略") == "Lue"
            assert to_pinyin("绿") == "Lv"
            assert to_pinyin("雨") == "Yu"
            assert to_pinyin("约") == "Yue"

        def test03(self):
            assert to_pinyin("hello world") == "HelloWorld"
            assert (
                to_pinyin("hi123", keep_chars=string.ascii_letters + string.digits)
                == "Hi123"
            )


if __name__ == "__main__":
    unittest.main()
