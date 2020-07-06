# -*- coding: utf-8 -*-
import collections
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from ssl import SSLContext
from typing import Optional, Union

import aiopg
from aiopg import Connection, Cursor
from ruamel.yaml import YAML
from upcheck.exceptions import UpcheckException
from upcheck.url_check import CheckMetric


class CheckTarget(metaclass=ABCMeta):
    @classmethod
    def load_from_file(cls, path: Union[str, Path]):

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

        if not isinstance(content, collections.abc.Mapping):
            raise UpcheckException(
                msg=f"Can't load target config '{path.as_posix()}'.",
                reason="File content must be dictionary.",
            )

        target_type = "postgres"
        try:
            target = PostgresTarget(**content)
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
    async def write(self, *results: CheckMetric) -> None:
        pass


class PostgresTarget(CheckTarget):
    def __init__(
        self,
        username: str,
        password: str,
        dbname: str,
        host: str = "localhost",
        port: int = 5432,
        ssl: Union[SSLContext, bool, None] = None,
    ):

        self._username: str = username
        self._password: str = password
        self._dbname: str = dbname
        self._host: str = host
        self._port: int = port
        self._ssl: Union[SSLContext, bool, None] = ssl

        self._connection: Optional[Connection] = None
        self._cursor: Optional[Cursor] = None

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def database(self) -> str:
        return self._dbname

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def ssl(self) -> Union[SSLContext, bool, None]:
        return self._ssl

    async def connect(self) -> Connection:

        if self._connection is not None:
            raise UpcheckException(
                msg="Can't connect to database.",
                reason="Connection already established.",
            )

        try:
            self._connection = await aiopg.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                dbname=self.database,
                # sslmode="require",
            )
        except Exception as e:
            raise UpcheckException(msg="Can't connect to database.", reason=str(e))

        return self._connection

    async def disconnect(self) -> None:

        if self._connection is not None:
            await self._connection.close()

    async def cursor(self):

        if self._cursor is None:
            if self._connection is None:
                await self.connect()
            self._cursor = await self._connection.cursor()
        return self._cursor

    async def _insert(self, query: str, args) -> None:

        cur = await self.cursor()
        await cur.execute(query, args)

    async def write(self, *results: CheckMetric) -> None:

        # TODO: could use arrays for more efficient batch inserts, but probably not worth it at this stage
        for result in results:
            query = """
            INSERT INTO check_results (url, regex, start_time, response_time_ms, response_code, regex_match) VALUES(%s, %s, %s, %s, %s, %s)"""
            args = (
                result.url_check.url,
                result.url_check.regex,
                result.start_time,
                result.response_time,
                result.response_code,
                result.regex_matched,
            )

            await self._insert(query, args)
