#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import unittest
import os
import time
import datetime
import uuid
import decimal
from fastutils.jsonutils import simple_json_dumps
from PIL import Image

def get_example_image():
    example_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./test_imageutils.jpeg"))
    return Image.open(example_image_path)


class TestJsonUtils(unittest.TestCase):
    def test01(self):
        data = {
            "t1": datetime.datetime.now(),
            "t2": datetime.date(2019, 12, 7),
            "t3": datetime.time(21, 35, 1),
            "uid": uuid.uuid4(),
            "p1": 3.45,
            "p2": decimal.Decimal(1) / decimal.Decimal(7),
            "p3": (1, 2, 3),
            "p4": [1, 2, 3, 4],
            "r1": os.urandom(1024),
            "e1": RuntimeError("RuntimeError"),
            "e2": ZeroDivisionError("ZeroDivisionError"),
            "e4": Exception("Exception"),
        }
        result = simple_json_dumps(data, indent=4, ensure_ascii=False)
        assert result

    def test02(self):
        im = get_example_image()
        data = {
            "ts": time.time(),
            "image": im,
        }
        result = simple_json_dumps(data)
        assert result

if __name__ == "__main__":
    unittest.main()
