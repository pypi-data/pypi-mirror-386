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
Make logging setup easy. Default logging settings:

```
logging_config = {
   "version": 1,
   "disable_existing_loggers": False,
   "formatters": {
      "default": {
            "format": "{asctime} {levelname} {pathname} {lineno} {module} {funcName} {process} {thread} {message}",
            "style": "{"
      },
      "message_only": {
            "format": "{message}",
            "style": "{",
      },
      "json": {
            "class": "jsonformatter.JsonFormatter",
            "format": {
               "asctime": "asctime",
               "levelname": "levelname",
               "pathname": "pathname",
               "lineno": "lineno",
               "module": "module",
               "funcName": "funcName",
               "process": "process",
               "thread": "thread",
               "message": "message",
            },
      },
   },
   "handlers": {
      "default_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
      },
      "default_file": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": logfile,
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "formatter": "default",
      },
      "json_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
      },
      "json_file": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": logfile,
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "formatter": "json",
      },
   },
   "loggers": {
   },
   "root": {
      "handlers": ["default_file", "default_console"],
      "level": loglevel,
      "propagate": True,
   }
}
```

Example:

```
from fastutils import logutils

def setup(settings):
    logging_settings = settings.get("logging", {})
    logutils.setup(**logging_settings)

```
"""

from zenutils.logutils import *
from zenutils.logutils import get_simple_config as get_simple_config_core
import zenutils.logutils
from zenutils import dictutils

__all__ = [] + zenutils.logutils.__all__

from jsonformatter import JsonFormatter


def get_simple_config(
    logfile=None,
    loglevel=None,
    logfmt=None,
    loggers=None,
    logging=None,
    console_handler_class=None,
    file_handler_class=None,
    log_to_console=True,
    log_to_file=True,
    **kwargs
):
    """Make simple logging settings.

    logfile default to app.log.
    loglevel choices are: DEBUG/INFO/WARNING/ERROR. default to INFO.
    logfmt choices are: default/message_only/json. default to default.
    Use logger parameter to override the default settings' logger sections.
    Use logging parameter to override the whole settings.

    """
    kwargs = kwargs or {}
    kwargs["log_to_console"] = log_to_console
    kwargs["log_to_file"] = log_to_file
    logging_config = get_simple_config_core(
        logfile,
        loglevel,
        logfmt,
        loggers,
        logging,
        console_handler_class,
        file_handler_class,
        **kwargs
    )
    # default logging template
    dictutils.deep_merge(
        logging_config,
        {
            "formatters": {
                "json": {
                    "class": ".".join(
                        [JsonFormatter.__module__, JsonFormatter.__name__]
                    ),
                    "format": {
                        "asctime": "asctime",
                        "levelname": "levelname",
                        "pathname": "pathname",
                        "lineno": "lineno",
                        "module": "module",
                        "funcName": "funcName",
                        "process": "process",
                        "thread": "thread",
                        "message": "message",
                    },
                },
                "simple_json": {
                    "class": ".".join(
                        [JsonFormatter.__module__, JsonFormatter.__name__]
                    ),
                    "format": {
                        "asctime": "asctime",
                        "levelname": "levelname",
                        "message": "message",
                    },
                },
            }
        },
    )
    if log_to_console:
        dictutils.deep_merge(
            logging_config,
            {
                "handlers": {
                    "json_console": get_console_handler(
                        "json", "DEBUG", handler_class=console_handler_class
                    ),
                    "simple_json_console": get_console_handler(
                        "simple_json", "DEBUG", handler_class=console_handler_class
                    ),
                }
            },
        )
    if log_to_file:
        dictutils.deep_merge(
            logging_config,
            {
                "json_file": get_file_handler(
                    logfile, "json", "DEBUG", handler_class=file_handler_class
                ),
                "simple_json_file": get_file_handler(
                    logfile, "simple_json", "DEBUG", handler_class=file_handler_class
                ),
            },
        )
    return logging_config
