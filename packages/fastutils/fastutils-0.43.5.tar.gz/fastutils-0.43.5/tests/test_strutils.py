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

"""
String operate functions.

"""
import os
import binascii
import unittest
import random
import string
import uuid
from fastutils import strutils
from zenutils import base64utils
from zenutils import sixutils


class TestStrUtils(unittest.TestCase):
    def test01(self):
        text = "1,2.3,4.5"
        values = strutils.split(text, [",", "."])
        assert values == ["1", "2", "3", "4", "5"]

    def test02(self):
        text = "1,  2 .  3 , 4 . 5 "
        values = strutils.split(text, [",", "."], strip=True)
        assert values == ["1", "2", "3", "4", "5"]

    def test03(self):
        assert strutils.str_composed_by("abc", "abc") is True
        assert strutils.str_composed_by("abcd", "abc") is False
        assert strutils.str_composed_by("a", "") is False
        assert strutils.str_composed_by("aaa", "a") is True
        assert strutils.str_composed_by("aaa", "b") is False
        assert strutils.str_composed_by("ab", "abc") is True

    def test04(self):
        assert strutils.is_hex_digits("") is False
        assert strutils.is_hex_digits("0") is True
        assert strutils.is_hex_digits("9") is True
        assert strutils.is_hex_digits("a") is True
        assert strutils.is_hex_digits("f") is True
        assert strutils.is_hex_digits("g") is False
        assert strutils.is_hex_digits("0123456789abcdefABCDEF") is True

    def test05(self):
        assert strutils.join_lines("") == ""
        assert strutils.join_lines("a") == "a"
        assert strutils.join_lines("a\n") == "a"
        assert strutils.join_lines("a\nb") == "ab"
        assert strutils.join_lines("a\nb\n") == "ab"
        assert strutils.join_lines("a") == "a"
        assert strutils.join_lines("a\r") == "a"
        assert strutils.join_lines("a\rb") == "ab"
        assert strutils.join_lines("a\rb\r") == "ab"
        assert strutils.join_lines("a") == "a"
        assert strutils.join_lines("a\r\n") == "a"
        assert strutils.join_lines("a\r\nb") == "ab"
        assert strutils.join_lines("a\r\nb\r\n") == "ab"
        assert strutils.join_lines("a\rb\nc\r\n") == "abc"

    def test06(self):
        assert strutils.is_urlsafeb64_decodable("") is False
        assert strutils.is_urlsafeb64_decodable("a") is False
        assert strutils.is_urlsafeb64_decodable("ab") is False
        assert strutils.is_urlsafeb64_decodable("abc") is False
        assert strutils.is_urlsafeb64_decodable("abcde") is False
        assert strutils.is_urlsafeb64_decodable("abcdef") is False
        assert strutils.is_urlsafeb64_decodable("abcdefg") is False
        assert strutils.is_urlsafeb64_decodable("abcdefgh") is True
        assert strutils.is_urlsafeb64_decodable("abcdefghi") is False
        text = base64utils.urlsafe_b64encode(os.urandom(16)).decode()
        assert strutils.is_urlsafeb64_decodable(text) is True

    def test07(self):
        assert strutils.is_base64_decodable("") is False
        assert strutils.is_base64_decodable(" ") is False
        assert strutils.is_base64_decodable("a") is False
        assert strutils.is_base64_decodable("a    ") is False
        assert strutils.is_base64_decodable("ab") is False
        assert strutils.is_base64_decodable("ab    ") is False
        assert strutils.is_base64_decodable("abc") is False
        assert strutils.is_base64_decodable("abcd") is True
        assert strutils.is_base64_decodable("abcd  ") is True
        assert strutils.is_base64_decodable("abcde") is False
        assert strutils.is_base64_decodable("abcdef") is False
        assert strutils.is_base64_decodable("abcdefg") is False
        assert strutils.is_base64_decodable("abcdefgh") is True
        assert strutils.is_base64_decodable("abcdefghi") is False
        text = base64utils.encodebytes(os.urandom(4096)).decode()
        assert strutils.is_base64_decodable(text) is True

    def test08(self):
        assert strutils.is_unhexlifiable("") is False
        assert strutils.is_unhexlifiable("a") is False
        assert strutils.is_unhexlifiable("ab") is True
        assert strutils.is_unhexlifiable("abc") is False
        assert strutils.is_unhexlifiable("abcd") is True
        assert strutils.is_unhexlifiable("abcde") is False
        assert strutils.is_unhexlifiable("abcdef") is True
        assert strutils.is_unhexlifiable("abcdefg") is False
        assert strutils.is_unhexlifiable("abcdefgh") is False
        assert strutils.is_unhexlifiable("abcdefghi") is False
        text = binascii.hexlify(os.urandom(4096)).decode()
        assert strutils.is_unhexlifiable(text) is True

    def test09(self):
        assert strutils.split("", ",") == []
        assert strutils.split("a", ",") == ["a"]
        assert strutils.split("a,b", ",") == ["a", "b"]
        assert strutils.split("a,b,", ",") == ["a", "b", ""]

    def test10(self):
        assert strutils.text_display_length("") == 0
        assert strutils.text_display_length("a") == 1
        assert strutils.text_display_length("测") == 2
        assert strutils.text_display_length("测试") == 4
        assert strutils.text_display_length("测试", unicode_display_length=3) == 6
        assert strutils.text_display_length("a测试") == 5
        assert strutils.text_display_length("ab测试") == 6
        assert strutils.text_display_length("ab测试a") == 7
        assert strutils.text_display_length("ab测试ab") == 8

    def test11(self):
        assert strutils.text_display_shorten("", 5) == sixutils.TEXT("")
        assert strutils.text_display_shorten("a", 5) == sixutils.TEXT("a")
        assert strutils.text_display_shorten("ab", 5) == sixutils.TEXT("ab")
        assert strutils.text_display_shorten("abc", 5) == sixutils.TEXT("abc")
        assert strutils.text_display_shorten("abcd", 5) == sixutils.TEXT("abcd")
        assert strutils.text_display_shorten("abcde", 5) == sixutils.TEXT("abcde")
        assert strutils.text_display_shorten("abcdef", 5) == sixutils.TEXT("ab...")
        assert strutils.text_display_shorten("abcdefg", 5) == sixutils.TEXT("ab...")
        assert strutils.text_display_shorten("abcdefgh", 5) == sixutils.TEXT("ab...")
        assert strutils.text_display_shorten("测", 5) == sixutils.TEXT("测")
        assert strutils.text_display_shorten("测测", 5) == sixutils.TEXT("测测")
        assert strutils.text_display_shorten("测测测", 5) == sixutils.TEXT("测...")
        assert strutils.text_display_shorten("测测测测", 5) == sixutils.TEXT("测...")
        assert strutils.text_display_shorten("测测测测测", 5) == sixutils.TEXT("测...")
        assert strutils.text_display_shorten("a测", 5) == sixutils.TEXT("a测")
        assert strutils.text_display_shorten("a测测", 5) == sixutils.TEXT("a测测")
        assert strutils.text_display_shorten("a测测测", 5) == sixutils.TEXT("a...")
        assert strutils.text_display_shorten("a测测测测", 5) == sixutils.TEXT("a...")
        assert strutils.text_display_shorten("a测测测测测", 5) == sixutils.TEXT("a...")

    def test12(self):
        assert strutils.wholestrip("a b") == "ab"
        assert strutils.wholestrip(" a b ") == "ab"

    def test13(self):
        s1 = os.urandom(random.randint(0, 1024))
        s21 = binascii.hexlify(s1).decode()
        s22 = base64utils.encodebytes(s1).decode()
        s23 = base64utils.urlsafe_b64encode(s1).decode()
        s24 = s1
        s31 = strutils.smart_get_binary_data(s21)
        s32 = strutils.smart_get_binary_data(s22)
        s33 = strutils.smart_get_binary_data(s23)
        s34 = strutils.smart_get_binary_data(s24)
        assert s1 == s31 == s32 == s33 == s34

    def test14(self):
        assert strutils.is_chinese_character("是") is True
        assert strutils.is_chinese_character("1") is False

    def test15(self):
        for length in range(1024):
            a = os.urandom(length)
            b = strutils.binarify(a)
            c = strutils.unbinarify(b)
            assert a == c

    def test16(self):
        assert strutils.ints2bytes([]) == b""
        assert strutils.ints2bytes([ord("a"), ord("b"), ord("c")]) == b"abc"
        assert strutils.ints2bytes([0, 1, 2, 255]) == b"\x00\x01\x02\xff"
        assert (
            strutils.ints2bytes([256, 257, 65534, 65535, 65536])
            == b"\x01\x00\x01\x01\xff\xfe\xff\xff\x01\x00\x00"
        )

    def test17(self):
        assert strutils.force_numberic(1) == 1
        assert strutils.force_numberic(1.2) == 1.2
        assert strutils.force_numberic("1") == 1
        assert strutils.force_numberic("1.2") == 1.2

    def test18(self):
        assert strutils.force_float(1) == 1.0
        assert strutils.force_float(1.2) == 1.2
        assert strutils.force_float("1") == 1.0
        assert strutils.force_float("1.2") == 1.2

    def test19(self):
        assert strutils.char_force_to_int(None) is None
        assert sixutils.BYTES(None) is None
        assert sixutils.TEXT(None) is None
        assert strutils.force_int(None) is None

    def test20(self):
        t1 = "测试"
        assert sixutils.force_text(t1.encode("gbk"), ["utf-8", "gb18030"]) == t1

    def test21(self):
        assert len(strutils.substrings("")) == 0
        assert len(strutils.substrings("a")) == 1
        assert len(strutils.substrings("ab")) == 3
        assert len(strutils.substrings("aa")) == 2
        assert len(strutils.substrings("abc")) == len(
            ["a", "b", "c", "ab", "bc", "abc"]
        )
        assert len(strutils.substrings("abc", 2)) == len(["ab", "bc"])
        assert len(strutils.substrings("abc", 3)) == 1
        assert len(strutils.substrings("abc", 1)) == 3
        assert len(strutils.substrings("abc", [1, 2])) == 5

    def test22(self):
        assert len(strutils.combinations("a", 2)) == 1**2
        assert len(strutils.combinations("ab", 2)) == 2**2
        assert len(strutils.combinations("abc", 2)) == 3**2
        assert len(strutils.combinations("a", 3)) == 1**3
        assert len(strutils.combinations("ab", 3)) == 2**3
        assert len(strutils.combinations(string.digits, 2)) == 10**2
        assert len(strutils.combinations(string.digits, 3)) == 10**3
        assert len(strutils.combinations(string.ascii_lowercase, 3)) == 26**3
        assert len(strutils.combinations(["a", "cd"], 3)) == 8
        assert len(strutils.combinations(["ab", "cd"], 3)) == 8
        assert len(strutils.combinations(["aa", "bb"], 3)) == 6
        assert len(strutils.combinations(["abc"], 1)) == 3
        assert len(strutils.combinations(["abc"], 2)) == 3
        assert len(strutils.combinations(["abc"], 3)) == 3
        assert len(strutils.combinations(["abc"], 4)) == 3
        assert len(strutils.combinations(["abc"], 5)) == 3
        assert len(strutils.combinations(["abc"], 6)) == 3
        assert len(strutils.combinations(["abc"], 7)) == 3
        assert len(strutils.combinations(["abc"], 8)) == 3

    def test23(self):
        assert strutils.captital_number(0) == "零圆"
        assert strutils.captital_number(1) == "壹圆"
        assert strutils.captital_number(10) == "壹拾圆"
        assert strutils.captital_number(12) == "壹拾贰圆"
        assert strutils.captital_number(100) == "壹佰圆"
        assert strutils.captital_number(102) == "壹佰零贰圆"
        assert strutils.captital_number(123) == "壹佰贰拾叁圆"
        assert strutils.captital_number(1000) == "壹仟圆"
        assert strutils.captital_number(1002) == "壹仟零贰圆"
        assert strutils.captital_number(1023) == "壹仟零贰拾叁圆"
        assert strutils.captital_number(1234) == "壹仟贰佰叁拾肆圆"
        assert strutils.captital_number(10000) == "壹万圆"
        assert strutils.captital_number(10002) == "壹万零贰圆"
        assert strutils.captital_number(10023) == "壹万零贰拾叁圆"
        assert strutils.captital_number(10234) == "壹万零贰佰叁拾肆圆"
        assert strutils.captital_number(10204) == "壹万零贰佰零肆圆"
        assert strutils.captital_number(12345) == "壹万贰仟叁佰肆拾伍圆"
        assert strutils.captital_number(12005) == "壹万贰仟零伍圆"
        assert strutils.captital_number(112005) == "壹拾壹万贰仟零伍圆"
        assert strutils.captital_number(10112005) == "壹仟零壹拾壹万贰仟零伍圆"
        assert strutils.captital_number(100000000) == "壹亿圆"
        assert strutils.captital_number(100000002) == "壹亿零贰圆"
        assert strutils.captital_number(100030000) == "壹亿零叁万圆"
        assert strutils.captital_number(100003000) == "壹亿零叁仟圆"
        assert strutils.captital_number(123100003000) == "壹仟贰佰叁拾壹亿零叁仟圆"
        assert strutils.captital_number(1234567890123) == "壹万贰仟叁佰肆拾伍亿陆仟柒佰捌拾玖万零壹佰贰拾叁圆"
        assert strutils.captital_number(1234567) == "壹佰贰拾叁万肆仟伍佰陆拾柒圆"

    def test24(self):
        assert strutils.captital_number(0.1) == "零圆壹角"
        assert strutils.captital_number(0.01) == "零圆壹分"
        assert strutils.captital_number(0.001) == "零圆壹厘"
        assert strutils.captital_number(0.0001) == "零圆壹毫"
        assert strutils.captital_number(0.00001) == "零圆壹丝"
        assert strutils.captital_number(0.000001) == "零圆壹忽"
        assert strutils.captital_number(0.0000001) == "零圆壹微"
        assert strutils.captital_number(0.00000001) == "零圆"
        assert strutils.captital_number(0.12) == "零圆壹角贰分"
        assert strutils.captital_number(0.123) == "零圆壹角贰分叁厘"
        assert strutils.captital_number(0.1234) == "零圆壹角贰分叁厘肆毫"
        assert strutils.captital_number(0.12345) == "零圆壹角贰分叁厘肆毫伍丝"
        assert strutils.captital_number(0.123456) == "零圆壹角贰分叁厘肆毫伍丝陆忽"
        assert strutils.captital_number(0.1234567) == "零圆壹角贰分叁厘肆毫伍丝陆忽柒微"
        assert strutils.captital_number(0.12345678) == "零圆壹角贰分叁厘肆毫伍丝陆忽柒微"

    def test25(self):
        assert strutils.camel("hello") == "Hello"
        assert strutils.camel("hello world") == "Hello World"
        assert strutils.camel(" hello ") == " Hello "
        assert strutils.camel("hello  world") == "Hello  World"
        assert strutils.camel("hello-world") == "Hello-World"
        assert strutils.camel("hello_world") == "Hello_World"

        assert strutils.camel("hello", clean=True) == "Hello"
        assert strutils.camel("hello world", clean=True) == "HelloWorld"
        assert strutils.camel(" hello ", clean=True) == "Hello"
        assert strutils.camel("hello  world", clean=True) == "HelloWorld"
        assert strutils.camel("hello-world", clean=True) == "HelloWorld"
        assert strutils.camel("hello_world", clean=True) == "HelloWorld"

    def test26(self):
        assert (
            strutils.format_with_mapping("{}{}", strutils.none_to_empty_string, 1, None)
            == "1"
        )
        assert (
            strutils.format_with_mapping(
                "{a}{b}", strutils.none_to_empty_string, a=1, b=None
            )
            == "1"
        )
        assert (
            strutils.format_with_mapping(
                "{}{a}{}{b}", strutils.none_to_empty_string, 1, None, a=3, b=None
            )
            == "13"
        )
        assert (
            strutils.format_with_mapping("{:d}:{:}", strutils.no_mapping, 1, None)
            == "1:None"
        )

    def test27(self):
        assert strutils.unquote('''"hello"''') == "hello"
        assert strutils.unquote('"""hello"""') == "hello"
        assert strutils.unquote("“hello”") == "hello"
        assert strutils.unquote("‘hello’") == "hello"

    def test28(self):
        assert strutils.is_uuid(uuid.uuid4())
        assert strutils.is_uuid(uuid.uuid4().hex)
        assert strutils.is_uuid(uuid.uuid4().bytes)
        assert strutils.is_uuid("abc") == False
        assert strutils.is_uuid("abcdefghijklmnopqrstuvwxyz") == False
        assert strutils.is_uuid("{12345678-1234-5678-1234-567812345678}")
        assert strutils.is_uuid("12345678123456781234567812345678")
        assert strutils.is_uuid("12345678-1234-5678-1234-567812345678")

    def test29(self):
        assert (
            strutils.camel("hello world", clean=True, lower_first=True) == "helloWorld"
        )

    def test30(self):
        assert strutils.stringlist_append("a b c", "a", separator=" ") == "a b c a"
        assert strutils.stringlist_append("a,b,c", "a") == "a,b,c,a"
        assert (
            strutils.stringlist_append("a,b,c", "a", allow_duplicate=False) == "a,b,c"
        )

    def test31(self):
        assert strutils.is_urlsafeb64_decodable("abcd") is True

    def test32(self):
        assert strutils.html_element_css_append("a b c", "a") == "a b c"
        assert strutils.html_element_css_append("a b c", "d") == "a b c d"

    def test33(self):
        assert strutils.remove_prefix("helloworld", "hello") == "world"
        assert strutils.remove_prefix("helloworld", "hi") == "helloworld"
        assert strutils.remove_prefix("helloworld", "") == "helloworld"

    def test34(self):
        assert strutils.remove_suffix("helloworld", "world") == "hello"
        assert strutils.remove_suffix("helloworld", "word") == "helloworld"
        assert strutils.remove_suffix("helloworld", "") == "helloworld"

    def test35(self):
        assert strutils.split2("hello world") == ["hello", "world"]
        assert strutils.split2("hello world !") == ["hello", "world !"]
        assert strutils.split2("1,2,3", ",") == ["1", "2,3"]

    def test36(self):
        assert strutils.is_uuid("90a0332d-7f06-gace-a1e2-3c27e634c17f") == False
        assert (
            strutils.is_uuid(
                "90a0332d-7f06-gace-a1e2-3c27e634c17f", allow_bad_characters=True
            )
            == True
        )
        assert (
            strutils.is_uuid(
                "90a0332d-7f06-gace-a1e2-3c27e634c17f-x", allow_bad_characters=True
            )
            == False
        )
        assert (
            strutils.is_uuid("123412341234123412341234", allow_bad_characters=True)
            == False
        )

    def test37(self):
        assert strutils.chunk("", 2) == []
        assert strutils.chunk("1", 2) == ["1"]
        assert strutils.chunk("12", 2) == ["12"]
        assert strutils.chunk("123", 2) == ["12", "3"]
        assert strutils.chunk("1234", 2) == ["12", "34"]
        assert strutils.chunk("", 1) == []
        assert strutils.chunk("1", 1) == ["1"]
        assert strutils.chunk("12", 1) == ["1", "2"]
        assert strutils.chunk("123", 1) == ["1", "2", "3"]

    def test38(self):
        assert strutils.get_all_substrings("a") == set(["a"])
        assert strutils.get_all_substrings("ab") == set(["a", "b", "ab"])
        assert strutils.get_all_substrings("abc") == set(
            ["a", "b", "c", "ab", "bc", "abc"]
        )
        assert strutils.get_all_substrings("abcd") == set(
            ["a", "b", "c", "d", "ab", "bc", "cd", "abc", "bcd", "abcd"]
        )

        assert strutils.get_all_substrings("aa") == set(["a", "aa"])
        assert strutils.get_all_substrings("aab") == set(["a", "b", "aa", "ab", "aab"])
        assert strutils.get_all_substrings("aba") == set(["a", "b", "ab", "ba", "aba"])
        assert strutils.get_all_substrings("abab") == set(
            ["a", "b", "ab", "ba", "aba", "bab", "abab"]
        )

    def test39(self):
        assert strutils.get_all_substrings(b"a") == set([b"a"])
        assert strutils.get_all_substrings(b"ab") == set([b"a", b"b", b"ab"])
        assert strutils.get_all_substrings(b"abc") == set(
            [b"a", b"b", b"c", b"ab", b"bc", b"abc"]
        )
        assert strutils.get_all_substrings(b"abcd") == set(
            [b"a", b"b", b"c", b"d", b"ab", b"bc", b"cd", b"abc", b"bcd", b"abcd"]
        )

        assert strutils.get_all_substrings(b"aa") == set([b"a", b"aa"])
        assert strutils.get_all_substrings(b"aab") == set(
            [b"a", b"b", b"aa", b"ab", b"aab"]
        )
        assert strutils.get_all_substrings(b"aba") == set(
            [b"a", b"b", b"ab", b"ba", b"aba"]
        )
        assert strutils.get_all_substrings(b"abab") == set(
            [b"a", b"b", b"ab", b"ba", b"aba", b"bab", b"abab"]
        )


if __name__ == "__main__":
    unittest.main()
