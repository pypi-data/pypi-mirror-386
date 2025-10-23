#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import unittest
import json
from fastutils import dictutils

class TestDictUtils(unittest.TestCase):
    def test01(self):
        data1 = {
            "a": {
                "b": {
                    "c": "c",
                }
            }
        }
        data2 = {
            "a": {
                "b": {
                    "d": "d",
                }
            }
        }
        dictutils.deep_merge(data1, data2)
        assert data1["a"]["b"]["c"] == "c"
        assert data1["a"]["b"]["d"] == "d"
    
    def test02(self):
        data1 = {
            "a": "a",
        }
        data2 = {
            "a": [1, 2, 3]
        }
        dictutils.deep_merge(data1, data2)
        assert data1["a"] == [1, 2, 3]

    def test03(self):
        data = {
            "a": {
                "b": {
                    "c": "c",
                }
            }
        }
        assert "b" in dictutils.select(data, "a")
        assert "c" in dictutils.select(data, "a.b")
        assert dictutils.select(data, "a.b.c") == "c"

    def test04(self):
        data = [1, 2, 3]
        assert dictutils.select(data, "0") == 1

    def test05(self):
        data = {
            "a": [{
                "b": {
                    "c": "c"
                }
            }]
        }
        assert dictutils.select(data, "a.0.b.c") == "c"

    def test06(self):
        data = {
            "a": [{
                "b": {
                    "c": "c"
                }
            }]
        }
        assert dictutils.select(data, "a.1") is None

    def test07(self):
        data = {}
        dictutils.update(data, "a.b.c.d", "d")
        assert dictutils.select(data, "a.b.c.d") == "d"

    def test08(self):
        data = {}
        dictutils.update(data, "a.0.c.d", "d")
        assert dictutils.select(data, "a.0.c.d") == "d"

    def test09(self):
        data = {}
        dictutils.update(data, "a.1.c.d", "d")
        assert data["a"][0] is None
        assert dictutils.select(data, "a.1.c.d") == "d"

    def test10(self):
        data = {
            "a": [{
                "c": {
                    "d": "d",
                }
            }]
        }
        dictutils.update(data, "a.0.c.d", "e")
        assert dictutils.select(data, "a.0.c.d") == "e"

    def test11(self):
        data = []
        dictutils.update(data, "5", "e")
        assert dictutils.select(data, "5") == "e"

    def test12(self):
        data = {
            "a": [{
                "b": {
                    "c": "c",
                }
            }]
        }
        dictutils.update(data, "a.0.b.d", "d")
        assert dictutils.select(data, "a.0.b.c") == "c"
        assert dictutils.select(data, "a.0.b.d") == "d"

    def test13(self):
        data1 = {
            "a": None,
            "b": 0,
            "c": False,
            "d": [],
            "e": {},
            "f": "hi",
        }
        data2 = dictutils.ignore_none_item(data1)
        assert "a" not in data2
        assert "b" in data2
        assert "c" in data2
        assert "d" not in data2
        assert "e" not in data2
        assert "f" in data2

    def test14(self):
        data1 = {"a": True, "b": "b", "c": 1234}
        data2 = dictutils.to_object(data1)
        assert data2.a == True
        assert data2.b == "b"
        assert data2.c == 1234

        data3 = {"a": {"a": [1,2,3], "b-c": {"a-a": "a-a"}}}
        data4 = dictutils.to_object(data3)
        assert data4.a.a == [1,2,3]
        assert data4.a["b-c"]["a-a"] == "a-a"

        text4 = json.dumps(data4, sort_keys=True)
        text3 = json.dumps(data3, sort_keys=True)
        assert text3 == text4

    def test15(self):
        data1 = dictutils.to_object({"a": "a", "b": "b"})
        data2 = {"a": "a", "b": "c"}
        assert dictutils.change(data1, data2, "a") == False
        assert dictutils.change(data1, data2, "b") == True
        assert data1.b == "c"
    
    def test16(self):
        data1 = dictutils.to_object({"a": "a", "b": "b"})
        data1["a"] = "b"
        assert data1.a == "b"
        data1.b = "c"
        assert data1["b"] == "c"
        data1.c = "d"
        assert data1["c"] == "d"

    def test17(self):
        data1 = dictutils.to_object({"a": "a", "b": "b"})
        data2 = {"a": "a", "b": "b"}
        assert dictutils.changes(data1, data2, ["a", "b"]) == False

        data3 = dictutils.to_object({"a": "a", "b": "b"})
        data4 = {"a": "a", "b": "c"}
        assert dictutils.changes(data3, data4, ["a", "b"]) == True
        assert data3.b == "c"

    def test18(self):
        data1 = {
            "a": {
                "b": {
                    "c": "a.b.c",
                }
            }
        }
        data2 = dictutils.to_object(data1)
        value = dictutils.select(data2, "a.b.c")
        assert value == "a.b.c"

    def test19(self):
        data1 = {}
        dictutils.update(data1, "a.b.c", "a.b.c")
        assert dictutils.select(data1, "a.b.c") == "a.b.c"

    def test20(self):
        data1 = {}
        data2 = dictutils.to_object(data1)
        dictutils.update(data2, "a.b.c", "a.b.c")
        assert data2.a.b.c == "a.b.c"

    def test21(self):
        data = dictutils.Object()
        data.a = {}
        data['a']['b'] = 'a.b'
        assert data.a.b == 'a.b'

    def test22(self):
        data = dictutils.Object({"a": {"b": "a.b"}})
        assert data.a.b == "a.b"

    def test23(self):
        data1 = {}
        data2 = dictutils.Object()
        data3 = dictutils.update(data1, "a.b.c", "a.b.c")
        data4 = dictutils.update(data2, "a.b.c", "a.b.c")
        assert type(data1) == type(data3)
        assert type(data2) == type(data4)
        assert data1 == data3
        assert data2 == data4

    def test24(self):
        data1 = {"id": 1, "name": "mktg"}
        data2 = dictutils.prefix_key(data1, "department")
        assert data2["departmentId"] == data1["id"]
        assert data2["departmentName"] == data1["name"]

    def test25(self):
        class A(object):
            pass
        data1 = A()
        dictutils.update(data1, "a.b.c.d", "a.b.c.d")
        assert dictutils.select(data1, "a.b.c.d") == "a.b.c.d"

    def test26(self):
        a = {
            "a": "a",
            "b": "b",
            "c": "c",
        }
        b = {
            "a": "a",
            "c": "cc",
            "d": "d",
        }
        create_keys, updated_keys, deleted_keys = dictutils.diff(a, b)
        assert "b" in deleted_keys
        assert "c" in updated_keys
        assert "d" in create_keys

    def test27(self):
        a = dictutils.Object({"a": "a", "b": {"c": "c", "d": [{"e": "e"}]}})
        assert a.a == "a"
        assert a.b.c == "c"
        assert a.b.d[0].e == "e"

    def test28(self):
        a = dictutils.Object()
        b = dictutils.Object()
        b.a = 'a'
        b.b = {
            "c": "c"
        }
        a.update(b)
        assert a.a == "a"
        assert a.b.c == "c"

    def test29(self):
        a = dictutils.Object()
        b = dictutils.Object()
        a.a = 'a'
        b.a = 'b'
        a.update(b)
        b.a = 'c'
        assert a.a == 'b'
        assert b.a == 'c'

    def test30(self):
        a = dictutils.Object()
        a.setdefault('a', 'a')
        assert a.a == 'a'

    def test31(self):
        a = dictutils.Object(a='a')
        assert a.pop('a') == 'a'
        assert a.pop('a', 'b') == 'b'

    def test32(self):
        a = dictutils.Object(a='a')
        a.clear()
        assert not 'a' in a

    def test33(self):
        a = dictutils.Object(a='a')
        b = a.copy()
        assert b.a == 'a'

    def test34(self):
        a = dictutils.Object(a='b')
        k, v = a.popitem()
        assert k == 'a'
        assert v == 'b'
        assert not 'a' in a
        assert hasattr(a, 'a') is False

    def test35(self):
        a = dictutils.Object()
        a.a = [1,2,3, {'a': 'a'}]
        assert a.a[3].a == 'a'

    def test36(self):
        a = dictutils.Object()
        a.a = [1,2,3]
        a.a.append({"a": "a"})
        assert type(a.a[3]) == dict
        a.fix()
        assert a.a[3].a == "a"

        
if __name__ == "__main__":
    unittest.main()
