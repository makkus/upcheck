# -*- coding: utf-8 -*-
from upcheck.interfaces.cli.main import console
from upcheck.models import CheckMetric
from upcheck.targets import CheckTarget


class TerminalTarget(CheckTarget):
    """Simple target to print check results to the terminal."""

    def __init__(self, **config):

        self._config = config  # ignored for now

    def get_id(self) -> str:
        return "terminal"

    async def write(self, *results: CheckMetric) -> None:

        for result in results:
            console.print(result)
