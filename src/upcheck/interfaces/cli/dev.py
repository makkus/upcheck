# -*- coding: utf-8 -*-
"""Only used in development, ignore."""

import os

import asyncclick as click
from upcheck.interfaces.cli.main import command, handle_exc
from upcheck.utils.aiven import UpcheckAivenClient


# flake8: noqa


@command.group(short_help="development related commands")
@click.pass_context
@handle_exc
async def dev(ctx):

    pass


@dev.command()
@click.pass_context
async def kafka(ctx):

    password = os.environ["AIVEN_TOKEN"]

    project_name = None
    kafka_service_name = None

    topic = "check_metrics"
    group_id = "dev2"

    aiven_client: UpcheckAivenClient = UpcheckAivenClient(
        token_or_account_password=password
    )

    # kafka_client = aiven_client.create_kafka_client(
    #     topic=topic,
    #     group_id=group_id,
    #     project_name=project_name,
    #     service_name=kafka_service_name,
    # )
    # # consumer = await kafka_client.get_consumer()
    #
    # # offsets = await consumer.beginning_offsets([TopicPartition('check_metrics', 0)])
    # # print(offsets)
    # # async for msg in consumer:
    # #     print("consumed: ", msg.topic, msg.partition, msg.offset,
    # #               msg.key, msg.value, msg.timestamp)
    #
    # async def callback(msg):
    #     print(msg)
    #
    # await kafka_client.listen(callback)
    #
    # await kafka_client.disconnect_consumer()

    connection = await aiven_client.create_postgres_connection("defaultdb")
    print(connection)

    async with connection.cursor() as cur:
        await cur.execute("select * from check_results")
        ret = []
        async for row in cur:
            ret.append(row)

        print(ret)

    connection.close()
