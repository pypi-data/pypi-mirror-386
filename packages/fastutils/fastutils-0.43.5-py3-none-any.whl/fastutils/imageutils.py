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
Image operate functions.

Note: Non exact division leads some error in width-and-height ratio.
"""

__all__ = [
    "get_image_bytes",
    "get_base64image",
    "parse_base64image",
    "resize",
    "resize_to_fixed_width",
    "resize_to_fixed_height",
]

from zenutils.strutils import get_image_bytes
from zenutils.strutils import get_base64image
from zenutils.strutils import parse_base64image


def resize(src, scale):
    """Resize PIL image using scale. Non exact division leads some error in width-and-height ratio."""
    src_size = src.size
    dst_size = (int(src_size[0] * scale), int(src_size[1] * scale))
    dst = src.resize(dst_size)
    return dst


def resize_to_fixed_width(src, new_width):
    """Keep image's width-and-height ratio, scale the image to a specified new width. Non exact division leads some error in width-and-height ratio."""
    width, height = src.size
    new_height = int(new_width * height / width)
    dst = src.resize((new_width, new_height))
    return dst


def resize_to_fixed_height(src, new_height):
    """Keep image's width-and-height ratio, scale the image to a specified new height. Non exact division leads some error in width-and-height ratio."""
    width, height = src.size
    new_width = int(new_height * width / height)
    dst = src.resize((new_width, new_height))
    return dst
