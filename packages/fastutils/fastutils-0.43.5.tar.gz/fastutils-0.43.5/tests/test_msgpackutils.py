#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import unittest
import os
import uuid
import datetime
import pytz

from fastutils import msgpackutils

class TestMsgpackUtils(unittest.TestCase):

    def test01(self):
        msg1 = {
            "id": uuid.uuid4(),
            "type": msgpackutils.Msg.MSG_REQUEST,
            "data": {
                "str": "a",
                "int": 1234,
                "float": 1.234,
                "list": [1,2,3],
                "set": set([1,2,3]),
                "datetime": datetime.datetime.now(),
                "datetime_with_tzinfo": pytz.timezone('Asia/Shanghai').localize(datetime.datetime.now()),
                "bytes": os.urandom(10),
                "bool": True,
                "bool_false": False,
                "null": None,
                "empty_list": [],
                "empty_set": set([]),
            }
        }
        msgbytes = msgpackutils.Msg.make_msg(msg1, password="hello").dumps()
        assert msgbytes

        msg2 = msgpackutils.Msg(password="hello").loads(msgbytes)
        msg3 = msg2.as_dict()

        assert msg3 == msg1

if __name__ == "__main__":
    unittest.main()
