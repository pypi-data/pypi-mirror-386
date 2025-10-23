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
import os
import json
import binascii
from zenutils.cipherutils import *
from zenutils import sixutils
from zenutils import base64utils

import zenutils.cipherutils

__all__ = (
    []
    + zenutils.cipherutils.__all__
    + [
        "get_aes_mode",
        "md5_key",
        "mysql_aes_key",
        "sha1prng_key",
        "aes_padding_ansix923",
        "aes_padding_iso10126",
        "aes_padding_pkcs5",
        "AesCipher",
        "MysqlAesCipher",
        "RawKeyAesCipher",
        "RsaCipher",
        "AesCtrCipher",
        "AesGcmCipher",
    ]
)


from Crypto.Cipher import AES

from fastutils import aesutils
from fastutils import rsautils

from fastutils.aesutils import get_aes_mode

from fastutils.aesutils import get_md5_key as md5_key
from fastutils.aesutils import get_mysql_aes_key as mysql_aes_key
from fastutils.aesutils import get_sha1prng_key as sha1prng_key
from fastutils.aesutils import get_raw_aes_key as raw_aes_key

from fastutils.aesutils import padding_ansix923 as aes_padding_ansix923
from fastutils.aesutils import padding_iso10126 as aes_padding_iso10126
from fastutils.aesutils import padding_pkcs5 as aes_padding_pkcs5


class AesCtrCipher(CipherBase):
    """AES加解密码。使用CTR模式。

    CTR模式在加密后会产生nonce，需要与结果一起发送到解密端。
    CTR模式加密结果的数据结构为：
        {
            "cipher_text": cipher_text,
            "nonce": cipher.nonce,
        }
    将该结构使用json序列化后，形成最终的结果字节流。

    另外，CTR模式不需要对加密数据进行填充。
    """

    def __init__(self, password=None, key=sha1prng_key, **kwargs):
        self.aes_key_prepare = key
        self.aes_key = self.aes_key_prepare(password)
        super(AesCtrCipher, self).__init__(password, **kwargs)

    def do_encrypt(self, data, **kwargs):
        cipher = AES.new(self.aes_key, AES.MODE_CTR)
        cipher_text = cipher.encrypt(data)
        nonce = cipher.nonce
        return sixutils.BYTES(
            json.dumps(
                {
                    "cipher_text": sixutils.TEXT(binascii.hexlify(cipher_text)),
                    "nonce": sixutils.TEXT(binascii.hexlify(nonce)),
                }
            )
        )

    def do_decrypt(self, data, **kwargs):
        data = sixutils.TEXT(data)
        info = json.loads(data)  # 低版本python中json.loads要求参数必须为str类型，不能为bytes类型
        cipher_text = binascii.unhexlify(sixutils.BYTES(info["cipher_text"]))
        nonce = binascii.unhexlify(sixutils.BYTES(info["nonce"]))
        cipher = AES.new(self.aes_key, AES.MODE_CTR, nonce=nonce)
        return cipher.decrypt(cipher_text)


