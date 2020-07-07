# -*- coding: utf-8 -*-
import io
import logging
from typing import Any, Mapping, Optional

import avro
from avro.io import DatumReader
from upcheck.kafka import CHECK_METRIC_SCHEMA, UpcheckKafkaClient
from upcheck.sources import CheckSource
from upcheck.targets import CheckTarget
from upcheck.url_check import CheckMetric


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

    async def _start(self, *targets: CheckTarget) -> None:

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
                metric: CheckMetric = CheckMetric.from_dict(data)
            except Exception as e:
                log.error(f"Error parsing message: {e}")
                continue

            for _t in targets:
                log.debug(f"Write metric to target: {_t.get_id()}")
                try:
                    await _t.write(metric)
                except Exception as e:
                    log.error(f"Can't write metric to target '{_t.get_id()}': {e}")

    async def _stop(self) -> None:
        pass
