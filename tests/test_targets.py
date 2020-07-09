# -*- coding: utf-8 -*-
import os

import pytest
from upcheck.exceptions import UpcheckException
from upcheck.targets import CheckTarget
from upcheck.targets.kafka import KafkaTarget
from upcheck.targets.postgres import PostgresTarget


RESOURCES_FOLDER = os.path.join(os.path.dirname(__file__), "resources")


def test_postgres_target_config():

    config_file = os.path.join(RESOURCES_FOLDER, "postgres_target.yaml")

    source = CheckTarget.create_from_file(config_file)
    assert isinstance(source, CheckTarget)
    assert isinstance(source, PostgresTarget)


def test_postgres_target_config_invalid():

    config_file = os.path.join(RESOURCES_FOLDER, "postgres_target_invalid.yaml")

    with pytest.raises(UpcheckException) as ue:
        CheckTarget.create_from_file(config_file)
        assert "No 'type' key" in ue.reason


def test_kafka_target_config():

    config_file = os.path.join(RESOURCES_FOLDER, "kafka_source.yaml")

    source = CheckTarget.create_from_file(config_file)
    assert isinstance(source, CheckTarget)
    assert isinstance(source, KafkaTarget)


def test_kafka_target_config_invalid():

    config_file = os.path.join(RESOURCES_FOLDER, "kafka_source_invalid.yaml")

    with pytest.raises(UpcheckException):
        CheckTarget.create_from_file(config_file)
