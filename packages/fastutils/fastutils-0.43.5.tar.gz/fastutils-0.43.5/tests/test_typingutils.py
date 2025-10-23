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

import unittest
import os
import binascii
import typing
import uuid
from fastutils.typingutils import Number
from fastutils.typingutils import smart_cast
from zenutils import base64utils
from zenutils import sixutils


class TestTypingUtils(unittest.TestCase):
    def test01(self):
        assert smart_cast(int, "12") == 12
        assert smart_cast(float, "12.34") == 12.34
        assert smart_cast(bool, "true") == True
        assert smart_cast(sixutils.BYTES_TYPE, "6869") == b"hi"
        assert smart_cast(list, "1,2,3") == ["1", "2", "3"]
        assert smart_cast(typing.List, "[1, 2, 3]") == [1, 2, 3]
        assert smart_cast(dict, """{"a": "a", "b": "b"}""") == {"a": "a", "b": "b"}
        assert smart_cast(typing.Mapping, """{"a": "a", "b": "b"}""") == {
            "a": "a",
            "b": "b",
        }
        assert smart_cast(sixutils.STR_TYPE, b"hello") == "hello"

    def test02(self):
        assert smart_cast(bool, "True") is True
        assert smart_cast(bool, "False") is False
        assert smart_cast(bool, "1") is True
        assert smart_cast(bool, "0") is False
        assert smart_cast(bool, "y") is True
        assert smart_cast(bool, "n") is False
        assert smart_cast(bool, "yes") is True
        assert smart_cast(bool, "no") is False
        assert smart_cast(bool, 1) is True
        assert smart_cast(bool, 0) is False
        assert smart_cast(bool, True) is True
        assert smart_cast(bool, False) is False
        assert smart_cast(bool, 1.1) is True
        assert smart_cast(bool, 0.0) is False

    def test03(self):
        assert smart_cast(int, 1) == 1
        assert smart_cast(int, 0) == 0
        assert smart_cast(int, "1") == 1
        assert smart_cast(int, "0") == 0

    def test04(self):
        assert smart_cast(sixutils.STR_TYPE, "a") == "a"
        assert smart_cast(sixutils.STR_TYPE, "测试") == "测试"
        assert smart_cast(sixutils.STR_TYPE, 1) == "1"
        assert smart_cast(sixutils.STR_TYPE, True) == "True"
        assert smart_cast(sixutils.STR_TYPE, False) == "False"
        assert smart_cast(sixutils.STR_TYPE, "测试".encode("utf-8")) == "测试"
        assert smart_cast(sixutils.STR_TYPE, "测试".encode("gbk")) == "测试"

    def test05(self):
        assert smart_cast(sixutils.BYTES_TYPE, "a") == b"a"
        assert smart_cast(sixutils.BYTES_TYPE, b"a") == b"a"
        assert smart_cast(sixutils.BYTES_TYPE, "测试") == "测试".encode("utf-8")
        assert smart_cast(sixutils.BYTES_TYPE, "YQ==") == b"a"
        assert smart_cast(sixutils.BYTES_TYPE, "YWI=") == b"ab"
        assert smart_cast(sixutils.BYTES_TYPE, "6162") == b"ab"

    def test06(self):
        s = os.urandom(16)
        t1 = binascii.hexlify(s).decode()
        t2 = base64utils.encodebytes(s).decode()
        t3 = base64utils.urlsafe_b64encode(s).decode()
        assert smart_cast(sixutils.BYTES_TYPE, t1) == s
        assert smart_cast(sixutils.BYTES_TYPE, t2) == s
        assert smart_cast(sixutils.BYTES_TYPE, t3) == s

    def test07(self):
        assert smart_cast(dict, {"a": "a"})["a"] == "a"
        assert smart_cast(dict, """{"a": "a"}""")["a"] == "a"
        assert smart_cast(dict, [("a", "a")])["a"] == "a"

    def test08(self):
        assert smart_cast(list, [1, 2, 3])[0] == 1
        assert smart_cast(list, """[1, 2, 3]""")[0] == 1
        assert smart_cast(list, """1 , 2 , 3""")[0] == "1"

    def test09(self):
        assert smart_cast(Number, 1) == 1
        assert smart_cast(Number, 1.0) == 1.0
        assert smart_cast(Number, "1") == 1
        assert smart_cast(Number, "1.0") == 1.0

    def test10(self):
        assert smart_cast(int, "") == None
        assert smart_cast(float, "") == None
        assert smart_cast(list, "") == None
        assert smart_cast(dict, "") == None

    def test11(self):
        data1 = uuid.uuid4()
        assert smart_cast(uuid.UUID, data1) == data1
        assert smart_cast(uuid.UUID, data1.hex) == data1
        assert smart_cast(uuid.UUID, data1.bytes) == data1
        assert smart_cast(uuid.UUID, data1.fields) == data1


if __name__ == "__main__":
    unittest.main()