class AesGcmCipher(CipherBase):
    """AES加解密码。使用GCM模式。

    GCM模式在加密后会产生nonce, tag，需要与结果一起发送到解密端。
    GCM模式加密结果的数据结构为：
        {
            "header": binascii.hexlify(header),
            "cipher_text": binascii.hexlify(cipher_text),
            "nonce": binascii.hexlify(cipher.nonce),
            "tag": binascii.hexlify(tag),
        }
    将该结构使用json序列化后，形成最终的结果字节流。

    @Example 1

    加密内容及结果来自：https://try8.cn/tool/cipher/aes

    ```
        import json
        import binascii
        from fastutils import cipherutils
        from zenutils import sixutils
        from zenutils import base64utils

        cipher_text = base64utils.decodebytes(b"Ue58k2ky2vM=") # 其它语言加密后的cipher_text
        tag = base64utils.decodebytes(b"81ZPIPGgiRQtE3pzo74BYQ==") # 其它语言加密后的tag
        header = b"adf" # 其它语言加密时使用header
        password = b"1234567812345678" # 其它语言加密时使用的密码，未使用密码预处理
        nonce = b"1234567812345678" # 其它语言加密时使用的nonce。如果没有在加密时指定，会随机生成nonce
        data1 = b"123456ef" # 明文内容
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

    ```
    """

    def __init__(
        self,
        password=None,
        header=None,
        key=sha1prng_key,
        random_header_size=64,
        **kwargs
    ):
        """
        @param password:
            任意字符串。
            由于AES要求的KEY为16字节长度的字节流，
            所以一般会对密码进行预处理。
            使用key函数对密码进行预算，一般会使用sha1rpng方法。

        @param header:
            任意字节流。
            允许为空。
            如果空的话，会生成随机指定长度的字节字节流。
            默认为64字节.
            解密的时候，不需要提供，因为加密结果数据中已经提供了header数据。

        @param key:
            密码预处理算法。

        @param random_header_size:
            加密时，未指定header的情况，默认生成的header长度。

        """
        header = header or os.urandom(random_header_size)
        self.aes_key_prepare = key
        self.aes_gcm_header = sixutils.BYTES(header)
        self.aes_key = self.aes_key_prepare(password)
        super(AesGcmCipher, self).__init__(password, **kwargs)

    def do_encrypt(self, data, **kwargs):
        cipher = AES.new(self.aes_key, AES.MODE_GCM)
        cipher.update(self.aes_gcm_header)
        cipher_text, tag = cipher.encrypt_and_digest(data)
        nonce = cipher.nonce
        print(
            {
                "cipher_text": sixutils.TEXT(binascii.hexlify(cipher_text)),
                "nonce": sixutils.TEXT(binascii.hexlify(nonce)),
                "header": sixutils.TEXT(binascii.hexlify(self.aes_gcm_header)),
                "tag": sixutils.TEXT(binascii.hexlify(tag)),
            }
        )
        return sixutils.BYTES(
            json.dumps(
                {
                    "cipher_text": sixutils.TEXT(binascii.hexlify(cipher_text)),
                    "nonce": sixutils.TEXT(binascii.hexlify(nonce)),
                    "header": sixutils.TEXT(binascii.hexlify(self.aes_gcm_header)),
                    "tag": sixutils.TEXT(binascii.hexlify(tag)),
                }
            )
        )

    def do_decrypt(self, data, **kwargs):
        data = sixutils.TEXT(data)
        info = json.loads(data)  # 低版本python中json.loads要求参数必须为str类型，不能为bytes类型
        cipher_text = binascii.unhexlify(sixutils.BYTES(info["cipher_text"]))
        nonce = binascii.unhexlify(sixutils.BYTES(info["nonce"]))
        header = binascii.unhexlify(sixutils.BYTES(info["header"]))
        tag = binascii.unhexlify(sixutils.BYTES(info["tag"]))
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=nonce)
        cipher.update(header)
        return cipher.decrypt_and_verify(cipher_text, tag)


