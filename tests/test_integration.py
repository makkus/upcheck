# -*- coding: utf-8 -*-
import os

# if os.path.exists("/home/markus/projects/aiven/upcheck_configs/kafka/ca.pem"):
import pytest
from upcheck.models import UrlCheck
from upcheck.sources.check import ActualCheckCheckSource
from upcheck.targets import CheckTarget, CollectorCheckTarget
from upcheck.upcheck import Upcheck


RESOURCES_FOLDER = "/home/markus/projects/aiven/upcheck_configs"


@pytest.mark.anyio
async def test_integration_no_target():

    multi_check_config = os.path.join(RESOURCES_FOLDER, "multi.yaml")

    url_checks = UrlCheck.create_checks(multi_check_config)
    source = ActualCheckCheckSource(*url_checks)
    target = CollectorCheckTarget()

    upcheck = Upcheck(source=source, targets=[target])

    await upcheck.start(wait_for_keypress=False)

    assert len(target.results) == 2


@pytest.mark.anyio
async def test_integration_kafka_target(httpserver):

    if os.environ.get("AIVEN_TOKEN", None) is None:
        return
    # empty the queue if necessary
    kafka_config = {
        "type": "kafka-aiven",
        "topic": "upcheck_testing",
        "password": os.environ["AIVEN_TOKEN"],
    }
    kafka_target = CheckTarget.create_from_dict(kafka_config)

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")

    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

    source = ActualCheckCheckSource.create_check_source(check_url)

    upcheck = Upcheck(source=source, targets=[kafka_target])

    await upcheck.start(wait_for_keypress=False)

    await source.disconnect()
    await kafka_target.disconnect()
