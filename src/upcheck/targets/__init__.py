# -*- coding: utf-8 -*-
import collections
import logging
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Union

from ruamel.yaml import YAML
from upcheck.exceptions import UpcheckException
from upcheck.url_check import CheckMetric


log = logging.getLogger("upcheck")

AVAILABLE_TARGET_TYPES = ["kafka", "postgres"]


class CheckTarget(metaclass=ABCMeta):
    @classmethod
    def create_from_file(cls, path: Union[str, Path]):

        if isinstance(path, str):
            path = Path(os.path.expanduser(path))

        if not path.exists():
            raise UpcheckException(
                msg=f"Can't load target config '{path}'", reason="File does not exist"
            )

        try:
            yaml = YAML()
            content = yaml.load(path)
        except Exception as e:
            raise UpcheckException(
                msg=f"Can't load target config '{path.as_posix()}'.",
                reason="File content not valid yaml.",
                parent=e,
            )

        if not isinstance(content, collections.abc.MutableMapping):
            raise UpcheckException(
                msg=f"Can't load target config '{path.as_posix()}'.",
                reason="File content must be dictionary.",
            )

        target_type = content.pop("type", None)
        if target_type is None:
            raise UpcheckException(
                msg=f"Can't create target from file '{path}'",
                reason="No 'type' key specified.",
                solution=f"Add a key 'type' with a value from: {', '.join(AVAILABLE_TARGET_TYPES)}",
            )

        try:
            if target_type == "postgres":

                from upcheck.targets.postgres import PostgresTarget

                target: CheckTarget = PostgresTarget(**content)

            elif target_type == "kafka":

                from upcheck.targets.kafka import KafkaTarget

                target = KafkaTarget(**content)
            else:
                raise UpcheckException(
                    msg=f"Can't create target from file '{path}'",
                    reason=f"Invalid target type '{target_type}'",
                    solution=f"Use a valid 'target_type' value (one of: {', '.join(AVAILABLE_TARGET_TYPES)}).",
                )

            log.debug(f"Created target of type '{target_type}': {target.get_id()}")

        except Exception as e:
            raise UpcheckException(
                msg=f"Can't load target config '{path.as_posix()}'.",
                reason=f"Invalid config for target type '{target_type}: {e}",
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
    async def write(self, *results: CheckMetric) -> None:
        pass

    def __repr__(self):
        return f"({self.__class__.__name__}: id={self.get_id()}"
