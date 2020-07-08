#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `upcheck` package."""
import os

import pytest  # noqa
from upcheck.models import UrlCheck


RESOURCES_FOLDER = os.path.join(os.path.dirname(__file__), "resources")


def test_read_config():

    config_path = os.path.join(RESOURCES_FOLDER, "urls_1.yaml")

    checks = UrlCheck.create_checks(config_path)
    print(checks)

    assert len(checks) == 2

    for item in checks:
        assert item.url


def test_read_invalid_yaml_config():

    config_path = os.path.join(RESOURCES_FOLDER, "urls_invalid_yaml.yaml")

    with pytest.raises(Exception) as excinfo:
        UrlCheck.create_checks(config_path)

    assert "Could not read config file" in str(excinfo)


def test_read_invalid_url_config():

    config_path = os.path.join(RESOURCES_FOLDER, "urls_invalid_url.yaml")

    with pytest.raises(Exception) as excinfo:
        UrlCheck.create_checks(config_path)

    assert "invalid url (no scheme)" in str(excinfo)

    config_path = os.path.join(RESOURCES_FOLDER, "urls_invalid_url_2.yaml")

    with pytest.raises(Exception) as excinfo:
        UrlCheck.create_checks(config_path)

    assert "invalid url (no/invalid domain name)" in str(excinfo)

    with pytest.raises(Exception) as excinfo:
        UrlCheck(url="spiegel.de")
    assert "invalid url (no scheme)" in str(excinfo)
