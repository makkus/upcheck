# -*- coding: utf-8 -*-
import os
from typing import Any, Mapping, Optional

import aiopg
from aiopg import Connection, Pool
from upcheck.exceptions import UpcheckException
from upcheck.models import CheckMetric
from upcheck.targets import CheckTarget
from upcheck.utils import create_temp_dir_with_text_files
from upcheck.utils.aiven import UpcheckAivenClient


class PostgresTarget(CheckTarget):
    def __init__(
        self,
        username: str,
        password: str,
        dbname: str,
        host: str = "localhost",
        port: int = 5432,
        sslmode: Optional[str] = None,
        sslrootcert: Optional[str] = None,
    ):

        self._username: str = username
        self._password: str = password
        self._dbname: str = dbname
        self._host: str = host
        self._port: int = port

        if sslmode is None and sslrootcert:
            sslmode = "verify-ca"
        self._sslmode: Optional[str] = sslmode
        self._sslrootcert: Optional[str] = sslrootcert

        self._pool: Optional[Pool] = None

    def get_id(self) -> str:

        return f"postgres::{self._host}:{self._port}/{self._dbname}"

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

    async def connect(self) -> Connection:

        if self._pool is not None:
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
                sslmode=self._sslmode,
                sslrootcert=self._sslrootcert,
            )
        except Exception as e:
            raise UpcheckException(msg="Can't connect to database.", reason=str(e))

        return self._connection

    async def disconnect(self) -> None:

        if self._connection is not None:
            await self._connection.close()

    async def connection(self):

        if self._connection is None:
            await self.connect()
        return self._connection

    async def _insert(self, query: str, args) -> None:

        # cur = await self.cursor()
        connection = await self.connection()
        async with connection.cursor() as cur:
            await cur.execute(query, args)

    async def write(self, *results: CheckMetric) -> None:

        # TODO: could use arrays for more efficient batch inserts, but probably not worth it at this stage
        for result in results:
            query = """
            INSERT INTO check_results (url, regex, start_time, response_time_ms, response_code, regex_match) VALUES(%s, %s, %s, %s, %s, %s)"""
            args = (
                result.url_check.url,
                result.url_check.regex,
                result.check_time,
                result.response_time,
                result.response_code,
                result.regex_matched,
            )

            await self._insert(query, args)


class AivenPostgresTarget(PostgresTarget):
    def __init__(
        self,
        dbname: str,
        password: str,
        email: Optional[str] = None,
        project_name: Optional[str] = None,
        postgres_service_name: Optional[str] = None,
    ):

        # TODO: lazy initialization, on demand
        self._client = UpcheckAivenClient(
            token_or_account_password=password, email=email
        )
        self._postgres_service_details: Mapping[
            str, Any
        ] = self._client.get_postgres_service_details(
            project_name=project_name, service_name=postgres_service_name
        )

        ca_cert = self._postgres_service_details["ca_cert"]
        temp_dir = create_temp_dir_with_text_files({"ca.pem": ca_cert})

        postgres_target_config = {
            "username": self._postgres_service_details["user"],
            "password": self._postgres_service_details["password"],
            "host": self._postgres_service_details["host"],
            "port": self._postgres_service_details["port"],
            "dbname": dbname,
            "sslmode": "verify-ca",
            "sslrootcert": os.path.join(temp_dir, "ca.pem"),
        }

        super().__init__(**postgres_target_config)
