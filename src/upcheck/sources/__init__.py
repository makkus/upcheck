# -*- coding: utf-8 -*-
import collections
import logging
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import AsyncIterator, Iterable, Optional, Union

from ruamel.yaml import YAML
from upcheck.exceptions import UpcheckException
from upcheck.models import CheckResult


log = logging.getLogger("upcheck")

AVAILABLE_SOURCE_TYPES = ["kafka"]


class CheckSource(metaclass=ABCMeta):
    @classmethod
    def create_from_file(cls, path: Union[str, Path], force_source_type: Optional[str]):

        if isinstance(path, str):
            path = Path(os.path.expanduser(path))

        if not path.exists():
            raise UpcheckException(
                msg=f"Can't load source config '{path}'", reason="File does not exist"
            )

        try:
            yaml = YAML()
            content = yaml.load(path)
        except Exception as e:
            raise UpcheckException(
                msg=f"Can't load source config '{path.as_posix()}'.",
                reason="File content not valid yaml.",
                parent=e,
            )

        if not isinstance(content, collections.abc.MutableMapping):
            raise UpcheckException(
                msg=f"Can't load source config '{path.as_posix()}'.",
                reason="File content must be dictionary.",
            )

        source_type: str = content.pop("type", "kafka")
        if force_source_type:
            if force_source_type != source_type:
                raise UpcheckException(
                    msg=f"Can't create source of type '{force_source_type}' from config '{path}'.",
                    reason=f"Invalid source type '{source_type}' specified.",
                )
            source_type = source_type

        if source_type is None:
            raise UpcheckException(
                msg=f"Can't create source from file '{path}'",
                reason="No 'type' key specified.",
                solution=f"Add a key 'type' with a value from: {', '.join(AVAILABLE_SOURCE_TYPES)}",
            )

        try:
            if source_type == "kafka":

                from upcheck.sources.kafka import KafkaSource

                target = KafkaSource(**content)
            else:
                raise UpcheckException(
                    msg=f"Can't create source from file '{path}'",
                    reason=f"Invalid source type '{source_type}'",
                    solution=f"Use a valid 'source_type' value (one of: {', '.join(AVAILABLE_SOURCE_TYPES)}).",
                )

            log.debug(f"Created source of type '{source_type}': {target.get_id()}")

        except Exception as e:
            raise UpcheckException(
                msg=f"Can't load source config '{path.as_posix()}'.",
                reason=f"Invalid config for source type '{source_type}: {e}",
            )
        return target

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    async def start(self) -> AsyncIterator[CheckResult]:
        pass

    async def stop(self) -> Optional[Iterable[CheckResult]]:
        return None

    def __repr__(self):
        return f"({self.__class__.__name__}: id={self.get_id()}"
