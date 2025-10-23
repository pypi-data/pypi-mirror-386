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
import json
import base64
import binascii
import random
import string
from fastutils.cipherutils import S12Cipher
from fastutils.cipherutils import RawDataEncoder
from fastutils.cipherutils import HexlifyEncoder
from fastutils.cipherutils import Base64Encoder
from fastutils.cipherutils import SafeBase64Encoder
from fastutils.cipherutils import S12Cipher
from fastutils.cipherutils import AesCipher
from fastutils.cipherutils import IvCipher
from fastutils.cipherutils import IvfCipher
from fastutils.cipherutils import S1Cipher
from fastutils.cipherutils import S2Cipher
from fastutils import cipherutils
from fastutils import rsautils
from fastutils import listutils
from fastutils import randomutils
from zenutils import sixutils
from zenutils import base64utils
from Crypto.Util import Counter


class TestCipherUtils(unittest.TestCase):
    def test01(self):
        password = "".join(
            randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
        )
        cipher = S12Cipher(password=password)
        text1 = (
            "".join(
                randomutils.choices(string.ascii_letters, k=random.randint(0, 1024))
            )
        ).encode()
        data = cipher.encrypt(text1)
        text2 = cipher.decrypt(data)
        assert text1 == text2

    def test02(self):
        password = "".join(
            randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
        )
        cipher = S12Cipher(password=password)
        text1 = "hello"
        text2 = "hello world"
        data1 = cipher.encrypt(text1)
        data2 = cipher.encrypt(text2)
        assert data2.startswith(data1)

    def test03(self):
        password = "".join(
            randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
        )
        cipher = S12Cipher(
            password=password, result_encoder=cipherutils.HexlifyEncoder()
        )
        for c in sixutils.TEXT(string.ascii_letters):
            d = cipher.encrypt(c)
            assert d
            print("{} ==> {}".format(c, d))

    def test04(self):
        gen = RawDataEncoder()
        data1 = os.urandom(1024)
        data2 = gen.encode(data1)
        data3 = gen.decode(data2)
        assert data1 == data3

    def test05(self):
        gen = HexlifyEncoder()
        data1 = os.urandom(1024)
        data2 = gen.encode(data1)
        data3 = gen.decode(data2)
        assert data1 == data3

    def test06(self):
        gen = Base64Encoder()
        data1 = os.urandom(1024)
        data2 = gen.encode(data1)
        data3 = gen.decode(data2)
        assert data1 == data3

    def test07(self):
        gen = SafeBase64Encoder()
        data1 = os.urandom(1024)
        data2 = gen.encode(data1)
        data3 = gen.decode(data2)
        assert data1 == data3

    def test08(self):
        cipher = S12Cipher(
            password="testpwd", result_encoder=HexlifyEncoder(), force_text=True
        )
        text1 = "".join(randomutils.choices(string.ascii_letters, k=1024))
        text2 = cipher.encrypt(text1)
        text3 = cipher.decrypt(text2)
        assert text1 == text3

    def test09(self):
        cipher = cipherutils.AesCipher(
            password="testpwd", result_encoder=Base64Encoder(), force_text=True
        )
        text1 = "".join(randomutils.choices(string.ascii_letters, k=1024))
        text2 = cipher.encrypt(text1.encode())
        text3 = cipher.decrypt(text2)
        assert text1 == text3

    def test10(self):
        cipher = cipherutils.AesCipher(
            password="testpwd",
            result_encoder=cipherutils.HexlifyEncoder(),
            kwargs={"key": cipherutils.mysql_aes_key},
            force_text=True,
        )
        text1 = "".join(randomutils.choices(string.ascii_letters, k=8))
        text2 = cipher.encrypt(text1.encode())
        text3 = cipher.decrypt(text2)
        assert text1 == text3

    def test11(self):
        password = "".join(
            randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
        )
        cipher = IvCipher(password=password)
        last_n2 = None
        for n1 in range(-10000, 10000, 100):
            n2 = cipher.encrypt(n1)
            n3 = cipher.decrypt(n2)
            if last_n2 is None:
                last_n2 = n2
            else:
                assert n2 > last_n2
            assert n1 == n3
            last_n2 = n2

    def test12(self):
        password = "".join(
            randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
        )
        cipher = IvCipher(password=password)
        last_n2 = None
        for n1 in range(-10000, 10000, 100):
            n2 = cipher.encrypt(n1)
            n3 = cipher.decrypt(n2)
            if last_n2 is None:
                last_n2 = n2
            else:
                assert n2 > last_n2
            assert n1 == n3
            last_n2 = n2

    def test13(self):
        password = "".join(
            randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
        )
        cipher = IvfCipher(password=password)
        n1 = 19231.1313
        n2 = cipher.encrypt(n1)
        n3 = cipher.decrypt(n2)
        assert n1 == n3

    def test14(self):
        for int_digits in range(1, 11):
            for float_digits in range(1, 6):
                for _ in range(5):
                    password = "".join(
                        randomutils.choices(
                            string.ascii_letters, k=random.randint(4, 16)
                        )
                    )
                    cipher_params = {
                        "int_digits": int_digits,
                        "float_digits": float_digits,
                    }
                    cipher = IvfCipher(password=password, **cipher_params)
                    max_value = 10**int_digits + (1 - 0.1**float_digits)
                    range_start = -1 * max_value * (10**float_digits)
                    range_end = max_value * (10**float_digits)
                    ns = []
                    for n1 in range(
                        int(range_start), int(range_end), int(range_end / 13)
                    ):
                        n1 /= 10**float_digits
                        n2 = cipher.encrypt(n1)
                        n3 = cipher.decrypt(n2)
                        assert n1 == n3
                        ns.append(n2)
                    assert listutils.is_ordered(ns)

    def test15(self):
        for int_digits in range(1, 11):
            for _ in range(50):
                float_digits = 0
                password = "".join(
                    randomutils.choices(string.ascii_letters, k=random.randint(4, 16))
                )
                cipher_params = {
                    "int_digits": int_digits,
                    "float_digits": float_digits,
                }
                cipher = IvfCipher(password=password, kwargs=cipher_params)
                max_value = 10**int_digits - random.randint(1, 1000)
                last_n2 = None
                for n1 in range(
                    int(-1 * max_value), int(max_value), max(int(max_value / 13), 1)
                ):
                    n2 = cipher.encrypt(n1)
                    n3 = cipher.decrypt(n2)
                    if last_n2 is None:
                        last_n2 = n2
                    else:
                        assert n2 > last_n2
                    assert n1 == n3
                    last_n2 = n2

    def test16(self):
        for i in range(0, 100):
            cipher = S1Cipher(password=os.urandom(8))
            data1 = os.urandom(1024)
            data2 = cipher.encrypt(data1)
            data3 = cipher.decrypt(data2)
            assert data1 == data3

    def test17(self):
        for i in range(0, 100):
            cipher = S2Cipher(password=os.urandom(8))
            data1 = os.urandom(1024)
            data2 = cipher.encrypt(data1)
            data3 = cipher.decrypt(data2)
            assert data1 == data3

    def test18(self):
        # Used for sorting test for S1Cipher
        # failed
        for loop1 in range(1):
            cipher = cipherutils.S1Cipher(password=os.urandom(16))
            for loop2 in range(100):
                data1 = os.urandom(random.randint(1, 100))
                data2 = os.urandom(random.randint(1, 100))
                flag1 = data1 > data2
                data3 = cipher.encrypt(data1)
                data4 = cipher.encrypt(data2)
                flag2 = data3 > data4
                # assert flag1 == flag2

    def test19(self):
        # Used for sorting test for S2Cipher
        # failed
        for loop1 in range(1):
            cipher = cipherutils.S2Cipher(password=os.urandom(16))
            for loop2 in range(100):
                data1 = os.urandom(random.randint(1, 100))
                data2 = os.urandom(random.randint(1, 100))
                flag1 = data1 > data2
                data3 = cipher.encrypt(data1)
                data4 = cipher.encrypt(data2)
                flag2 = data3 > data4
                # assert flag1 == flag2

    def test20(self):
        # Used for sorting test for S12Cipher
        # pass
        for loop1 in range(1):
            cipher = cipherutils.S12Cipher(password=os.urandom(16))
            for loop2 in range(100):
                data1 = os.urandom(random.randint(1, 100))
                data2 = os.urandom(random.randint(1, 100))
                flag1 = data1 > data2
                data3 = cipher.encrypt(data1)
                data4 = cipher.encrypt(data2)
                flag2 = data3 > data4
                assert flag1 == flag2

    def test21(self):
        # Used for partly searching test for S1Cipher with result_encoder=RawDataEncoder
        # pass
        for loop1 in range(1):
            password = os.urandom(16)
            cipher = cipherutils.S1Cipher(password=password)
            for loop2 in range(10):
                for x in range(256):
                    all_seeds = list(range(256))
                    all_seeds.remove(x)
                    random.shuffle(all_seeds)
                    data = cipher.encrypt(bytes(all_seeds))
                    xt = cipher.encrypt(bytes([x]))
                    assert not xt in data

    def test22(self):
        # Used for partly searching test for S1Cipher with result_encoder=HexlifyEncoder
        # failed
        for loop1 in range(1):
            password = os.urandom(16)
            cipher = cipherutils.S1Cipher(
                password=password, result_encoder=cipherutils.HexlifyEncoder()
            )
            for loop2 in range(10):
                for x in range(256):
                    all_seeds = list(range(256))
                    all_seeds.remove(x)
                    random.shuffle(all_seeds)
                    data = cipher.encrypt(bytes(all_seeds))
                    xt = cipher.encrypt(bytes([x]))
                    # assert not xt in data

    def test23(self):
        # Used for partly searching test for S2Cipher with result_encoder=Utf8Encoder
        # failed
        for loop1 in range(1):
            password = os.urandom(16)
            cipher = cipherutils.S2Cipher(password=password)
            for loop2 in range(10):
                for x in range(256):
                    all_seeds = list(range(256))
                    all_seeds.remove(x)
                    random.shuffle(all_seeds)
                    data = cipher.encrypt(bytes(all_seeds))
                    xt = cipher.encrypt(bytes([x]))
                    # assert not xt in data

    def test24(self):
        # Used for partly searching test for S2Cipher with result_encoder=HexlifyEncoder
        # failed
        for loop1 in range(1):
            password = os.urandom(16)
            cipher = cipherutils.S2Cipher(
                password=password, result_encoder=cipherutils.HexlifyEncoder()
            )
            for loop2 in range(10):
                for x in range(256):
                    all_seeds = list(range(256))
                    all_seeds.remove(x)
                    random.shuffle(all_seeds)
                    data = cipher.encrypt(bytes(all_seeds))
                    xt = cipher.encrypt(bytes([x]))
                    # assert not xt in data

    def test25(self):
        # Used for partly searching test for S12Cipher with result_encoder=RawDataEncoder
        # failed
        for loop1 in range(1):
            password = os.urandom(16)
            cipher = cipherutils.S12Cipher(password=password)
            for loop2 in range(10):
                for x in range(256):
                    all_seeds = list(range(256))
                    all_seeds.remove(x)
                    random.shuffle(all_seeds)
                    data = cipher.encrypt(bytes(all_seeds))
                    xt = cipher.encrypt(bytes([x]))
                    # assert not xt in data

    def test26(self):
        # Used for partly searching test for S12Cipher with result_encoder=HexlifyEncoder
        # failed
        for loop1 in range(1):
            password = os.urandom(16)
            cipher = cipherutils.S12Cipher(
                password=password, result_encoder=cipherutils.HexlifyEncoder()
            )
            for loop2 in range(10):
                for x in range(256):
                    all_seeds = list(range(256))
                    all_seeds.remove(x)
                    random.shuffle(all_seeds)
                    data = cipher.encrypt(bytes(all_seeds))
                    xt = cipher.encrypt(bytes([x]))
                    # assert not xt in data

    def test27(self):
        cipher = cipherutils.MysqlAesCipher(password="testpwd")
        data1 = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        data12 = cipher.encrypt(data1)
        data22 = binascii.unhexlify(
            b"F75693794539B946929EDF3DB505B35DF346F20390F728883B1F9A0723CF00C35EAAF4DEF9145D8F04291F2C2CC415E75FA3881F5C2A10C8D19B347A07ABA5CE"
        )
        data3 = cipher.decrypt(data12)
        assert data12 == data22
        assert data3 == data1

    def test28(self):
        data1 = "hello world"
        pk, sk = rsautils.newkeys(1024)
        pkt = pk.export_key().decode()
        skt = sk.export_key().decode()
        print(pkt)
        print(skt)
        cipher = cipherutils.RsaCipher(public_key=pkt)
        data2 = cipher.encrypt(data1)
        print(data2)
        cipher = cipherutils.RsaCipher(private_key=skt)
        data3 = cipher.decrypt(data2)
        print(data3)
        assert data1 == data3

    def test29(self):
        thelist = []
        for i in range(1000000000000000, 1000000000000000 + 10):
            cipher = IvfCipher(password="testpwd")
            value = cipher.encrypt(i)
            thelist.append(value)
        assert listutils.is_ordered(thelist)

    def test30(self):
        c1 = S1Cipher(password="hello")
        c2 = S1Cipher(password="hello")
        d1 = c1.encrypt("hello")
        d2 = c2.encrypt("hello")
        assert d1 == d2

    def test31(self):
        c1 = S2Cipher(password="hello")
        c2 = S2Cipher(password="hello")
        d1 = c1.encrypt("hello")
        d2 = c2.encrypt("hello")
        assert d1 == d2

    def test32(self):
        c1 = S12Cipher(password="hello")
        c2 = S12Cipher(password="hello")
        d1 = c1.encrypt("hello")
        d2 = c2.encrypt("hello")
        assert d1 == d2

    def test33(self):
        c1 = S1Cipher(password="hello")
        d1 = c1.encrypt("hello")

        password = c1.dumps()
        c2 = S1Cipher(password=password)
        d2 = c2.encrypt("hello")
        assert d1 == d2

    def test34(self):
        c1 = S2Cipher(password="hello")
        d1 = c1.encrypt("hello")

        password = c1.dumps()
        c2 = S2Cipher(password=password)
        d2 = c2.encrypt("hello")
        assert d1 == d2

    def test35(self):
        c1 = S12Cipher(password="hello")
        d1 = c1.encrypt("hello")

        password = c1.dumps()
        c2 = S12Cipher(password=password)
        d2 = c2.encrypt("hello")
        assert d1 == d2

    def test36(self):
        password = "j8w99hmOUaiiHcs9wAQb6JHaFMunWR3u"
        data1 = "hello world"
        data2 = "40a3d36ba209b051301895bf2f028a30"
        cipher = cipherutils.AesCipher(
            password=password,
            result_encoder=cipherutils.HexlifyEncoder(),
            key=cipherutils.mysql_aes_key,
            force_text=True,
        )
        data3 = cipher.decrypt(data2)
        assert data1 == data3

    def test37(self):
        rndpwd = "z0gZPuIh"
        iv = "8R7xqSM3Mh3NHDbv"
        data1 = "QN9OJ9UCH18HjA14AskgdMoxlhPqJYH7"
        data2 = "173e4cd102776813462fbb3d93416e8e5524c981ab6affc191f4eed233956c18b215c6407a2c2aa333b0969c87db17b6"
        gen = cipherutils.AesCipher(
            password=rndpwd,
            mode=cipherutils.AES.MODE_CBC,
            aes_init_params={"iv": sixutils.BYTES(iv)},
            result_encoder=cipherutils.HexlifyEncoder(),
            force_text=True,
        )
        data3 = gen.encrypt(data1)
        assert data2 == data3
        data4 = gen.decrypt(data3)
        assert data1 == data4

    def test38(self):
        password = "z0gZPuIh"
        iv = "8R7xqSM3Mh3NHDbv"
        data1 = "QN9OJ9UCH18HjA14AskgdMoxlhPqJYH7"
        data2 = "4f1db4f6c19859b1d858296f1b591127146330683f4606046bdeb0958606c14e44ca90a8b1dd3daeca76d26f319cc61c"
        gen = cipherutils.AesCipher(
            password=password,
            mode=cipherutils.AES.MODE_CFB,
            aes_init_params={"iv": sixutils.BYTES(iv)},
            result_encoder=cipherutils.HexlifyEncoder(),
            force_text=True,
        )
        data3 = gen.encrypt(data1)
        assert data2 == data3
        data4 = gen.decrypt(data3)
        assert data1 == data4

    def test39(self):
        password = "z0gZPuIh"
        prefix = b"prefix"
        suffix = b"suffix"
        initial_value = 123412341
        iv = "8R7xqSM3Mh3NHDbv"
        data1 = "QN9OJ9UCH18HjA14AskgdMoxlhPqJYH7"
        data2 = "a95882551cebd8ac44ebbcbe22e58acd72c48a0975efa8c153d952ba161f059b9ecb44754cbf2f26cefc6293bc50c045"
        gen = cipherutils.AesCipher(
            password=password,
            mode=cipherutils.AES.MODE_CTR,
            aes_init_params={
                "counter": Counter.new(
                    (cipherutils.AES.block_size - len(prefix) - len(suffix)) * 8,
                    prefix=prefix,
                    suffix=suffix,
                    initial_value=initial_value,
                )
            },
            result_encoder=cipherutils.HexlifyEncoder(),
            force_text=True,
        )
        data3 = gen.encrypt(data1)
        assert data2 == data3
        data4 = gen.decrypt(data3)
        assert data1 == data4

    def test40(self):
        testpwd = "7KqZ4DwSLU3d"
        cipher = cipherutils.AesCtrCipher(
            password=testpwd,
            result_encoder=cipherutils.Base64Encoder(),
            force_text=True,
        )
        data1 = "E1yWFx4byty4CHb7hTyyDmfA3jz100un"
        data2 = cipher.encrypt(data1)
        data3 = cipher.decrypt(data2)
        assert data1 == data3

    def test41(self):
        testpwd = os.urandom(12)
        cipher = cipherutils.AesCtrCipher(
            password=testpwd,
            result_encoder=cipherutils.Base64Encoder(),
        )
        data1 = os.urandom(1024)
        data2 = cipher.encrypt(data1)
        data3 = cipher.decrypt(data2)
        assert data1 == data3

    def test42(self):
        testpwd = os.urandom(12)
        cipher = cipherutils.AesGcmCipher(
            password=testpwd,
            result_encoder=cipherutils.Base64Encoder(),
        )
        data1 = os.urandom(1023)
        data2 = cipher.encrypt(data1)
        data3 = cipher.decrypt(data2)
        assert data1 == data3

    def test43(self):
        # 原始数据来自 https://try8.cn/tool/cipher/aes
        # 测试gcm加解密与其他语言生成的数据的兼容性
        # 其他人对于结果数据的封装可能与我们使用的封装格式不同
        # 将实际各项内容解出来后，按我们的格式要求进行封装。
        cipher_text = base64utils.decodebytes(b"Ue58k2ky2vM=")
        tag = base64utils.decodebytes(b"81ZPIPGgiRQtE3pzo74BYQ==")
        header = b"adf"
        password = b"1234567812345678"
        nonce = b"1234567812345678"
        data1 = b"123456ef"
        data2 = json.dumps(
            {
                "cipher_text": sixutils.TEXT(binascii.hexlify(cipher_text)),
                "header": sixutils.TEXT(binascii.hexlify(header)),
                "tag": sixutils.TEXT(binascii.hexlify(tag)),
                "nonce": sixutils.TEXT(binascii.hexlify(nonce)),
            }
        )
        cipher = cipherutils.AesGcmCipher(
            password=password, key=cipherutils.raw_aes_key
        )
        data3 = cipher.decrypt(data2)
        assert data1 == data3

    def test44(self):
        cipher = cipherutils.AesCipher(
            "hello",
            mode=cipherutils.AES.MODE_CTR,
            aes_init_params={"nonce": b"12345678"},
        )
        data1 = b"hello world"
        data2 = cipher.encrypt(data1)
        data3 = cipher.decrypt(data2)
        assert data1 == data3


if __name__ == "__main__":
    unittest.main()