class AesCipher(CipherBase):
    """AES加解密工具类型。

    默认为ECB模式，只要指定password即可。
    CBC, CFB, OFB等模式，需要指定mode，并提供iv初始化参数。
    CTR模式:
        1. 支持指定counter初始化方式，支持指定nonce的初始化方式。
        2. 但不支持加密时不指定nonce，要求AES算法自动生成随机nonce的初始化方式，因为没有可用于返回随机nonce的结果编码机制。
    GCM模式不支持。

    ### Example 1
    mode: AES.MODE_ECB
    padding: aes_padding_pkcs5
    key: sha1prng_key # use sha1prng to transform the original password


    ```
        In [47]: from fastutils import cipherutils

        In [48]: cipherutils.AesCipher(password='hello')
        Out[48]: <fastutils.cipherutils.AesCipher at 0x2285d130c10>

        In [49]: cipher = cipherutils.AesCipher(password='hello')

        In [50]: cipher.encrypt('hello')
        Out[50]: b'\\xa0\\x96<YaIOy`fiw\\x0b\\xf3\\xf7\\x84'

        In [51]: cipher.decrypt(cipher.encrypt('hello'))
        Out[51]: b'hello'

        In [59]: cipher = cipherutils.AesCipher(password='hello', result_encoder=cipherutils.Base64Encoder(), force_text=True)

        In [60]: cipher.encrypt('hello')
        Out[60]: 'oJY8WWFJT3lgZml3C/P3hA=='

        In [61]: cipher.decrypt('oJY8WWFJT3lgZml3C/P3hA==')
        Out[61]: 'hello'
    ```

    ### Example 2
    mode: AES.MODE_CBC
    注意：需要在初始化时指定16位的iv参数，bytes类型。

    ```
        from fastutils import cipherutils
        from zenutils import sixutils

        password = "z0gZPuIh"
        iv = "8R7xqSM3Mh3NHDbv"
        data1 = "QN9OJ9UCH18HjA14AskgdMoxlhPqJYH7"
        data2 = "173e4cd102776813462fbb3d93416e8e5524c981ab6affc191f4eed233956c18b215c6407a2c2aa333b0969c87db17b6"
        gen = cipherutils.AesCipher(
            password=password,
            mode=cipherutils.AES.MODE_CBC,
            aes_init_params={"iv": sixutils.BYTES(iv)},
            result_encoder=cipherutils.HexlifyEncoder(),
            force_text=True,
        )
        data3 = gen.encrypt(data1)
        assert data2 == data3
        data4 = gen.decrypt(data3)
        assert data1 == data4

    ```

    ### Example 3
    mode: AES.MODE_CFB
    注意：需要在初始化时指定16位的iv参数，bytes类型。

    ```
        from fastutils import cipherutils
        from zenutils import sixutils

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

    ```

    ### Example 4
    mode: AES.MODE_OFB
    注意：需要在初始化时指定16位的iv参数，bytes类型。

    ```
        from fastutils import cipherutils
        from zenutils import sixutils

        password = "z0gZPuIh"
        iv = "8R7xqSM3Mh3NHDbv"
        data1 = "QN9OJ9UCH18HjA14AskgdMoxlhPqJYH7"
        data2 = "4fe46389cbf161de5df75273aff2301c077c5d0ea47063a4ff1175e864cbed1db157c9626591a64f12745e76f903780c"
        gen = cipherutils.AesCipher(
            password=password,
            mode=cipherutils.AES.MODE_OFB,
            aes_init_params={"iv": sixutils.BYTES(iv)},
            result_encoder=cipherutils.HexlifyEncoder(),
            force_text=True,
        )
        data3 = gen.encrypt(data1)
        assert data2 == data3
        data4 = gen.decrypt(data3)
        assert data1 == data4

    ```

    ### Example 5
    mode: AES.MOD_CTR
    注意：
    - 需要在初始化时指定Crypto.Util.Counter实例。
    - counter在不同语言中的实现不同，可能会导致无法跨语言加解密码，一般不推荐使用。
    - prefix, suffix的长度之和不能大于12。

    ```
        from fastutils import cipherutils
        from Crypto.Util import Counter

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

    ```

    """

    def __init__(
        self,
        password,
        padding=aes_padding_pkcs5,
        key=sha1prng_key,
        mode=AES.MODE_ECB,
        aes_init_params=None,
        **kwargs
    ):
        self.aes_init_params = aes_init_params or {}
        self.aes_init_params.update(
            {
                "password": password,
                "padding": padding,
                "key": key,
                "mode": mode,
            }
        )
        super(AesCipher, self).__init__(password=password, **kwargs)

    def do_encrypt(self, data, **kwargs):
        calling_kwargs = {}
        calling_kwargs.update(self.aes_init_params)
        calling_kwargs.update(kwargs)
        return aesutils.encrypt(data, **calling_kwargs)

    def do_decrypt(self, data, **kwargs):
        calling_kwargs = {}
        calling_kwargs.update(self.aes_init_params)
        calling_kwargs.update(kwargs)
        return aesutils.decrypt(data, **calling_kwargs)


