# -*- coding: utf-8 -*-
import collections
import os
import re
import urllib
from datetime import datetime
from functools import total_ordering
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Union
from urllib.parse import ParseResult

import aiohttp
from aiohttp import ClientError, ClientResponseError
from anyio import create_task_group
from rich import box
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from ruamel.yaml import YAML
from sortedcontainers import SortedList
from tzlocal import get_localzone


yaml = YAML()


class CheckResult(object):
    def __init__(self, url_check: "UrlCheck", start_time: datetime, end_time: datetime):
        """Base class to collect metrics and results for url checks.

        Args:
            url_check (UrlCheck): the check that was performed
            start_time (datetime): the time the check was kicked off
            end_time (datetime): the time the check finished
        """

        self._url_check: UrlCheck = url_check
        self._start_time: datetime = start_time
        self._end_time: datetime = end_time

        self._report_data: Optional[Mapping[str, Any]] = None

    @property
    def url_check(self) -> "UrlCheck":
        return self._url_check

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def response_time(self) -> int:
        delta = self._end_time - self._start_time
        duration_ms = int(delta.total_seconds() * 1000)
        return duration_ms

    def __repr__(self):

        return f"({self.__class__.__name__}: url={self.url_check.url} response_time={self.response_time} ms"


class CheckMetric(CheckResult):
    """Class to hold metrics for successful checks.

    Successful, in this context, means there were no underlying problems
    out of the responding servers control (e.g. network issues on the machine
    that runs the check). So, even a '401'-response code would be considered
    a 'successful' check.
    """

    def __init__(
        self,
        url_check: "UrlCheck",
        start_time: datetime,
        end_time: datetime,
        response_code: int,
        content: Optional[str],
    ):

        self._response_code: int = response_code
        self._content: Optional[str] = content
        super().__init__(url_check=url_check, start_time=start_time, end_time=end_time)

    @property
    def response_code(self) -> int:
        return self._response_code

    @property
    def content(self) -> Optional[str]:
        return self._content

    @property
    def regex_matched(self) -> Optional[bool]:

        if not self.url_check.regex:
            return None

        if not self.content:
            return False

        # UNSURE: maybe only check if response code indicates success?
        result = re.search(self.url_check.regex, self.content)
        return True if result else False

    @property
    def report_data(self) -> Mapping[str, Any]:

        if self._report_data is None:
            self._report_data = {
                "url": self._url_check.url,
                "check_time": self.start_time,
                "response_code": self.response_code,
                "response_time": self.response_time,
                "regex_matched": self.regex_matched,
            }
        return self._report_data

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Attribute")
        table.add_column("Value", style="italic")

        table.add_row("url", self.url_check.url)

        table.add_row("started", str(self.start_time))
        table.add_row("response time", f"{self.response_time} ms")
        table.add_row("response code", str(self.response_code))
        if self.regex_matched is None:
            table.add_row("regex matched", "n/a")
        else:
            table.add_row("regex matched", "true" if self.regex_matched else "false")

        yield table


class CheckError(CheckResult):
    """Class to hold details for errors in case of unsucessful checks.

    This will not be used for checks that merely respond with an error code, but for checks that fail because of underlying reasons like the network connection of the machine this runs os being down, etc.

    For the purpose of this application, checks that fail in this way will
    be ignored, since the website that is checked is not responsible for the failure.
    """

    def __init__(
        self,
        url_check: "UrlCheck",
        start_time: datetime,
        end_time: datetime,
        error: ClientError,
    ):

        self._error = error
        super().__init__(url_check=url_check, start_time=start_time, end_time=end_time)

    def error(self) -> ClientError:
        return self._error

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Attribute")
        table.add_column("Value", style="italic")

        table.add_row("url", self.url_check.url)

        table.add_row("started", str(self.start_time))
        table.add_row("response time", f"{self.response_time} ms")
        table.add_row("error", str(self.error()))

        yield table


@total_ordering
class UrlCheck(object):
    """Class to represent a single website check job.

    Args:
        url (str): the url to check
        regex (str): an optional regex
    """

    def __init__(self, url: str, regex: Optional[str] = None):

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
        self._regex: Optional[str] = regex

    @property
    def url(self) -> str:
        """The url to check."""
        return self._url

    @property
    def regex(self) -> Optional[str]:
        """An optional regex to check the content of a (successful) check against."""
        return self._regex

    async def perform_check(self) -> CheckResult:
        """Perform one check againts the configured url.

        Returns:
            CheckResult: the result object, populated with the details of the check
        """

        html: Optional[str] = None
        response_code: Optional[int] = None

        error: Optional[ClientError] = None

        # using advice from: https://stackoverflow.com/questions/2720319/python-figure-out-local-timezone/17363006#17363006
        tz = get_localzone()
        started = tz.localize(datetime.now(), is_dst=None)

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

        finished = tz.localize(datetime.now(), is_dst=None)

        if error:
            result: CheckResult = CheckError(
                url_check=self, start_time=started, end_time=finished, error=error
            )
        else:
            result = CheckMetric(
                url_check=self,
                start_time=started,
                end_time=finished,
                response_code=response_code,  # type: ignore
                content=html,
            )

        return result

    def __eq__(self, other):

        if not isinstance(other, self.__class__):
            return False

        return (self.url, self.regex) == (other.url, other.regex)

    def __hash__(self):

        return hash((self.url, self.regex))

    def __lt__(self, other):

        if not isinstance(other, self.__class__):
            return NotImplemented

        return (self.url, self.regex) < (other.url, other.regex)

    def __repr__(self):

        if not self.regex:
            regex_string = ""
        else:
            regex_string = f"regex={self.regex}"
        return f"(UrlCheck: url={self.url}{regex_string})"


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

        result = UrlChecks(*checks)
        return result

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
            content = yaml.load(path)
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

    def __init__(self, *url_checks: UrlCheck, seconds_between_checks: int = 60):

        self._url_checks: Set[UrlCheck] = set(url_checks)
        self._seconds_between_checks: int = seconds_between_checks

    @property
    def seconds_between_checks(self) -> int:
        """The time between checks (in seconds)."""
        return self._seconds_between_checks

    @property
    def url_checks(self) -> Iterable[UrlCheck]:
        return self._url_checks

    async def perform_checks(self) -> List[CheckResult]:

        results: SortedList[CheckResult] = SortedList(
            key=lambda x: (x.start_time, x.url_check)
        )

        async def run_check(_check: UrlCheck):
            result = await _check.perform_check()
            results.add(result)

        async with create_task_group() as tg:
            for check in self.url_checks:
                await tg.spawn(run_check, check)

        return results

    def __repr__(self):

        return f"(UrlChecks: {self.url_checks})"
