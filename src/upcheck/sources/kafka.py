# -*- coding: utf-8 -*-
import io
import logging
import os
from typing import Any, AsyncIterator, Mapping, Optional

import avro
from avro.io import DatumReader
from upcheck.models import CheckMetric, CheckResult
from upcheck.sources import CheckSource
from upcheck.utils import create_temp_dir_with_text_files
from upcheck.utils.aiven import UpcheckAivenClient
from upcheck.utils.kafka import CHECK_METRIC_SCHEMA, UpcheckKafkaClient


CHECK_METRIC_READER = DatumReader(CHECK_METRIC_SCHEMA)

log = logging.getLogger("upcheck")


class KafkaSource(CheckSource):
    """Source to consume check results from a Kafka topic.

    Args:
        hsot (str): the host that runs the Kafka service
        port (int): the port on which Kafka listens
        topic (str): the topic to send check results to
        group_id (str): the group id of the Kafka consumer
        cafile (str): path to a ca file
        certfile (str): path to a cert file
        keyfile (str): path to a key file
    """

    def __init__(
        self,
        host: str,
        port: int,
        topic: str,
        group_id: Optional[str] = None,
        cafile: Optional[str] = None,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
    ):

        # TODO: lazy initialization, on demand
        self._client: UpcheckKafkaClient = UpcheckKafkaClient(
            host=host,
            port=port,
            topic=topic,
            group_id=group_id,
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
        try:
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

        finally:
            await consumer.stop()

        return


class AivenKafkaSoure(KafkaSource):
    """Convenience source class to not have to provide most of the Kafka config values manually.

    Only useful if using the Aiven service.

    Args:
        topic (str): the topic to send check results to
        password (str): the password of the Aiven account (if also providing the 'email' value), or an authentication token
        email (str): optional account email
        group_id (str): the group id of the Kafka consumer
        project_name (str): the name of the  aiven project to use
        service_name (str): the name of the Kafka service to use

    """

    def __init__(
        self,
        topic: str,
        password: str,
        email: Optional[str] = None,
        group_id: Optional[str] = None,
        project_name: Optional[str] = None,
        service_name: Optional[str] = None,
    ):

        # TODO: lazy initialization, on demand
        self._aiven_client: UpcheckAivenClient = UpcheckAivenClient(
            token_or_account_password=password, email=email
        )
        self._kafka_service_details: Mapping[
            str, Any
        ] = self._aiven_client.get_kafka_service_details(
            project_name=project_name, service_name=service_name
        )

        ca_cert = self._kafka_service_details["ca_cert"]
        access_cert = self._kafka_service_details["access_cert"]
        access_key = self._kafka_service_details["access_key"]

        temp_dir = create_temp_dir_with_text_files(
            {"ca.pem": ca_cert, "service.cert": access_cert, "service.key": access_key}
        )

        kafka_source_config = {
            "host": self._kafka_service_details["host"],
            "port": self._kafka_service_details["port"],
            "topic": topic,
            "group_id": group_id,
            "cafile": os.path.join(temp_dir, "ca.pem"),
            "certfile": os.path.join(temp_dir, "service.cert"),
            "keyfile": os.path.join(temp_dir, "service.key"),
        }

        super().__init__(**kafka_source_config)
