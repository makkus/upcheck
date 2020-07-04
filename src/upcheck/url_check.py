# -*- coding: utf-8 -*-
import collections
import os
import urllib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union
from urllib.parse import ParseResult

import aiohttp
import yaml
from aiohttp import ClientError, ClientResponseError


class CheckResult(object):
    def __init__(self, url_check: "UrlCheck", start_time: datetime, duration_ms: int):

        self._url_check = url_check
        self._start_time = start_time
        self._duration_ms = duration_ms

    @property
    def url_check(self) -> "UrlCheck":
        return self._url_check

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def duration_ms(self) -> int:
        return self._duration_ms

    def __repr__(self):

        return f"({self.__class__.__name__}: url={self.url_check.url} duration={self.duration_ms}"


class CheckMetric(CheckResult):
    """Class to hold metrics for successful checks.
    """

    def __init__(
        self,
        url_check: "UrlCheck",
        response_code: int,
        start_time: datetime,
        duration_ms: int,
        content: Optional[str],
    ):

        self._response_code: int = response_code
        self._content: Optional[str] = content
        super().__init__(
            url_check=url_check, start_time=start_time, duration_ms=duration_ms
        )

    @property
    def response_code(self) -> int:
        return self._response_code

    @property
    def content(self) -> Optional[str]:
        return self._content


class CheckError(CheckResult):
    """Class to hold details for errors in case of unsucessful checks.

    This will not be used for checks that merely respond with an error code, but for checks that fail because of underlying reasons like the network connection of the machine this runs os being down, etc.

    For the purpose of this application, checks that fail in this way will
    be ignored, since the website that is checked is not responsible for the failure.
    """

    def __init__(
        self,
        url_check: "UrlCheck",
        error: ClientError,
        start_time: datetime,
        duration_ms: int,
    ):

        self._error = error

    def error(self) -> ClientError:
        return self._error


class UrlCheck(object):
    """Class to represent a single website check job.

    Args:
        url (str): the url to check
        seconds_between_checks (int): the time between two checks of the same url
        regexes_to_check (str): an optional regex
    """

    def __init__(
        self,
        url: str,
        seconds_between_checks: int = 60,
        regex_to_check: Optional[str] = None,
    ):

        # parse url, raises error if invalid. save so we can potentially later group checks by the netloc attribute
        if not url:
            raise ValueError("Can't create url check, no url provided.")

        self._parsed_url: ParseResult = urllib.parse.urlparse(url)
        if not self._parsed_url.scheme:
            raise ValueError(f"Can't create url check, invalid url (no scheme): {url}")
        if not self._parsed_url.netloc:
            raise ValueError(
                f"Can't create url check, invalid url (no/invalid domain name): {url}"
            )
        self._url: str = url

        self._seconds_between_checks: int = seconds_between_checks
        self._regex: Optional[str] = regex_to_check

    @property
    def url(self) -> str:
        """The url to check."""
        return self._url

    @property
    def seconds_between_checks(self) -> int:
        """The time between checks (in seconds)."""
        return self._seconds_between_checks

    @property
    def regex_to_check(self) -> Optional[str]:
        """An optional regex to check the content of a (successful) check against."""
        return self._regex

    async def perform_check(self) -> CheckResult:
        """Perform one check againts the configured url.

        Returns:
            CheckResult: the result object, populated with the details of the check
        """

        started = datetime.now()
        html: Optional[str] = None
        response_code: Optional[int] = None

        error: Optional[ClientError] = None

        try:
            async with aiohttp.ClientSession() as session:

                async with session.get(self.url) as response:
                    html = await response.text()
                    response_code = response.status

            if response_code is None:
                raise Exception("Internal error, no response code")

        except ClientResponseError as cre:
            response_code = cre.status
        except ClientError as ce:
            error = ce

        finished = datetime.now()
        delta = finished - started
        duration_ms = int(delta.total_seconds() * 1000)

        if error:
            result: CheckResult = CheckError(
                url_check=self, error=error, start_time=started, duration_ms=duration_ms
            )
        else:
            result = CheckMetric(
                url_check=self,
                response_code=response_code,  # type: ignore
                start_time=started,
                duration_ms=duration_ms,
                content=html,
            )

        return result

    def __repr__(self):

        if not self.regex_to_check:
            regex_string = ""
        else:
            regex_string = f"regex={self.regex_to_check}"
        return f"(UrlCheck: url={self.url} recheck={self.seconds_between_checks}{regex_string})"


