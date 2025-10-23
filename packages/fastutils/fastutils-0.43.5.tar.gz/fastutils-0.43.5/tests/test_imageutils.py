#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import os

import unittest
from PIL import Image
from fastutils.imageutils import get_image_bytes
from fastutils.imageutils import get_base64image
from fastutils.imageutils import parse_base64image
from fastutils.imageutils import resize
from fastutils.imageutils import resize_to_fixed_width
from fastutils.imageutils import resize_to_fixed_height

def get_example_image():
    example_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./test_imageutils.jpeg"))
    return Image.open(example_image_path)

class TestImageUtils(unittest.TestCase):

    def test01(self):
        format = "png"
        image = get_example_image()
        data = get_image_bytes(image, format=format)
        b64image = get_base64image(data, format=format)
        format_new, data_new = parse_base64image(b64image)
        assert format_new == format
        assert data_new == data

    def test02(self):
        image1 = get_example_image()
        width1, height1 = image1.size
        image2 = resize(image1, scale=0.5)
        width2, height2 = image2.size

        assert abs(width2 / width1 - 0.5) < 0.002
        assert abs(height2 / height1 - 0.5) < 0.002

    def test03(self):
        image1 = get_example_image()
        width1, height1 = image1.size

        image2 = resize_to_fixed_width(image1, new_width=400)
        width2, height2 = image2.size

        assert width2 == 400
        assert abs(width1/height1 - width2/height2) < 0.002

    def test04(self):
        image1 = get_example_image()
        width1, height1 = image1.size

        image2 = resize_to_fixed_height(image1, new_height=400)
        width2, height2 = image2.size

        assert height2 == 400
        print(width1/height1, width2/height2)
        assert abs(width1/height1 - width2/height2) < 0.002

if __name__ == "__main__":
    unittest.main()

