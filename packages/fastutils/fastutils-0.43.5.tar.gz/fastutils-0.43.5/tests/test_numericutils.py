#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import unittest
from fastutils.numericutils import binary_decompose
from fastutils.numericutils import decimal_change_base
from fastutils.numericutils import get_float_part
from fastutils.numericutils import float_split

class TestNumericUtils(unittest.TestCase):
    def test01(self):
        assert binary_decompose(0) == set([])
        assert binary_decompose(1) == set([1])
        assert binary_decompose(2) == set([2])
        assert binary_decompose(3) == set([1, 2])
        assert binary_decompose(4) == set([4])
        assert binary_decompose(5) == set([1, 4])
        assert binary_decompose(6) == set([2, 4])
        assert binary_decompose(7) == set([1, 2, 4])
        assert binary_decompose(8) == set([8])
    
    def test02(self):
        assert decimal_change_base(0, 10) == "0"
        assert decimal_change_base(1, 10) == "1"
        assert decimal_change_base(2, 10) == "2"
        assert decimal_change_base(3, 10) == "3"
        assert decimal_change_base(4, 10) == "4"
        assert decimal_change_base(5, 10) == "5"
        assert decimal_change_base(6, 10) == "6"
        assert decimal_change_base(7, 10) == "7"
        assert decimal_change_base(8, 10) == "8"
        assert decimal_change_base(9, 10) == "9"
        assert decimal_change_base(10, 10) == "10"
        assert decimal_change_base(11, 10) == "11"


    def test03(self):
        assert decimal_change_base(0, 2) == "0"
        assert decimal_change_base(1, 2) == "1"
        assert decimal_change_base(2, 2) == "10"
        assert decimal_change_base(3, 2) == "11"
        assert decimal_change_base(4, 2) == "100"
        assert decimal_change_base(5, 2) == "101"
        assert decimal_change_base(6, 2) == "110"
        assert decimal_change_base(7, 2) == "111"
        assert decimal_change_base(8, 2) == "1000"
        assert decimal_change_base(9, 2) == "1001"
        assert decimal_change_base(10, 2) == "1010"
        assert decimal_change_base(11, 2) == "1011"

    def test04(self):
        assert decimal_change_base(0, 16) == "0"
        assert decimal_change_base(1, 16) == "1"
        assert decimal_change_base(2, 16) == "2"
        assert decimal_change_base(3, 16) == "3"
        assert decimal_change_base(4, 16) == "4"
        assert decimal_change_base(5, 16) == "5"
        assert decimal_change_base(6, 16) == "6"
        assert decimal_change_base(7, 16) == "7"
        assert decimal_change_base(8, 16) == "8"
        assert decimal_change_base(9, 16) == "9"
        assert decimal_change_base(10, 16) == "a"
        assert decimal_change_base(11, 16) == "b"
        assert decimal_change_base(12, 16) == "c"
        assert decimal_change_base(13, 16) == "d"
        assert decimal_change_base(14, 16) == "e"
        assert decimal_change_base(15, 16) == "f"
        assert decimal_change_base(16, 16) == "10"

    def test05(self):
        assert get_float_part(0) == 0
        assert get_float_part(1) == 0
        assert get_float_part(-0) == 0
        assert get_float_part(-1) == 0
        assert get_float_part(1.0) == 0
        assert get_float_part(1.1) == 1000000
        assert get_float_part(1.12) == 1200000
        assert get_float_part(1.123) == 1230000
        assert get_float_part(0.0) == 0
        assert get_float_part(0.1) == 1000000
        assert get_float_part(0.12) == 1200000
        assert get_float_part(0.123) == 1230000
        assert get_float_part(-1.0) == 0
        assert get_float_part(-1.1) == 1000000
        assert get_float_part(-1.12) == 1200000
        assert get_float_part(-1.123) == 1230000
        assert get_float_part(-0.0) == 0
        assert get_float_part(-0.12) == 1200000
        assert get_float_part(-0.123) == 1230000
        assert get_float_part(-0.1) == 1000000
        assert get_float_part(-0.01) == 100000
        assert get_float_part(-0.001) == 10000
        assert get_float_part(-0.0001) == 1000
        assert get_float_part(-0.00001) == 100
        assert get_float_part(-0.000001) == 10
        assert get_float_part(-0.0000001) == 1
        assert get_float_part(-0.00000001, 9) == 10


    def test06(self):
        assert float_split(0) == (1, 0, 0)
        assert float_split(1) == (1, 1, 0)
        assert float_split(-0) == (1, 0, 0)
        assert float_split(-1) == (-1, 1, 0)
        assert float_split(1.0) == (1, 1, 0)
        assert float_split(1.1) == (1, 1, 1000000)
        assert float_split(1.12) == (1, 1, 1200000)
        assert float_split(1.123) == (1, 1, 1230000)
        assert float_split(0.0) == (1, 0, 0)
        assert float_split(0.1) == (1, 0, 1000000)
        assert float_split(0.12) == (1, 0, 1200000)
        assert float_split(0.123) == (1, 0, 1230000)
        assert float_split(-1.0) == (-1, 1, 0)
        assert float_split(-1.1) == (-1, 1, 1000000)
        assert float_split(-1.12) == (-1, 1, 1200000)
        assert float_split(-1.123) == (-1, 1, 1230000)
        assert float_split(-0.0) == (1, 0, 0)
        assert float_split(-0.1) == (-1, 0, 1000000)
        assert float_split(-0.12) == (-1, 0, 1200000)
        assert float_split(-0.123) == (-1, 0, 1230000)
        assert float_split(-0.01) == (-1, 0, 100000)
        assert float_split(-0.12345678) == (-1, 0, 1234567)

if __name__ == "__main__":
    unittest.main()
