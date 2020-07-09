# -*- coding: utf-8 -*-
import asyncclick as click
from upcheck.interfaces.cli.main import command, handle_exc
from upcheck.utils.aiven import UpcheckAivenClient


@command.group(short_help="development related commands")
@click.pass_context
@handle_exc
async def dev(ctx):

    pass


@dev.command()
@click.pass_context
async def kafka(ctx):

    password = "OoIUcdmxRi3wl2AmIXt3HgkHWTnC9l0OakKuWHqefGrUDLO8+1OaKpufvpMklJRY5cZsqKZ+DAMoQMFeep0l6xrtH2F3kY6Djx2LmTcqyx819YG8ptR81LcvCm4+INvG+7+0GfW5ralmhTH99XYYQlHgBCbNVQDCdryKNKMz29lmNYqGE8bKBAYvHu+juZ98BlXEpJMfyxp6OyERZ4r+ky/O0OCjXSBVsuooHusrQRDsmVYumWh2C68gBDgeEDmxACaa5LNbU5dw9W9Zx/eJreW1QhCHVqs/NqvVrEGVArLWqQmFY7IywS3pDb1XwsF9S0rl6W2qXnP92XdYfGRB/uvqMeBsfdXzB8hmUD9CRrY="

    project_name = None
    kafka_service_name = None

    topic = "check_metrics"
    group_id = "dev2"

    aiven_client: UpcheckAivenClient = UpcheckAivenClient(
        token_or_account_password=password
    )

    kafka_client = aiven_client.create_kafka_client(
        topic=topic,
        group_id=group_id,
        project_name=project_name,
        service_name=kafka_service_name,
    )
    # consumer = await kafka_client.get_consumer()

    # offsets = await consumer.beginning_offsets([TopicPartition('check_metrics', 0)])
    # print(offsets)
    # async for msg in consumer:
    #     print("consumed: ", msg.topic, msg.partition, msg.offset,
    #               msg.key, msg.value, msg.timestamp)

    async def callback(msg):
        print(msg)

    await kafka_client.listen(callback)

    await kafka_client.disconnect_consumer()

    # connection = await aiven_client.create_postgres_connection("defaultdb")
    # print(connection)
    #
    # async with connection.cursor() as cur:
    #     await cur.execute("select * from check_results")
    #     ret = []
    #     async for row in cur:
    #         ret.append(row)
    #
    #     print(ret)
    #
    # connection.close()
