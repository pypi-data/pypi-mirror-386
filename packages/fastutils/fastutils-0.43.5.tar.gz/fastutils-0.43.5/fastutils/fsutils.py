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
from zenutils.fsutils import *

import zenutils.fsutils

__all__ = (
    []
    + zenutils.fsutils.__all__
    + [
        "load_application_config",
    ]
)

import yaml


def load_application_config(appname, name="config", suffix="yml"):
    """Load application config."""
    filename = get_application_config_filepath(appname, name, suffix)
    if not filename:
        return {}
    else:
        with open(filename, "rb") as fobj:
            data = yaml.safe_load(fobj)
        if not data:
            return {}
        if not isinstance(data, dict):
            return {}
        return data
