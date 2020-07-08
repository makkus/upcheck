# -*- coding: utf-8 -*-
import io
from typing import Optional

import avro.schema
from avro.io import DatumWriter
from upcheck.models import CheckMetric
from upcheck.targets import CheckTarget
from upcheck.utils.kafka import CHECK_METRIC_SCHEMA, UpcheckKafkaClient


CHECK_METRIC_WRITER = DatumWriter(CHECK_METRIC_SCHEMA)


class KafkaTarget(CheckTarget):
    def __init__(
        self,
        host: str,
        port: int,
        topic: str,
        cafile: Optional[str] = None,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
    ):

        self._client = UpcheckKafkaClient(
            host=host,
            port=port,
            topic=topic,
            cafile=cafile,
            certfile=certfile,
            keyfile=keyfile,
        )

    def get_id(self) -> str:

        return f"kafka::{self._client.host}:{self._client.port}/{self._client.topic}"

    async def connect(self) -> None:

        await self._client.connect_producer()

    async def disconnect(self) -> None:

        await self._client.disconnect_producer()

    async def write(self, *results: CheckMetric) -> None:

        producer = await self._client.get_producer()

        for result in results:

            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)

            # we need to convert the start time to a string
            # since datetime is not natively supported
            data = dict(result.report_data)
            data["check_time"] = str(data["check_time"])

            if data["regex"] is None:
                data.pop("regex")
            if data["regex_matched"] is None:
                data.pop("regex_matched")

            CHECK_METRIC_WRITER.write(data, encoder)

            bytes = bytes_writer.getvalue()

            await producer.send_and_wait(self._client.topic, bytes, partition=0)
