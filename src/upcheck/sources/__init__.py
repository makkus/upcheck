# -*- coding: utf-8 -*-
import collections
import logging
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, MutableMapping, Optional, Union

from ruamel.yaml import YAML
from upcheck.exceptions import UpcheckException
from upcheck.models import CheckResult


log = logging.getLogger("upcheck")

AVAILABLE_SOURCE_TYPES = ["kafka", "kafka-aiven"]


class CheckSource(metaclass=ABCMeta):
    """A check source is an object that emits 'CheckResult's.

    The main CheckSource class is the 'ActualCheckCheckSource', which performs checks against websites. The other
    currently implemented CheckSource class is KafkaCheckSource, which listens to Kafka topics for check result messages.

    The main reason to have an abstract base class here is to enable very flexible plumbing of sources and targets,
    as well as share code for configuration, as well as enable easy addition of new source types.
    """

    @classmethod
    def create_from_file(
        cls, path: Union[str, Path], force_source_type: Optional[str] = None
    ) -> "CheckSource":
        """Create a source from a (yaml) file.

        Args:
            path: the path to the source config
            force_source_type: (optionally) ensure that the config is of the specified type

        Returns:
            CheckSource: the CheckSource object
        """

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

        return cls.create_from_dict(
            source_config=content, force_source_type=force_source_type
        )

    @classmethod
    def create_from_dict(
        cls,
        source_config: MutableMapping[str, Any],
        force_source_type: Optional[str] = None,
    ):
        """Create a source from a dict.

        Args:
            source_config: the configuration dict
            force_source_type: (optionally) ensure that the config is of the specified type

        Returns:
            CheckSource: the CheckSource object
        """

        source_type: str = source_config.pop("type", "kafka")
        if force_source_type:
            if force_source_type != source_type:
                raise UpcheckException(
                    msg=f"Can't create source of type '{force_source_type}' from config.",
                    reason=f"Invalid source type specified: '{source_type}'",
                )
            source_type = source_type

        if source_type is None:
            raise UpcheckException(
                msg="Can't create source from config.",
                reason="No 'type' key specified.",
                solution=f"Add a key 'type' with a value from: {', '.join(AVAILABLE_SOURCE_TYPES)}",
            )

        try:
            if source_type == "kafka":

                from upcheck.sources.kafka import KafkaSource

                target = KafkaSource(**source_config)
            elif source_type == "kafka-aiven":

                from upcheck.sources.kafka import AivenKafkaSoure

                target = AivenKafkaSoure(**source_config)

            else:
                raise UpcheckException(
                    msg="Can't create source from config.",
                    reason=f"Invalid source type '{source_type}'",
                    solution=f"Use a valid 'source_type' value (one of: {', '.join(AVAILABLE_SOURCE_TYPES)}).",
                )

            log.debug(f"Created source of type '{source_type}': {target.get_id()}")

        except UpcheckException as ue:
            raise ue
        except Exception as e:
            raise UpcheckException(
                msg=f"Error creating source of type '{source_type}'.",
                reason=f"Invalid config for source type '{source_type}: {e}",
            )
        return target

    async def connect(self) -> None:
        """Connect the source."""
        pass

    async def disconnect(self) -> None:
        """Disconnect the source."""
        pass

    @abstractmethod
    def get_id(self) -> str:
        """The internal id of the source.

        Should be unique across the application invocation.
        """
        pass

    @abstractmethod
    async def start(self) -> AsyncIterator[CheckResult]:
        """Start the source.

        This should async-yield CheckResult items.
        """
        pass

    async def stop(self) -> Optional[Iterable[CheckResult]]:
        """Stop the source.

        Should return (if necessary) any check result items that haven't been 'yielded' by 'start'.
        """
        return None

    def __repr__(self):
        return f"({self.__class__.__name__}: id={self.get_id()}"
