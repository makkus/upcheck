# -*- coding: utf-8 -*-
import os
from ssl import SSLContext
from typing import Optional

import avro.schema
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.helpers import create_ssl_context
from upcheck.defaults import DEFAULT_KAFKA_GROUP_ID, UPCHECK_RESOURCES_FOLDER
from upcheck.exceptions import UpcheckException


CHECK_METRIC_SCHEMA_FILE = os.path.join(UPCHECK_RESOURCES_FOLDER, "check_metric.avsc")
CHECK_METRIC_SCHEMA = avro.schema.parse(open(CHECK_METRIC_SCHEMA_FILE, "rb").read())


class UpcheckKafkaClient(object):
    """Wrapper class for Kafka client functionality, used in both Kafka source and target."""

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

        self._host = host
        self._port = port
        self._topic: str = topic
        if group_id is None:
            group_id = DEFAULT_KAFKA_GROUP_ID
        self._group_id: str = group_id

        self._security_protocol: str = "SSL"

        self._cafile: Optional[str] = cafile
        self._certfile: Optional[str] = certfile
        self._keyfile: Optional[str] = keyfile

        self._ssl_context: Optional[SSLContext] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def topic(self) -> str:
        return self._topic

    def _get_ssl_context(self) -> Optional[SSLContext]:

        if self._ssl_context is None and (
            self._cafile or self._certfile or self._keyfile
        ):
            try:
                self._ssl_context = create_ssl_context(
                    cafile=self._cafile, certfile=self._certfile, keyfile=self._keyfile
                )
            except Exception as e:
                raise UpcheckException(
                    msg="Can't create security context for kafka.",
                    reason=str(e),
                    solution="Please check the relevant properties in your kafka target configuration.",
                )
        return self._ssl_context

    def get_id(self) -> str:

        return f"kafka::{self._host}:{self._port}/{self._topic}"

    async def connect_producer(self) -> None:

        if self._producer is not None:
            raise UpcheckException(
                "Can't connect to producer.", reason="Producer already exists."
            )

        self._producer = AIOKafkaProducer(
            bootstrap_servers=f"{self._host}:{self._port}",
            security_protocol=self._security_protocol,
            ssl_context=self._get_ssl_context(),
        )
        await self._producer.start()

    async def disconnect_producer(self) -> None:

        if self._producer is not None:
            await self._producer.stop()

    async def get_producer(self):

        if self._producer is None:
            await self.connect_producer()
        return self._producer

    async def connect_consumer(self) -> None:

        if self._consumer is not None:
            raise UpcheckException(
                "Can't connect to producer.", reason="Producer already exists."
            )
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=f"{self._host}:{self._port}",
            group_id=self._group_id,
            security_protocol=self._security_protocol,
            ssl_context=self._get_ssl_context(),
        )
        await self._consumer.start()

    async def disconnect_consumer(self):

        if self._consumer is not None:
            await self._consumer.stop()

    async def get_consumer(self) -> AIOKafkaConsumer:

        if self._consumer is None:
            await self.connect_consumer()
        return self._consumer
