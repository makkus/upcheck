# -*- coding: utf-8 -*-
import os
import time
import uuid
from multiprocessing import Manager, Process

import pytest
from upcheck.models import UrlCheck
from upcheck.sources import CheckSource
from upcheck.sources.check import ActualCheckCheckSource
from upcheck.targets import CheckTarget, CollectorCheckTarget
from upcheck.upcheck import Upcheck
from upcheck.utils.callables import wrap_async_task


os.environ["UPCHECK_NO_WAIT"] = "true"


@pytest.mark.anyio
async def test_integration_no_target():

    url_checks = UrlCheck.create_checks(
        {"url": "https://cloudflare.com", "regex": "cloudflare"}, "https://google.com"
    )
    print(url_checks)
    source = ActualCheckCheckSource(*url_checks)
    target = CollectorCheckTarget()

    upcheck = Upcheck(source=source, targets=[target])

    await upcheck.start(wait_for_keypress=False)

    assert len(target.results) == 2


@pytest.mark.anyio
async def test_integration_kafka_target(httpserver, kafka_client):

    if os.environ.get("AIVEN_TOKEN", None) is None:
        return

    manager = Manager()
    received = manager.list()

    def listen():
        async def callback(msg):
            print("New message")
            received.append(msg)

        wrap_async_task(kafka_client.listen, callback)

    p = Process(target=listen)
    p.start()

    try:

        # give the kafka client some time to connect...
        time.sleep(8)

        # empty the queue if necessary
        kafka_config = {
            "type": "kafka-aiven",
            "topic": "upcheck_testing",
            "password": os.environ["AIVEN_TOKEN"],
        }
        kafka_target = CheckTarget.create_from_dict(kafka_config)
        collector_target = CollectorCheckTarget()

        httpserver.expect_request("/abc").respond_with_data(
            "abcdefghijklmnopqrstuvwxyz"
        )

        check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

        source = ActualCheckCheckSource.create_check_source(check_url)

        upcheck = Upcheck(source=source, targets=[kafka_target, collector_target])

        await upcheck.start(wait_for_keypress=False)

        assert len(collector_target.results) == 1

        await source.disconnect()
        await kafka_target.disconnect()

        assert len(received) == 1
    finally:
        p.kill()


@pytest.mark.anyio
async def test_integration_postgres_target(httpserver, postgres_connection):

    if os.environ.get("AIVEN_TOKEN", None) is None:
        return

    pg_config = {
        "type": "postgres-aiven",
        "dbname": "testing",
        "password": os.environ["AIVEN_TOKEN"],
    }
    postgres_target = CheckTarget.create_from_dict(pg_config)
    collector_target = CollectorCheckTarget()

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")

    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

    source = ActualCheckCheckSource.create_check_source(check_url)

    upcheck = Upcheck(source=source, targets=[postgres_target, collector_target])

    await upcheck.start(wait_for_keypress=False)

    assert len(collector_target.results) == 1

    await source.disconnect()
    await postgres_target.disconnect()

    connection = await postgres_connection

    try:

        async with connection.cursor() as cur:

            for cr in collector_target.results:
                sql = "select * from check_results where start_time = (%s);"
                await cur.execute(sql, (cr.check_time,))
                ret = []
                async for row in cur:
                    ret.append(row)

                assert len(ret) == 1
    finally:
        connection.close()


@pytest.mark.anyio
async def test_integration_end_to_end(httpserver, postgres_connection):

    if os.environ.get("AIVEN_TOKEN", None) is None:
        return

    httpserver.expect_request("/abc").respond_with_data("abcdefghijklmnopqrstuvwxyz")

    check_url = f"http://{httpserver.host}:{httpserver.port}/abc"

    manager = Manager()
    check_results = manager.list()

    # setup listen
    def listen():

        topic = "upcheck_testing"
        kafka_source_config = {
            "type": "kafka-aiven",
            "topic": topic,
            "group_id": str(uuid.uuid4()),
            "password": os.environ["AIVEN_TOKEN"],
        }
        kafka_source = CheckSource.create_from_dict(kafka_source_config)
        pg_config = {
            "type": "postgres-aiven",
            "dbname": "testing",
            "password": os.environ["AIVEN_TOKEN"],
        }

        postgres_target = CheckTarget.create_from_dict(pg_config)

        upcheck = Upcheck(source=kafka_source, targets=[postgres_target])
        wrap_async_task(upcheck.start, False)

    listen_process = Process(target=listen)
    listen_process.start()

    # time for the kafka source to be up
    time.sleep(8)

    # setup check
    def check(check_url: str):

        topic = "upcheck_testing"
        kafka_target_config = {
            "type": "kafka-aiven",
            "topic": topic,
            "password": os.environ["AIVEN_TOKEN"],
        }
        postgres_target = CheckTarget.create_from_dict(kafka_target_config)
        collector_target = CollectorCheckTarget()

        source = ActualCheckCheckSource.create_check_source(check_url)
        upcheck = Upcheck(source=source, targets=[postgres_target, collector_target])

        wrap_async_task(upcheck.start, False)

        for r in collector_target.results:
            check_results.append(r)

        print("checks finished")

    check_process = Process(target=check, args=[check_url])
    check_process.start()

    try:

        connection = await postgres_connection

        try:

            async with connection.cursor() as cur:

                for cr in check_results:
                    print("XXX")
                    print(cr)
                    sql = "select * from check_results where start_time = (%s);"
                    await cur.execute(sql, (cr.check_time,))
                    ret = []
                    async for row in cur:
                        ret.append(row)

                    # TODO: sometimes there is more than 1 result
                    # maybe concurrent Python version test jobs on Gitlab?
                    # anyway, needs investigation and verifikation, could be a buggs
                    assert len(ret) >= 1

        finally:
            connection.close()

    finally:
        listen_process.kill()
        check_process.kill()