class UrlChecks(object):
    @classmethod
    def create_checks(
        cls, *url_or_config_file_paths: Union[Path, str, Mapping[str, Any]]
    ) -> "UrlChecks":
        """Create `UrlChecks` object from a list of string items.

        A string item can either be the path to a file containing a (yaml) list (check the `from_file` method for format
        details), or a url for a website to check (in which case the check defaults will be used (60 seconds between
        checks, no regex check).

        Args:
            url_or_config_file_paths: the list of website checks

        Returns:
            UrlChecks: the UrlChecks object populated with all configured UrlCheck child objects
        """

        configs: List[Mapping[str, Any]] = []

        for url_or_config_file_path in url_or_config_file_paths:

            if isinstance(url_or_config_file_path, Path):
                _configs: Iterable[Mapping[str, Any]] = cls.from_file(
                    url_or_config_file_path
                )
            elif isinstance(url_or_config_file_path, str):
                expanded = os.path.realpath(os.path.expanduser(url_or_config_file_path))
                if os.path.isfile(expanded):
                    _configs = cls.from_file(url_or_config_file_path)
                else:
                    _configs = [{"url": url_or_config_file_path}]
            elif isinstance(url_or_config_file_path, collections.abc.Mapping):
                _configs = [url_or_config_file_path]
            else:
                raise Exception(
                    f"Can't create url check, invalid type '{type(url_or_config_file_path)}' for url check item: {url_or_config_file_path}"
                )

            configs.extend(_configs)

        checks: List[UrlCheck] = []
        for config in configs:
            check = UrlCheck(**config)
            checks.append(check)

        return UrlChecks(*checks)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> Iterable[Mapping[str, Any]]:
        """Parse a (yaml) text file and return containing url check config as a list of dicts.

        The file must contain a yaml list where each item is either:
        - a string (which will be interpreted as url to check)
        - a dict with the mandatory 'url' and optional 'seconds_between_checks' and 'regex' keys

        Args:
            path: the path to a url check config file

        Returns:
            Iterable[Mapping]: a list with url check config dicts
        """

        if isinstance(path, str):
            path = Path(os.path.expanduser(path))

        try:

            content_string = path.read_text()
            content = yaml.load(content_string)
        except Exception as e:
            raise Exception(f"Could not read config file '{path}': {e}")

        if isinstance(content, (str, collections.abc.Mapping)) or not isinstance(
            content, collections.abc.Iterable
        ):
            raise Exception(
                f"Invalid config for url check in file '{path}', must be list of strings and/or mappings: {content}"
            )

        configs = []
        for item in content:
            if isinstance(item, str):
                _config: Dict[str, Any] = {"url": item}
            elif isinstance(item, collections.abc.Mapping):
                _config = item  # type: ignore
            else:
                raise Exception(
                    f"Invalid config item in file '{path}' (must be string or Mapping, not '{type(item)}'): {item}"
                )

            configs.append(_config)

        return configs

    def __init__(self, *url_checks: UrlCheck):

        self._url_checks: Iterable[UrlCheck] = url_checks

    @property
    def url_checks(self) -> Iterable[UrlCheck]:
        return self._url_checks

    async def perform_checks(self) -> Iterable[CheckResult]:

        results: List[CheckResult] = []
        for check in self.url_checks:

            print(f"checking: {check.url}")
            result = await check.perform_check()
            results.append(result)

        return results

    def __repr__(self):

        return f"(UrlChecks: {self.url_checks})"