class MysqlAesCipher(AesCipher):
    """AesCipher.

    mode: AES.MODE_ECB
    padding: aes_padding_pkcs5
    key: mysql_aes_key # use mysql default way to transform the original password

    Example:

    In [52]: from fastutils import cipherutils

    In [53]: cipher = cipherutils.MysqlAesCipher(password='hello')

    In [54]: cipher.encrypt('hello')
    Out[54]: b'\\xca\\xb2\\x9e\\xe5\\x9e\\xe9\\xec\\xc3j\\xc7\\xdf\\x82l\\x1b\\xcd\\xa9'

    In [55]: cipher.decrypt(cipher.encrypt('hello'))
    Out[55]: b'hello'

    In [56]: cipher = cipherutils.MysqlAesCipher(password='hello', result_encoder=cipherutils.Base64Encoder(), force_text=True)

    In [57]: cipher.encrypt('hello')
    Out[57]: 'yrKe5Z7p7MNqx9+CbBvNqQ=='

    In [58]: cipher.decrypt('yrKe5Z7p7MNqx9+CbBvNqQ==')
    Out[58]: 'hello'
    """

    def __init__(
        self,
        password,
        padding=aes_padding_pkcs5,
        key=mysql_aes_key,
        mode=AES.MODE_ECB,
        **kwargs
    ):
        super(MysqlAesCipher, self).__init__(password, padding, key, mode, **kwargs)


class RawKeyAesCipher(AesCipher):
    """AesCipher.

        mode: AES.MODE_ECB
        padding: aes_padding_pkcs5
        key: raw_aes_key # use password as aes key directly, so that the password must be 16 chars length.

        Most java applications do AES encrypt like code below.

        function encrypt(String content, String password) {
            // password length must equals 16
            try {
                byte[] key = password.getBytes();
                SecretKeySpec skey = new SecretKeySpec(key, "AES")
                Cipher cipher = Cipher.getInstance(ALGORITHMSTR);
                cipher.init(Cipher.ENCRYPT_MODE, skey);
                byte[] contentBytes = content.getBytes("utf-8");
                byte[] contentEncrypted = cipher.doFinal(contentBytes);
                return Base64.encodeBase64String(contentEncrypted);
            } catch (Exception e) {
                return null;
            }
        }

        It is not good to generate the key by taking the first 16 bytes of the password. Add this to make life easy.

        Example:

        In [1]: from fastutils import cipherutils

        In [2]: cipher = cipherutils.RawKeyAesCipher(password='hello')

        In [3]: cipher.encrypt('hello') # Since password length is not 16, so encrypt get error
    ---------------------------------------------------------------------------
    ValueError                                Traceback (most recent call last)
    <ipython-input-3-f47a0d4a8ca0> in <module>
    ......
    ......
    ValueError: Incorrect AES key length (5 bytes)

    """

    def __init__(
        self,
        password,
        padding=aes_padding_pkcs5,
        key=raw_aes_key,
        mode=AES.MODE_ECB,
        **kwargs
    ):
        if len(password) < 16:
            raise ValueError(
                "The password must be in 16 chars length. More that 16 chars will be truncate the first 16 chars."
            )
        super(RawKeyAesCipher, self).__init__(password, padding, key, mode, **kwargs)


StupidJavaAesCipher = RawKeyAesCipher


class RsaCipher(CipherBase):
    default_result_encoder = Utf8Encoder()
    default_force_text = True

    def __init__(self, public_key=None, private_key=None, passphrase=None, **kwargs):
        self.passphrase = passphrase
        if public_key:
            if isinstance(public_key, sixutils.BASESTRING_TYPES):
                self.public_key = rsautils.load_public_key(public_key)
            else:
                self.public_key = public_key
        else:
            self.public_key = None
        if private_key:
            if isinstance(private_key, sixutils.BASESTRING_TYPES):
                self.private_key = rsautils.load_private_key(private_key, passphrase)
            else:
                self.private_key = private_key
            if not self.public_key:
                self.public_key = self.private_key.publickey()
        else:
            self.private_key = None
        super(RsaCipher, self).__init__(**kwargs)

    def do_encrypt(self, text, **kwargs):
        if not self.public_key:
            raise RuntimeError("public_key NOT provided...")
        result = rsautils.encrypt(text, self.public_key)
        result = sixutils.BYTES(result)
        return result

    def do_decrypt(self, data, **kwargs):
        if not self.private_key:
            raise RuntimeError("private_key NOT provided...")
        data = sixutils.TEXT(data)
        result = rsautils.decrypt(data, self.private_key)
        result = sixutils.BYTES(result)
        return result
