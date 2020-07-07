# -*- coding: utf-8 -*-
"""Utils to make the command-line interface a bit prettier."""

import logging
import os

import asyncclick
import logzero


def configure_logger(*logger_names: str, **kwargs):
    """Configure several loggers at once.

    Configuration options that gets parsed from *kwargs* currently are:

      - *verbosity* (`str`)
      - *logformat* (`str`)
      - *dateformat* (`str`)
      - *color* (`bool`)

    Check the source code for details.

    Args:

        logger_names (Iterable[str]): a list of logger names
        **kwargs: optional properties to use for configuration
    """

    verbosity = kwargs.get("verbosity", logging.WARN)
    logformat = kwargs.get("logformat", None)
    dateformat = kwargs.get("dateformat", None)
    color = kwargs.get("color", True)

    logfile = kwargs.get("logfile", None)
    disable_stderr = kwargs.get("disable_stderr", False)

    if verbosity is None:
        verbosity = logging.WARN
    if isinstance(verbosity, str):
        verbosity = logging._nameToLevel[verbosity]

    if logformat is None:
        logformat = "%(color)s[%(levelname)1.1s %(name)s]%(end_color)s %(message)s"
    if dateformat is None:
        dateformat = "%H:%M:%S"
    formatter = logzero.LogFormatter(color=color, fmt=logformat, datefmt=dateformat)

    logzero.loglevel(verbosity)
    for logger_name in logger_names:
        logzero.setup_logger(
            logger_name,
            level=verbosity,
            formatter=formatter,
            logfile=logfile,
            disableStderrLogger=disable_stderr,
        )


def check_env(**kwargs):
    """Add logfile if env var is present."""

    if "logfile" not in kwargs.keys():

        env_lf = os.getenv("LOG_FILE", None)
        if env_lf:
            kwargs["logfile"] = env_lf

    return kwargs


def logzero_option(*logger_names, **kwargs):
    """Asyncclick option to control log level."""

    kwargs = check_env(**kwargs)

    if not logger_names:
        logger_names = ("upcheck",)

    def option(f):
        def _configure_logging(ctx, param, value):

            kwargs["verbosity"] = value.upper()
            configure_logger(*logger_names, **kwargs)

        default_verbosity = kwargs.get("default_verbosity", "WARNING")
        return asyncclick.option(
            "--verbosity",
            callback=_configure_logging,
            default=default_verbosity,
            metavar="LEVEL",
            expose_value=False,
            help="The log level: CRITICAL, ERROR, WARNING, INFO, DEBUG",
            type=asyncclick.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
            required=False,
            is_eager=True,
        )(f)

    return option
