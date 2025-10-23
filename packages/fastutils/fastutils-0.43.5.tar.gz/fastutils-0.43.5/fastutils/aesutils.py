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
    "AES_BLOCK_SIZE",
    "get_raw_aes_key",
    "get_mysql_aes_key",
    "get_sha1prng_key",
    "get_md5_key",
    "padding_ansix923",
    "remove_padding_ansix923",
    "padding_iso10126",
    "remove_padding_iso10126",
    "padding_pkcs5",
    "remove_padding_pkcs5",
    "get_padding_remove_method",
    "encrypt",
    "decrypt",
    "encrypt_and_base64encode",
    "decrypt_and_base64decode",
    "encrypt_and_safeb64encode",
    "decrypt_and_safeb64decode",
    "encrypt_and_hexlify",
    "decrypt_and_unhexlify",
    "get_aes_mode",
]

import os
import hashlib
import binascii

from Crypto.Cipher import AES
from zenutils import strutils
from zenutils import listutils
from zenutils import base64utils
from zenutils import sixutils

AES_BLOCK_SIZE = AES.block_size


def get_raw_aes_key(key):
    return sixutils.BYTES(key)[:16]


def get_mysql_aes_key(key):
    final_key = bytearray(16)
    for i, c in enumerate(key):
        final_key[i % 16] ^= ord(c)
    return bytes(final_key)


def get_sha1prng_key(key):
    """
    encrypt key with SHA1PRNG
    same as java AES crypto key generator SHA1PRNG
    """
    key = sixutils.BYTES(key)
    signature = hashlib.sha1(key).digest()
    signature = hashlib.sha1(signature).digest()
    return signature[:16]


def get_md5_key(key):
    key = sixutils.BYTES(key)
    signature = hashlib.md5(key).digest()
    return signature


def padding_ansix923(value):
    padsize = AES.block_size - len(value) % AES.block_size
    return (
        value
        + listutils.int_list_to_bytes([0] * (padsize - 1))
        + listutils.int_list_to_bytes([padsize])
    )


def remove_padding_ansix923(value):
    padsize = strutils.char_force_to_int(value[-1])
    return value[: -1 * padsize]


def padding_iso10126(value):
    padsize = AES.block_size - len(value) % AES.block_size
    return value + os.urandom(padsize - 1) + listutils.int_list_to_bytes([padsize])


def remove_padding_iso10126(value):
    padsize = strutils.char_force_to_int(value[-1])
    return value[: -1 * padsize]


def padding_pkcs5(value):
    padsize = AES.block_size - len(value) % AES.block_size
    value = value + listutils.int_list_to_bytes([padsize] * padsize)
    return value


def remove_padding_pkcs5(value):
    padsize = strutils.char_force_to_int(value[len(value) - 1])
    return value[: -1 * padsize]


def get_padding_remove_method(padding):
    if padding == padding_pkcs5:
        return remove_padding_pkcs5
    elif padding == padding_ansix923:
        return remove_padding_ansix923
    elif padding == padding_iso10126:
        return remove_padding_iso10126
    else:
        raise RuntimeError(
            "Padding method {} have NOT define a remove method...".format(str(padding))
        )


def encrypt(
    data,
    password,
    padding=padding_pkcs5,
    key=get_sha1prng_key,
    mode=AES.MODE_ECB,
    **kwargs
):
    """AES encrypt with AES/ECB/Pkcs5padding/SHA1PRNG options"""
    if padding:
        data = padding(data)
    if key:
        password = key(password)
    cipher = AES.new(password, mode, **kwargs)
    data_encrypted = cipher.encrypt(data)
    return data_encrypted


def decrypt(
    data_encrypted,
    password,
    padding=padding_pkcs5,
    key=get_sha1prng_key,
    mode=AES.MODE_ECB,
    **kwargs
):
    """AES decrypt with AES/ECB/Pkcs5padding/SHA1PRNG options"""
    if key:
        password = key(password)
    cipher = AES.new(password, mode, **kwargs)
    data_padded = cipher.decrypt(data_encrypted)
    if padding:
        padding_remove_method = get_padding_remove_method(padding)
        data = padding_remove_method(data_padded)
    return data


def encrypt_and_base64encode(data, password, **kwargs):
    data = sixutils.BYTES(data)
    data_encrypted = encrypt(data, password, **kwargs)
    data_base64_encoded = base64utils.encodebytes(data_encrypted)
    return strutils.join_lines(data_base64_encoded).decode()


def decrypt_and_base64decode(text, password, **kwargs):
    text = sixutils.BYTES(text)
    data_encrypted = base64utils.decodebytes(text)
    data = decrypt(data_encrypted, password, **kwargs)
    return data


def encrypt_and_safeb64encode(data, password, **kwargs):
    data = sixutils.BYTES(data)
    data_encrypted = encrypt(data, password, **kwargs)
    data_safeb64_encoded = base64utils.urlsafe_b64encode(data_encrypted)
    return strutils.join_lines(data_safeb64_encoded).decode()


def decrypt_and_safeb64decode(text, password, **kwargs):
    text = sixutils.BYTES(text)
    data_encrypted = base64utils.urlsafe_b64decode(text)
    data = decrypt(data_encrypted, password, **kwargs)
    return data


def encrypt_and_hexlify(data, password, **kwargs):
    data = sixutils.BYTES(data)
    data_encrypted = encrypt(data, password, **kwargs)
    return binascii.hexlify(data_encrypted).decode()


def decrypt_and_unhexlify(text, password, **kwargs):
    text = sixutils.BYTES(text)
    data_encrypted = binascii.unhexlify(text)
    data = decrypt(data_encrypted, password, **kwargs)
    return data


def get_aes_mode(mode):
    return getattr(AES, "MODE_{}".format(mode.upper()))
