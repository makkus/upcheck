# -*- coding: utf-8 -*-
import logging
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Mapping, Optional, Union

import anyio
from avro.io import DatumReader
from upcheck.models import CheckResult, UrlCheck
from upcheck.sources import CheckSource
from upcheck.utils.kafka import CHECK_METRIC_SCHEMA


CHECK_METRIC_READER = DatumReader(CHECK_METRIC_SCHEMA)

log = logging.getLogger("upcheck")


class ActualCheckCheckSource(CheckSource):
    @classmethod
    def create_check_source(
        cls,
        *url_or_config_file_paths: Union[Path, str, Mapping[str, Any]],
        repeat: Optional[int] = None,
        id: Optional[str] = None
    ) -> "ActualCheckCheckSource":

        url_checks: Iterable[UrlCheck] = UrlCheck.create_checks(
            *url_or_config_file_paths
        )
        cs = ActualCheckCheckSource(*url_checks, repeat=repeat, id=id)
        return cs

    def __init__(
        self,
        *url_checks: UrlCheck,
        repeat: Optional[int] = None,
        id: Optional[str] = None
    ):

        if id is None:
            id = str(uuid.uuid4())
        self._id: str = id
        self._url_checks: Iterable[UrlCheck] = url_checks
        if repeat is None or repeat < 0:
            repeat = 0
        self._repeat: int = repeat

    @property
    def repeat(self) -> int:
        return self._repeat

    @repeat.setter
    def repeat(self, repeat: int) -> None:
        if not repeat or repeat < 0:
            repeat = 0
        self._repeat = repeat

    def get_id(self) -> str:

        return self._id

    async def start(self) -> AsyncIterator[CheckResult]:  # type: ignore

        if self._repeat <= 0:
            for check in self._url_checks:
                result = await check.perform_check()
                yield result
            return

        while True:
            for check in self._url_checks:
                result = await check.perform_check()
                yield result
            await anyio.sleep(self._repeat)
        return
