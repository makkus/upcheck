# -*- coding: utf-8 -*-
from upcheck.interfaces.cli.main import console
from upcheck.targets import CheckTarget
from upcheck.url_check import CheckMetric


class TerminalTarget(CheckTarget):
    """Simple target to print"""

    def __init__(self, **config):

        self._config = config

    def get_id(self) -> str:
        return "terminal"

    async def write(self, *results: CheckMetric) -> None:

        for result in results:
            console.print(result)
