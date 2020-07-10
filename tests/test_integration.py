# -*- coding: utf-8 -*-
import os
import random
import string
import time
import uuid
from multiprocessing import Lock, Manager, Process

import anyio
import pytest
from upcheck.models import UrlCheck
from upcheck.sources import CheckSource
from upcheck.sources.check import ActualCheckCheckSource
from upcheck.targets import CheckTarget, CollectorCheckTarget
from upcheck.upcheck import Upcheck
from upcheck.utils.callables import wrap_async_task


os.environ["UPCHECK_NO_WAIT"] = "true"

run_integration_tests = (
    True
    if os.environ.get("RUN_INTEGRATION_TESTS", "false").lower() == "true"
    else False
)


@pytest.mark.anyio
async def test_integration_no_target():

    if not run_integration_tests:
        return

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

    # TODO: cleanup topic

    if not run_integration_tests:
        return

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

    # TODO: cleanup db

    if not run_integration_tests:
        return

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

    # TODO: cleanup topic & database

    if not run_integration_tests:
        return

    if os.environ.get("AIVEN_TOKEN", None) is None:
        return

    path = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

    httpserver.expect_request(f"/{path}").respond_with_data(
        "abcdefghijklmnopqrstuvwxyz"
    )

    check_url = f"http://{httpserver.host}:{httpserver.port}/{path}"

    manager = Manager()
    check_results = manager.list()

    lock = Lock()

    # setup listen
    def listen(lock: Lock):

        print("listen process acquiring lock")
        lock.acquire()  # type: ignore

        try:
            print("starting to listen to kafka...")

            topic = "upcheck_testing"
            kafka_source_config = {
                "type": "kafka-aiven",
                "topic": topic,
                "group_id": str(uuid.uuid4()),
                "password": os.environ["AIVEN_TOKEN"],
            }
            print("creating kafka source")
            kafka_source = CheckSource.create_from_dict(kafka_source_config)
            print("kafka source created")
            pg_config = {
                "type": "postgres-aiven",
                "dbname": "testing",
                "password": os.environ["AIVEN_TOKEN"],
            }
            print("creating postgres target")
            postgres_target = CheckTarget.create_from_dict(pg_config)
            print("postgres target created")

            upcheck = Upcheck(source=kafka_source, targets=[postgres_target])
            print("starting listening for kafka messages..")

            lock.release()  # type: ignore

            async def wrap():
                try:
                    await upcheck.connect()
                    await upcheck.start()
                finally:
                    await upcheck.disconnect()

            wrap_async_task(wrap, False)

        except Exception as e:
            print(e)
            raise e

    # setup check
    def check(check_url: str, lock: Lock):

        print("check process waiting for lock release...")
        lock.acquire()  # type: ignore

        print("starting checks...")
        try:

            topic = "upcheck_testing"
            kafka_target_config = {
                "type": "kafka-aiven",
                "topic": topic,
                "password": os.environ["AIVEN_TOKEN"],
            }
            print("creating kafka target...")
            kafka_target = CheckTarget.create_from_dict(kafka_target_config)
            print("kafka target created")
            collector_target = CollectorCheckTarget()

            source = ActualCheckCheckSource.create_check_source(check_url)
            upcheck = Upcheck(source=source, targets=[kafka_target, collector_target])

            print("starting checks...")

            async def wrap():
                try:
                    await upcheck.connect()
                    await upcheck.start()
                finally:
                    await upcheck.disconnect()

            wrap_async_task(wrap, False)
            print("checks finished")

            for r in collector_target.results:
                print(f"result added: {r}")
                check_results.append(r)

            print("checks finished")
        except Exception as e:
            print(e)
            raise e
        finally:
            lock.release()  # type: ignore

    listen_process = Process(target=listen, args=[lock])
    check_process = Process(target=check, args=[check_url, lock])
    listen_process.start()
    await anyio.sleep(1)
    check_process.start()

    check_process.join()

    try:
        print("checks finished")
        print("Results:")
        print(check_results)

        assert len(check_results) == 1
        print("establishing connection to postgres")
        connection = await postgres_connection

        try:

            async with connection.cursor() as cur:

                for cr in check_results:
                    print("querying results")
                    sql = "select * from check_results where start_time = (%s) and url = (%s);"
                    await cur.execute(sql, (cr.check_time, cr.url_check.url))
                    ret = []
                    async for row in cur:
                        ret.append(row)

                    print("Results in database:")
                    print(ret)

                    assert len(ret) == 1
        finally:
            connection.close()

    finally:
        try:
            listen_process.kill()
        except Exception:
            pass
