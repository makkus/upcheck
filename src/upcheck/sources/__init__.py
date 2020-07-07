# -*- coding: utf-8 -*-
import collections
import logging
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Union

from ruamel.yaml import YAML
from upcheck.exceptions import UpcheckException
from upcheck.interfaces.cli.main import console
from upcheck.targets import CheckTarget
from upcheck.utils.callables import wait_for_tasks_or_user_keypress


log = logging.getLogger("upcheck")

AVAILABLE_SOURCE_TYPES = ["kafka"]


class CheckSource(metaclass=ABCMeta):
    @classmethod
    def create_from_file(cls, path: Union[str, Path]):

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

        source_type = content.pop("type", "kafka")
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

    async def start(self, *targets: CheckTarget) -> None:

        await wait_for_tasks_or_user_keypress(
            {"func": self._start, "args": targets}, console=console
        )

        await self._stop()

    @abstractmethod
    async def _start(self, *targets: CheckTarget) -> None:
        pass

    @abstractmethod
    async def _stop(self) -> None:
        pass

    def __repr__(self):
        return f"({self.__class__.__name__}: id={self.get_id()}"
