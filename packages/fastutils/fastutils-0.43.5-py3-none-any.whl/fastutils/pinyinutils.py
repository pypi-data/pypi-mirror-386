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

__all__ = [
    "to_pinyin",
]

import string
from pypinyin import lazy_pinyin


def to_pinyin(value, clean=True, keep_chars=string.ascii_letters + string.digits):
    """Turn chinese text to pinyin string.

    Example:

    In [1]: from fastutils import pinyinutils

    In [2]: pinyinutils.to_pinyin('测试')
    Out[2]: 'CeShi'
    """
    from zenutils import listutils
    from zenutils import strutils

    words = lazy_pinyin(value)
    words = listutils.replace(words, {"lve": "lue"})
    title = " ".join([x.capitalize() for x in words])
    result = strutils.camel(title, clean=clean, keep_chars=keep_chars)
    return result
