#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for upcheck.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""
import os
import uuid

import pytest
from upcheck.utils.aiven import UpcheckAivenClient


@pytest.fixture
def kafka_client():

    password = os.environ.get("AIVEN_TOKEN", None)
    if password is None:
        return None

    os.environ["UPCHECK_NO_WAIT"] = "true"

    run_integration_tests = (
        True
        if os.environ.get("RUN_INTEGRATION_TESTS", "false").lower() == "true"
        else False
    )

    run_integration_tests = False

    if not run_integration_tests:
        return None

    project_name = None
    kafka_service_name = None

    topic = "upcheck_testing"
    # group_id = "testing"
    group_id = str(uuid.uuid4())

    aiven_client: UpcheckAivenClient = UpcheckAivenClient(
        token_or_account_password=password
    )

    kafka_client = aiven_client.create_kafka_client(
        topic=topic,
        group_id=group_id,
        project_name=project_name,
        service_name=kafka_service_name,
    )

    return kafka_client


@pytest.fixture
async def postgres_connection():

    password = os.environ.get("AIVEN_TOKEN", None)
    if password is None:
        return None

    run_integration_tests = (
        True
        if os.environ.get("RUN_INTEGRATION_TESTS", "false").lower() == "true"
        else False
    )

    run_integration_tests = False

    if not run_integration_tests:
        return None

    project_name = None
    postgres_service_name = None

    dbname = "testing"

    aiven_client: UpcheckAivenClient = UpcheckAivenClient(
        token_or_account_password=password
    )

    connection = aiven_client.create_postgres_connection(
        dbname, project_name=project_name, service_name=postgres_service_name
    )
    return connection
