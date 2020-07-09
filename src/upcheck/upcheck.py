# -*- coding: utf-8 -*-
import logging
import os
from typing import Dict, Iterable, Optional

from anyio import create_task_group
from rich.console import Console
from upcheck.exceptions import UpcheckException
from upcheck.models import CheckError, CheckMetric, CheckResult
from upcheck.sources import CheckSource
from upcheck.targets import CheckTarget
from upcheck.utils.callables import wait_for_tasks, wait_for_tasks_or_user_keypress


log = logging.getLogger("upcheck")


class Upcheck(object):
    """The central class of 'upcheck', connects a source to targets and kicks off the metric gathering.

    Args:

        source (CheckSource): the source object that emits 'CheckResult' objects
        targets (Iterable[CheckTarget]): a list of target objects that consume the 'CheckResults'
        console (Optional[Console]): optional rich.console.Console object, for terminal output. A new one will be created if not provided.
    """

    def __init__(
        self,
        source: CheckSource,
        targets: Iterable[CheckTarget],
        console: Optional[Console] = None,
    ):

        self._source: CheckSource = source
        self._targets: Dict[str, CheckTarget] = {}
        for _t in targets:
            if _t in self._targets.keys():
                raise UpcheckException(
                    msg=f"Can't create target with id '{_t.get_id()}'.",
                    reason="Duplicate id.",
                )
            self._targets[_t.get_id()] = _t

        if console is None:
            console = Console()
        self._console = console

    async def connect(self):

        log.debug(f"Trying to connect to source: {self._source.get_id()}")

        await self._source.connect()
        log.debug("Source connected.")

        failed: Dict[CheckTarget, Exception] = {}
        for _target in self._targets.values():
            log.debug(f"Trying to connect to target: {_target.get_id()}...")
            try:
                await _target.connect()
                log.debug("Target connected.")
            except Exception as e:
                failed[_target] = e
        if failed:
            if len(failed) == 1:
                _ft = list(failed.keys())[0]
                _fe = failed[_ft]
                msg = f"Can't connect to target '{_ft.get_id()}'."
                reason = str(_fe)
            else:
                failed_ids = [_ft.get_id() for _ft in failed.keys()]
                msg = f"Can't connect to targets: {', '.join(failed_ids)}"
                _reason = []
                for _ft, _fe in failed.items():
                    _reason.append(f"  [bold]{_ft.get_id()}[/bold]:")
                    _reason.append(f"       {_fe}")
                reason = "\n".join(_reason)
            raise UpcheckException(msg=msg, reason=reason)

    async def disconnect(self):

        log.debug(f"Disconnecting source {self._source.get_id()}...")
        await self._source.disconnect()
        log.debug("Source disconnected.")

        for _target in self._targets.values():

            try:
                log.debug(f"Disconnecting target {_target.get_id()}...")
                await _target.disconnect()
                log.debug("Target disconnected.")
            except Exception as e:
                log.warning(f"Failed to disconnect target '{_target.get_id()}': {e}")

    async def start(self, wait_for_keypress: Optional[bool] = None):

        if wait_for_keypress is None:
            no_wait = os.getenv("UPCHECK_NO_WAIT", "false")
            if no_wait.lower() == "true":
                wait_for_keypress = False
            else:
                wait_for_keypress = True

        log.debug("Starting upcheck pipeline...")

        async def watch():

            async for check_result in self._source.start():
                await self.write_result(check_result)

            return

        if wait_for_keypress:

            await wait_for_tasks_or_user_keypress(
                {"func": watch}, console=self._console
            )

        else:
            await wait_for_tasks({"func": watch})

        log.debug("Stopping upcheck pipeline...")
        rest_results: Optional[Iterable[CheckResult]] = await self._source.stop()

        if rest_results:
            for r in rest_results:
                await self.write_result(r)

        log.debug("upcheck pipeline stopped.")

    async def write_result(self, check_result: CheckResult) -> None:

        if not self._targets:
            return

        if isinstance(check_result, CheckError):
            log.error(f"Check error: {check_result.error()}")
            return

        if not isinstance(check_result, CheckMetric):
            raise Exception(
                f"Invalid type '{type(check_result)}' for check result (should be 'CheckMetric'. This is a bug."
            )

        if len(self._targets) == 1:
            target = list(self._targets.values())[0]
            log.debug(f"Write metric to target: {target.get_id()}")
            try:
                await target.write(check_result)
            except Exception as e:
                log.error(f"Can't write metric to target '{target.get_id()}': {e}")

            return

        async def wrap(_result: CheckMetric, _target: CheckTarget):
            log.debug(f"Write metric to target: {_target.get_id()}")
            try:
                await _target.write(_result)
                log.debug(f"Finished writing to target: {_target.get_id()}")
            except Exception as e:
                log.error(f"Can't write metric to target '{_target.get_id()}': {e}")

        async with create_task_group() as tg:

            for _t in self._targets.values():
                await tg.spawn(wrap, check_result, _t)
