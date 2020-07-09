#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for upcheck.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""
import uuid

import pytest
from upcheck.utils.aiven import UpcheckAivenClient


@pytest.fixture
def kafka_client():

    password = "OoIUcdmxRi3wl2AmIXt3HgkHWTnC9l0OakKuWHqefGrUDLO8+1OaKpufvpMklJRY5cZsqKZ+DAMoQMFeep0l6xrtH2F3kY6Djx2LmTcqyx819YG8ptR81LcvCm4+INvG+7+0GfW5ralmhTH99XYYQlHgBCbNVQDCdryKNKMz29lmNYqGE8bKBAYvHu+juZ98BlXEpJMfyxp6OyERZ4r+ky/O0OCjXSBVsuooHusrQRDsmVYumWh2C68gBDgeEDmxACaa5LNbU5dw9W9Zx/eJreW1QhCHVqs/NqvVrEGVArLWqQmFY7IywS3pDb1XwsF9S0rl6W2qXnP92XdYfGRB/uvqMeBsfdXzB8hmUD9CRrY="

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
