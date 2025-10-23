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
import unittest
from fastutils import rsautils

sktext = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAr7NZwAiJIV032u1AIGyMDPAbhfafLlKApS94+DPJZAnLQ5pB
t/9p9WCIcSI+dH6mbAB8iyyetjPXEwcc8zeoBgvuHodOKdH3MDse+aVsy9WNj95n
J9MI9teQy5U9CrpwlOQ75GjJlX/0ifily3R/7sK1PNPo57xI2ECU32tIL/GRuVPI
JDWnQSIjk8V+U6JVHrpJUHktBO9yoWNAa80p64F7iHOIUj1q/HefpTzRu8258znY
/0TRmk6lJRyePVox91NG+BeVkfICQa9e/gMnJq3ckcncKkd8ZnekaUaSRLX4513T
nzc3/YyMoXQdWelpS5pcgVpGHjlrL2bmtTOZtwIDAQABAoIBAAYfU3RL7S4FconQ
FJj3T1YFaTVyJ4/UqM5DaOK1OJeiI7wXpvdDZizPuqa+kRCRd+PG4eVznkAubu3R
z0zGVrYx5OVEGmbTUzASD1KW/23cONJCPLP4OEAUY45EhVusrXmdY7I3gza7aQkE
ag/nNQIGijbevNHpD1zBu1j3Aw1F6IWY+bDqSTYs+BycOwX26Spw2a3Zh8T2dCaA
dqvmdeSlks86qMQQ9FTOsTQTyh7xb83iayZhsK5IqK0+S1ufU4QqOLXgKpXUVMMI
S7jv4fZzpS6jg6PW48KSDwv6cT0Nk46wAVwafbpnDEi25Kn0RuAgEmeWPPmZw0+1
LEPpkEECgYEAx5r8LukVBsL09GZaoevYLkANlh72hgcuqGO7H77Z42lunY2IFi4n
+QpZHYvfCwQa03CK6Cm3HK9tN8iaB+dY1Lp2XOEHEqigZgMwhBVAymZpIP31phrT
x7CCmHjZ4uPpbHhxxfmkJy9g/eFVZzo3mV7liLbptJdjUUt1hHKoJGECgYEA4Vdi
B2aM3UY31sb+dqvN/GtIuvZCr4fC1R6cYAJIAlbJufsN0uoVn+8D3UzIqRQLYEC+
S28JdWWXq2a26Ho/yeH6mP5ESZdYa2b+o8Re8MLHVVjvfryM5g7fh2Uah02ASgpO
D6cC2UC5eXpfpl9DHQrBUroJ0k0r3imwl8J4dRcCgYEAxpjnzOzPpNiYzAqCppR3
lRzZ58GK2rOOsq/34JANTnz6N/w3qInn75tiK0mdc+JzpmhVbMUEkZ/hdR08VBzU
f2O+nI6wcNoiLR2DSgezXS4j71V+8fPDPu3aIkYr09mbx/bWjHnj37D+OdvXE0wT
QZ/vlOUZBjuR77K6jDtgHEECgYEAyqwNPxq9F0dQcZwIwjND0QOtJnrW/4jbc1NU
0gU7Pt9QEDX8+PYQ/Qe8Mg4da/TbRnb0sGPt3ejBwSdg2zcYqDrXaUNHp+i3XeIE
pMa5nVGSdvDGdvaew0wdP2lvssHB4NXj37AWn8/XAatO3BRSCIzj08P/kWZXTjmw
2s3OCYECgYAgkxXWfmTptcMLJYEGwA0K0JhCR/8zqfj+X6BpH1TQsTLmGuU8YlaV
iEF7L7CAJ1tXzgTcYxNWLlUAqhNzeLkW1d87y5w5yJI4r4qF8RfFMztRQSdgVY+v
+5t6rH40CsSC72+aJv/VArYzUEnWSf4qyQFaL7rGXxr9YBme5cOcZQ==
-----END RSA PRIVATE KEY-----
"""


class TestRsaUtils(unittest.TestCase):
    def test1(self):
        pk0, sk0 = rsautils.newkeys(1024)
        sk_text = rsautils.export_key(sk0)
        sk1 = rsautils.load_private_key(sk_text)
        pk1 = rsautils.load_public_key_from_private_key(sk_text)
        assert pk0 == pk1
        assert sk0 == sk1

    def test2(self):
        # if nbits == 1024, the max data length is 117(PKCS1_v1_5), 86(PKCS1_OAEP)
        # if nbits == 2048, the max data length is 245(PKCS1_v1_5), 214(PKCS1_OAEP)
        # if nbits == 4096, the max data length is 501(PKCS1_v1_5), 470(PKCS1_OAEP)
        pk0, sk0 = rsautils.newkeys(1024)
        for length in range(0, 86 + 1):
            print(length)
            data1 = os.urandom(length)
            text = rsautils.encrypt(data1, pk0, envelope=rsautils.PKCS1_v1_5)
            data2 = rsautils.decrypt(text, sk0, envelope=rsautils.PKCS1_v1_5)
            assert data1 == data2

    def test3(self):
        sk = rsautils.load_private_key(sktext)
        # encrypted with PKCS1_v1_5
        encrypted_data = "aLSM5Jqz+p+1ipbVl0HppTYVNZGgaEGCdTgx1l2LkISlnZ/bPIyBj4XJnPpD38BN9kDsjbPvS/JvO58YpSXf6UUNqdzi88Fk5NJHoIpfjrB4JsD0Qt9zlcagRiqaS6pdjnhwJj9cFZzJhBqkVWsL8mQs2tnXvWRxsAarehb5z1WGZJviAnzjGQbtwvLLWdYzQWeIyfbm2ccasEAxzwSmdfLh3c2DZ2ApPlTLG584uAC6TEsfMSUvv365Aej3P0bqTtqq+laybL7Vkjlg09f9HEEWONqhBbuYs4gq+yZTfiNKTHzWGv6RR15p0jvAod49gEO9CteqpNbwUCwV1VlKww=="
        data = rsautils.decrypt(encrypted_data, sk)
        assert data == b"hello world"

    def test4(self):
        import rsa

        sk = rsa.PrivateKey.load_pkcs1(sktext)
        pk = rsa.PublicKey(n=sk.n, e=sk.e)
        data1 = b"hello world"
        data2 = rsa.encrypt(data1, pk)
        data3 = rsautils.decrypt(data2, sk)
        data4 = rsautils.decrypt(data2, sk, envelope=rsautils.PKCS1_OAEP)
        assert data1 == data3
        assert data1 == data4

    def test5(self):
        sk = rsautils.load_private_key(sktext)
        data1 = b"hello world"
        data2 = "fE/q+vatQm1Qr2+BFpxUxSrMp4OcLxxxTAFBDcxGjlfFzWSKapFCGlq4/rPXELgwDx3cATpncyO8K8Acwg0E3IHZ/N3gmoBcAzG1e5O68kpKuATdxE16Ug0+loqAiRuTSy09qYuNvt/8gH9cfVQ+Qge/r5BWomb/yy54AOk6zaYYCf0nkY7BmBYFOtV5QnihKcT2QWL/hD4YCJ7pk2qoyDJtces8uhCaJqJlVmlKLvdd/FpQSoxKtyQlvqtjOaVBU2ogE6iDwaRcbETOitnwkhMi9PexlrOWC9pXSPLeEv1p23Dw1b0arMW8110deHvqb7MLjeCV77i/mnskS6RyYQ=="
        data3 = rsautils.decrypt(data2, sk)
        assert data1 == data3

    def test6(self):
        sk = rsautils.load_private_key(sktext)
        data2 = os.urandom(1023)
        data3 = rsautils.decrypt(data2, sk)  # always fail
        assert data3 is None

    def test7(self):
        sk = rsautils.load_private_key(sktext)
        pk = rsautils.load_public_key(sktext)
        data1 = b"hello world"
        data2 = rsautils.sign(data1, sk)
        data3 = rsautils.verify(data1, data2, pk)
        assert data3

    def test8(self):
        sk = rsautils.load_private_key(sktext)
        pk = rsautils.load_public_key(sktext)
        data1 = b"hello world"
        data2 = rsautils.sign(
            data1, sk, hash_method="MD5", sign_method=rsautils.PKCS1_v1_5_SIGNATURE
        )
        data3 = rsautils.verify(data1, data2, pk, hash_method="MD5")
        assert data3

    def test9(self):
        sk = rsautils.load_private_key(sktext)
        pk = rsautils.load_public_key(sktext)
        assert sk.can_sign()
        assert sk.can_encrypt()
        assert pk.can_encrypt()
        assert pk.can_sign()

    def test10(self):
        sks = "".join(sktext.splitlines()[1:-1])
        sk = rsautils.load_private_key(sks)
        assert sk.can_sign()
        assert sk.can_encrypt()

    def test11(self):
        text = """
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAykg9uAR/tuCS+dCsmntE
RtAt50NoDMUvs8bM75x7rprIVWJpeFP2plyhQ7+MhJskquEredGMrt9Y9ccra8bQ
8buSZvVOEX+FuBTA/b6qWwYNyaDyOhx0gQ8FBzxLZO7zjLESSDRkA7/oZusziVIO
0HDZbW5IFH0y4kXJr4xGrbatW5eQLcEqD8W6uoGdQlvG4kmCgW396reQGFkV3Dhz
ZwhowBePD9mjK70Ae5soNZ81XKek7yxIwEHzxPHv1ZQbcAJrwGSChCubQLjhEG7x
PMTC9Z+fpaST41oQzi+08fFpka5cKDsmLWh5iwDACHo2psbVDswTmWkceIY/+Kyv
9QIDAQAB
        """
        sk = rsautils.load_private_key(text)
        assert sk.can_encrypt()

    def test12(self):
        text = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt6wdaUKgi2w8HxU5BZOy
46YcXrA/qXy8YSoF9u2c8rTRsaMg+/owzb77+AfHzXgUFZUoGf5Ovmmxf00YkAPP
nZ0HCkkmk/AsuZwoXENJiqVixyUXk97Mz6jRjI1GA46VFgE6FjkjQCP4u5+hKlk7
X051hR1SeENZNxrUaFZDEZ65XHbTMWVjLfPX9/wvaVp3Cl4Jpw/SzsU+f2TIMVZ3
+1AxgFBTgo7FItEG6XSlMC4Eo3abE3DfVd3sMpMg03bQLb4hYry1GfrNUrLR8oX2
pfF+ZRg3pZrfKy/7LmeQWDFnDpBl32bTK6LVgSw3erLTaBFfpTA7ZONOZxAfciO4
9QIDAQAB
-----END PUBLIC KEY-----
""".strip()
        pk = rsautils.load_public_key(text)
        assert pk.can_encrypt()

    def test13(self):
        text = """
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt6wdaUKgi2w8HxU5BZOy
46YcXrA/qXy8YSoF9u2c8rTRsaMg+/owzb77+AfHzXgUFZUoGf5Ovmmxf00YkAPP
nZ0HCkkmk/AsuZwoXENJiqVixyUXk97Mz6jRjI1GA46VFgE6FjkjQCP4u5+hKlk7
X051hR1SeENZNxrUaFZDEZ65XHbTMWVjLfPX9/wvaVp3Cl4Jpw/SzsU+f2TIMVZ3
+1AxgFBTgo7FItEG6XSlMC4Eo3abE3DfVd3sMpMg03bQLb4hYry1GfrNUrLR8oX2
pfF+ZRg3pZrfKy/7LmeQWDFnDpBl32bTK6LVgSw3erLTaBFfpTA7ZONOZxAfciO4
9QIDAQAB
""".strip()
        pk = rsautils.load_public_key(text)
        assert pk.can_encrypt()

    def test14(self):
        text = """
MIIEpAIBAAKCAQEA3qisAge4hLrijYH3aD2oDrApAKr2nIepHXOjcnh6hMLF3o7A
joR81vfKYm0EBYZq7GXCnmUU76+UGptn8LH/Y9Y9zeYQn7a0mW2bQ6yBORxBgJiw
n68KbtTNsgcQ1JK9MJM4qZm1XqpgY4M6L4MmJjntEkKKyDFna9gjSXRtGu1ndLuz
YBpaPMg6IcWuM3LrElL3lPbc/1YehPEShFnXy+b/d5LQqn2G5PbeTwvf+n9gr8Hw
jV/X6BrQmdlGCvPx7iTfELRmXvccm+CXEYbg3FodHezvGNYBxEtntayqlXv6VY2E
pnVxaGschpmrX6zk+eoppRriFjBb0+RxHLywJwIDAQABAoIBAB9jT7w0Mm148ERa
ifIGnxD9rF9iZRlz1ldHMfIKdzBin1oxwttUZJ+OltfWiQvuWFcIPANFj0n/9Qo7
K3qMMnXJ1zSWC3SNtlqFT69JO349iXkDYq1gE5cZe1XEFo9LkE1aCPwqUEhkDup4
WVTRUX4aCbLam+MqHmuJheVDpbh3Hm/nHkpGNOsngq9a6dJFtIsbp9wtPNsmJsop
r/Z3DkRiQYK84j64egghc2RrHmGiaGi9zqdHt1IU7yFWexrrnrdTQwvOmT4FpL2V
YNlfPfHJ64L1AT0P/AdJ1VKLKaxxAEdm4B0Idnf9Ua6kZoauw2K4cpNqAKUIiLoI
zPmVxMECgYEA6QXSB3tvq3tez6zTIgX3l4DNqOjPqYmZzIQg5XDLx+xlvkYvfhWV
bgjD65cuQf5JuT9tigCmPc5lUqdZAB/BsSVZLmZiBAPM1XqHjJXp9ylK/YWcvr+G
TWK/jgsd64yy1yjpCPFPS3wXZuwR0FIr1IQJqP3XfeCOnNR/OaeSfTkCgYEA9J08
s984zMq/TToVuYPDoD8DsRoJnY7/UusJ5qcbsX27GMiBXpmiW90ZncOeb3xtiK+q
+3MXtKbfikLjYy2ft1Y+o0eX0F1WwiU+Ci9agKt9JmfczPF+5D8ZCqV7hzg5bwz3
VHkrXxD7xKRM99KAmb+NX+xDPfXBlPSjf5WZ+F8CgYEAk2lGM8uHmlDCathm/GgP
+DzYXZlh/Vt5+yI++UbA82l997/IvZeD34cWAgyyi7cFBna0og/FGuZdvMr3B5gP
XTRGVY8ZRHbu9sG7zFjuGJh7wyPqQ9U/bechTQeFVwS8Alb0DN8zDYqj900x+7pv
1dHtloV29D/BmD7peRykFCkCgYEA5EQa0mubEJienk122nCYTGChbFI06N/5aYJF
8gS9NgtzXfQ1rXbG6NzRu8RBhB3kBSqQ7yb+1yjl75rtoK6Bnc+QkkQL6ng/rtqc
I1r/JJVjK0S+6kztsccj8ihstsmD5xp9b0nHbGZn25/K53R7Z342Sm4qbZZ5OCx2
qmeLkBcCgYA6WGzZYt7wTKbKfZa1I7WAu5JiuNgibQUdDAZGRiN8WvBPs1PVVdC/
qDbJ9psaTwWL4aN7dkDmlpXTJyQZxHYqcSmzXU2sNh/DBaHHUrbNlN2QXFsmezt4
sO2m5kaUVcj1DTf0tRtAsPXxLIyCqDat2dN+GTmQktogyfPQi9etPA==
        """
        pk = rsautils.load_public_key(text)
        assert pk.can_encrypt()

    def test15(self):
        text = """
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAykg9uAR/tuCS+dCsmntE
RtAt50NoDMUvs8bM75x7rprIVWJpeFP2plyhQ7+MhJskquEredGMrt9Y9ccra8bQ
8buSZvVOEX+FuBTA/b6qWwYNyaDyOhx0gQ8FBzxLZO7zjLESSDRkA7/oZusziVIO
0HDZbW5IFH0y4kXJr4xGrbatW5eQLcEqD8W6uoGdQlvG4kmCgW396reQGFkV3Dhz
ZwhowBePD9mjK70Ae5soNZ81XKek7yxIwEHzxPHv1ZQbcAJrwGSChCubQLjhEG7x
PMTC9Z+fpaST41oQzi+08fFpka5cKDsmLWh5iwDACHo2psbVDswTmWkceIY/+Kyv
9QIDAQAB
        """
        pk = rsautils.load_public_key(text)
        assert pk.can_encrypt()

    def test16(self):
        text = """
MIIEpAIBAAKCAQEA3qisAge4hLrijYH3aD2oDrApAKr2nIepHXOjcnh6hMLF3o7A
joR81vfKYm0EBYZq7GXCnmUU76+UGptn8LH/Y9Y9zeYQn7a0mW2bQ6yBORxBgJiw
n68KbtTNsgcQ1JK9MJM4qZm1XqpgY4M6L4MmJjntEkKKyDFna9gjSXRtGu1ndLuz
YBpaPMg6IcWuM3LrElL3lPbc/1YehPEShFnXy+b/d5LQqn2G5PbeTwvf+n9gr8Hw
jV/X6BrQmdlGCvPx7iTfELRmXvccm+CXEYbg3FodHezvGNYBxEtntayqlXv6VY2E
pnVxaGschpmrX6zk+eoppRriFjBb0+RxHLywJwIDAQABAoIBAB9jT7w0Mm148ERa
ifIGnxD9rF9iZRlz1ldHMfIKdzBin1oxwttUZJ+OltfWiQvuWFcIPANFj0n/9Qo7
K3qMMnXJ1zSWC3SNtlqFT69JO349iXkDYq1gE5cZe1XEFo9LkE1aCPwqUEhkDup4
WVTRUX4aCbLam+MqHmuJheVDpbh3Hm/nHkpGNOsngq9a6dJFtIsbp9wtPNsmJsop
r/Z3DkRiQYK84j64egghc2RrHmGiaGi9zqdHt1IU7yFWexrrnrdTQwvOmT4FpL2V
YNlfPfHJ64L1AT0P/AdJ1VKLKaxxAEdm4B0Idnf9Ua6kZoauw2K4cpNqAKUIiLoI
zPmVxMECgYEA6QXSB3tvq3tez6zTIgX3l4DNqOjPqYmZzIQg5XDLx+xlvkYvfhWV
bgjD65cuQf5JuT9tigCmPc5lUqdZAB/BsSVZLmZiBAPM1XqHjJXp9ylK/YWcvr+G
TWK/jgsd64yy1yjpCPFPS3wXZuwR0FIr1IQJqP3XfeCOnNR/OaeSfTkCgYEA9J08
s984zMq/TToVuYPDoD8DsRoJnY7/UusJ5qcbsX27GMiBXpmiW90ZncOeb3xtiK+q
+3MXtKbfikLjYy2ft1Y+o0eX0F1WwiU+Ci9agKt9JmfczPF+5D8ZCqV7hzg5bwz3
VHkrXxD7xKRM99KAmb+NX+xDPfXBlPSjf5WZ+F8CgYEAk2lGM8uHmlDCathm/GgP
+DzYXZlh/Vt5+yI++UbA82l997/IvZeD34cWAgyyi7cFBna0og/FGuZdvMr3B5gP
XTRGVY8ZRHbu9sG7zFjuGJh7wyPqQ9U/bechTQeFVwS8Alb0DN8zDYqj900x+7pv
1dHtloV29D/BmD7peRykFCkCgYEA5EQa0mubEJienk122nCYTGChbFI06N/5aYJF
8gS9NgtzXfQ1rXbG6NzRu8RBhB3kBSqQ7yb+1yjl75rtoK6Bnc+QkkQL6ng/rtqc
I1r/JJVjK0S+6kztsccj8ihstsmD5xp9b0nHbGZn25/K53R7Z342Sm4qbZZ5OCx2
qmeLkBcCgYA6WGzZYt7wTKbKfZa1I7WAu5JiuNgibQUdDAZGRiN8WvBPs1PVVdC/
qDbJ9psaTwWL4aN7dkDmlpXTJyQZxHYqcSmzXU2sNh/DBaHHUrbNlN2QXFsmezt4
sO2m5kaUVcj1DTf0tRtAsPXxLIyCqDat2dN+GTmQktogyfPQi9etPA==
        """
        pk = rsautils.load_private_key(text)
        assert pk.can_sign()


if __name__ == "__main__":
    unittest.main()
