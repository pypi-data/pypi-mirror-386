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
import socket
from zenutils.sysutils import *

import zenutils.sysutils

__all__ = (
    []
    + zenutils.sysutils.__all__
    + [
        "get_daemon_application_pid",
        "get_worker_info",
    ]
)

import os
import platform
import psutil


def get_daemon_application_pid(pidfile):
    """Get pid from pidfile if the daemon process is alive. If the daemon process is dead, it will alway returns 0."""
    if os.path.exists(pidfile) and os.path.isfile(pidfile):
        with open(pidfile, "r", encoding="utf-8") as fobj:
            pid = int(fobj.read().strip())
        try:
            p = psutil.Process(pid=pid)
            return pid
        except psutil.NoSuchProcess:
            return 0
    else:
        return 0


def get_worker_info():
    """Get worker system information: hostname, system, release, version, machine, IPs, IPV4s, IPV6s, MACs.

    In [16]: from fastutils import sysutils

    In [17]: import json

    In [18]: print(json.dumps(sysutils.get_worker_info(), indent=4))
    {
        "hostname": "PC-MHOISDL",
        "system": "Windows",
        "release": "10",
        "version": "10.0.19042",
        "machine": "AMD64",
        "ips": [
            "192.168.1.123",
            "dd91::2355:3619:f34e:f54c"
        ],
        "ipv4s": [
            "192.168.1.123",
        ],
        "ipv6s": [
            "dd91::2355:3619:f34e:f54c"
        ],
        "macs": [
            "00-F3-C3-CF-19-24",
            "32-F9-DA-23-25-46",
        ]
    }
    """
    ipv4s = set()
    ipv6s = set()
    macs = set()
    for _, iaddrs in psutil.net_if_addrs().items():
        for iaddr in iaddrs:
            if iaddr.family == psutil.AF_LINK:
                macs.add(iaddr.address)
            elif iaddr.family == socket.AF_INET:
                ipv4s.add(iaddr.address)
            elif iaddr.family == socket.AF_INET6:
                ipv6s.add(iaddr.address)

    if "127.0.0.1" in ipv4s:
        ipv4s.remove("127.0.0.1")
    if "::1" in ipv6s:
        ipv6s.remove("::1")

    ipv4s = list(ipv4s)
    ipv6s = list(ipv6s)
    macs = list(macs)
    ipv4s.sort()
    ipv6s.sort()
    macs.sort()

    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "ips": ipv4s + ipv6s,
        "ipv4s": ipv4s,
        "ipv6s": ipv6s,
        "macs": macs,
    }
