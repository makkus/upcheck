# -*- coding: utf-8 -*-
import os
import sys

from appdirs import AppDirs


upcheck_app_dirs = AppDirs("upcheck", "frkl")

if not hasattr(sys, "frozen"):
    UPCHECK_MODULE_BASE_FOLDER = os.path.dirname(__file__)
    """Marker to indicate the base folder for the `upcheck` module."""
else:
    UPCHECK_MODULE_BASE_FOLDER = os.path.join(
        sys._MEIPASS, "upcheck"  # type: ignore
    )
    """Marker to indicate the base folder for the `upcheck` module."""

UPCHECK_RESOURCES_FOLDER = os.path.join(UPCHECK_MODULE_BASE_FOLDER, "resources")

DEFAULT_KAFKA_GROUP_ID = "upcheck"
