# -*- coding: utf-8 -*-
import io
import os
from typing import Any, Mapping, Optional

import avro.schema
from avro.io import DatumWriter
from upcheck.models import CheckMetric
from upcheck.targets import CheckTarget
from upcheck.utils import create_temp_dir_with_text_files
from upcheck.utils.aiven import UpcheckAivenClient
from upcheck.utils.kafka import CHECK_METRIC_SCHEMA, UpcheckKafkaClient


CHECK_METRIC_WRITER = DatumWriter(CHECK_METRIC_SCHEMA)


class KafkaTarget(CheckTarget):
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

        self._client = UpcheckKafkaClient(
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


class AivenKafkaTarget(KafkaTarget):
    def __init__(
        self,
        topic: str,
        password: str,
        email: Optional[str] = None,
        project_name: Optional[str] = None,
        group_id: Optional[str] = None,
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

        kafka_target_config = {
            "host": self._kafka_service_details["host"],
            "port": self._kafka_service_details["port"],
            "topic": topic,
            "group_id": group_id,
            "cafile": os.path.join(temp_dir, "ca.pem"),
            "certfile": os.path.join(temp_dir, "service.cert"),
            "keyfile": os.path.join(temp_dir, "service.key"),
        }

        super().__init__(**kafka_target_config)
