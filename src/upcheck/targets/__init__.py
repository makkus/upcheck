# -*- coding: utf-8 -*-
import collections
import logging
import os
import uuid
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, List, MutableMapping, Optional, Union

from ruamel.yaml import YAML
from upcheck.exceptions import UpcheckException
from upcheck.models import CheckMetric


log = logging.getLogger("upcheck")

AVAILABLE_TARGET_TYPES = ["kafka", "postgres", "kafka-aiven", "postgres-aiven"]


class CheckTarget(metaclass=ABCMeta):
    """A check target is an object that consumes 'CheckResult's.

    The main reason to have an abstract base class here is to enable very flexible plumbing of sources and targets,
    as well as share code for configuration, as well as enable easy addition of new source types.
    """

    @classmethod
    def create_from_file(cls, path: Union[str, Path]):
        """Create a target from a (yaml) file.

        Args:
            path: the path to the target config

        Returns:
            CheckTarget: the target object
        """
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

        return cls.create_from_dict(target_config=content)

    @classmethod
    def create_from_dict(cls, target_config: MutableMapping[str, Any]):
        """Create a target from a dict.

        Args:
            target_config: the configuration for the target

        Returns:
            CheckTarget: the target object
        """
        target_type = target_config.pop("type", None)
        if target_type is None:
            raise UpcheckException(
                msg="Can't create target.",
                reason="No 'type' key specified.",
                solution=f"Add a key 'type' with a value from: {', '.join(AVAILABLE_TARGET_TYPES)}",
            )

        try:
            if target_type == "postgres":

                from upcheck.targets.postgres import PostgresTarget

                target: CheckTarget = PostgresTarget(**target_config)

            elif target_type == "postgres-aiven":

                from upcheck.targets.postgres import AivenPostgresTarget

                target = AivenPostgresTarget(**target_config)

            elif target_type == "kafka":

                from upcheck.targets.kafka import KafkaTarget

                target = KafkaTarget(**target_config)

            elif target_type == "kafka-aiven":

                from upcheck.targets.kafka import AivenKafkaTarget

                target = AivenKafkaTarget(**target_config)

            else:
                raise UpcheckException(
                    msg="Can't create target.",
                    reason=f"Invalid target type '{target_type}'",
                    solution=f"Use a valid 'target_type' value (one of: {', '.join(AVAILABLE_TARGET_TYPES)}).",
                )

            log.debug(f"Created target of type '{target_type}': {target.get_id()}")

        except Exception as e:
            raise UpcheckException(
                msg="Can't load target config.",
                reason=f"Invalid config for target type '{target_type}: {e}",
            )
        return target

    async def connect(self) -> None:
        """Connect the target."""
        pass

    async def disconnect(self) -> None:
        """Disconnect the target."""
        pass

    @abstractmethod
    def get_id(self) -> str:
        """The internal id of the target.

        Should be unique across the application invocation.
        """
        pass

    @abstractmethod
    async def write(self, *results: CheckMetric) -> None:
        """Write a result to this target."""
        pass

    def __repr__(self):
        return f"({self.__class__.__name__}: id={self.get_id()}"


class CollectorCheckTarget(CheckTarget):
    """Target to collect results.

    This is mainly used in testing, but can also be used to hold test results in memory for other reasons.
    """

    def __init__(self, id: Optional[str] = None):

        if id is None:
            id = str(uuid.uuid4())
        self._id = id
        self._results: List[CheckMetric] = []

    def get_id(self) -> str:
        return self._id

    async def write(self, *results: CheckMetric) -> None:

        self._results.extend(results)

    @property
    def results(self) -> List[CheckMetric]:
        return self._results
