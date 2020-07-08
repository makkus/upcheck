# -*- coding: utf-8 -*-
import os

import pytest
from upcheck.models import CheckMetric, UrlCheck
from upcheck.sources.check import ActualCheckCheckSource
from upcheck.targets import CollectorCheckTarget
from upcheck.upcheck import Upcheck


RESOURCES_FOLDER = os.path.join(os.path.dirname(__file__), "resources")


@pytest.mark.anyio
async def test_check_simple(httpserver):

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")

    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

    source = ActualCheckCheckSource.create_check_source(check_url)
    target = CollectorCheckTarget()

    upcheck: Upcheck = Upcheck(source=source, targets=[target])
    await upcheck.start(wait_for_keypress=False)
    result = target.results[0]

    assert isinstance(result, CheckMetric)
    assert result.response_code == 200


@pytest.mark.anyio
async def test_check_regex_match(httpserver):

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")

    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

    source = ActualCheckCheckSource.create_check_source(
        {"url": check_url, "regex": "abc"}
    )
    target = CollectorCheckTarget()

    upcheck: Upcheck = Upcheck(source=source, targets=[target])
    await upcheck.start(wait_for_keypress=False)
    result = target.results[0]

    print(result.__dict__)

    assert isinstance(result, CheckMetric)
    assert result.response_code == 200
    assert result.regex_matched is True


@pytest.mark.anyio
async def test_check_regex_no_match(httpserver):

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")

    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"
    source = ActualCheckCheckSource.create_check_source(
        {"url": check_url, "regex": "asdf"}
    )
    target = CollectorCheckTarget()

    upcheck: Upcheck = Upcheck(source=source, targets=[target])
    await upcheck.start(wait_for_keypress=False)
    result = target.results[0]

    assert isinstance(result, CheckMetric)
    assert result.response_code == 200
    assert result.regex_matched is False


@pytest.mark.anyio
async def test_multiple_checks(httpserver):

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")
    httpserver.expect_request("/123").respond_with_data("1234567890")
    httpserver.expect_request("/test").respond_with_data("test")

    config_base_url = f"http://{httpserver.host}:{httpserver.port}"

    url_123 = f"{config_base_url}/123"
    url_abc = f"{config_base_url}/abc"
    url_test = f"{config_base_url}/test"

    checks_config = [
        url_123,
        {"url": url_123, "regex": "123"},
        {"url": url_123, "regex": "321"},
        url_abc,
        url_test,
    ]

    checks = UrlCheck.create_checks(*checks_config)
    source = ActualCheckCheckSource(*checks)
    target = CollectorCheckTarget()
    upcheck: Upcheck = Upcheck(source=source, targets=[target])
    await upcheck.start(wait_for_keypress=False)
    results = target.results

    assert len(results) == 5

    for result in results:
        assert result.response_code == 200
        if result.url_check.url == url_abc or result.url_check.url == url_test:
            assert result.regex_matched is None
            continue

        if result.url_check.regex is None:
            assert result.regex_matched is None
        elif result.url_check.regex == "123":
            assert result.regex_matched is True
        elif result.url_check.regex == "321":
            assert result.regex_matched is False
