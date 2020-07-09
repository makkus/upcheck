# -*- coding: utf-8 -*-
import os

import pytest
from upcheck.exceptions import UpcheckException
from upcheck.sources import CheckSource
from upcheck.sources.kafka import KafkaSource


RESOURCES_FOLDER = os.path.join(os.path.dirname(__file__), "resources")


def test_source_config():

    config_file = os.path.join(RESOURCES_FOLDER, "kafka_source.yaml")

    source = CheckSource.create_from_file(config_file)
    assert isinstance(source, CheckSource)
    assert isinstance(source, KafkaSource)


def test_source_config_fail():

    config_file = os.path.join(RESOURCES_FOLDER, "kafka_source_invalid.yaml")

    with pytest.raises(UpcheckException):
        CheckSource.create_from_file(config_file)


@pytest.mark.anyio
async def test_source_create():

    config_file = os.path.join(RESOURCES_FOLDER, "kafka_incl_certs.yaml")

    source: KafkaSource = CheckSource.create_from_file(config_file)
    assert isinstance(source, CheckSource)
    assert isinstance(source, KafkaSource)

    assert source._client._consumer is None

    try:
        await source.connect()
    except UpcheckException as ue:
        assert "Can't create security context for kafka" in ue.msg
        # we ignore this test, since we assume this runs in CI and CI is not setup yet
        # to handle those secrets
        return

    assert source._client._consumer is not None
