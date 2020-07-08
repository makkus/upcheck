# -*- coding: utf-8 -*-
import io
import logging
from typing import Any, AsyncIterator, Mapping, Optional

import avro
from avro.io import DatumReader
from upcheck.models import CheckMetric, CheckResult
from upcheck.sources import CheckSource
from upcheck.utils.kafka import CHECK_METRIC_SCHEMA, UpcheckKafkaClient


CHECK_METRIC_READER = DatumReader(CHECK_METRIC_SCHEMA)

log = logging.getLogger("upcheck")


class KafkaSource(CheckSource):
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

        await self._client.connect_consumer()

    async def disconnect(self) -> None:

        await self._client.disconnect_consumer()

    async def start(self) -> AsyncIterator[CheckResult]:  # type: ignore

        consumer = await self._client.get_consumer()

        async for msg in consumer:
            try:
                bytes_reader = io.BytesIO(msg.value)
                decoder = avro.io.BinaryDecoder(bytes_reader)
            except Exception as e:
                log.error(f"Error decoding msg: {e}")
                continue

            try:
                data: Mapping[str, Any] = CHECK_METRIC_READER.read(decoder)
                metric: CheckResult = CheckMetric.from_dict(data)
                yield metric
            except Exception as e:
                log.error(f"Error parsing message: {e}")
                continue

        return
